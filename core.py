# -*- coding: utf-8 -*-
import multiprocessing
import time
import itertools
from sqlalchemy import func, desc, distinct
from sqlalchemy import text
from sqlalchemy.sql.expression import literal, or_, and_
from sqlalchemy.orm.exc import NoResultFound
from database import Base, engine, get_engine, db_session
from publication import Publication, Word, FrontPage, WordCount, Forbidden
import config

from reader import read_front_page
from analyze import get_stats

# EXCEPTIONS
#------------------------------
class NonExistingDataException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# READ - DB AGGREGATION
#------------------------------

def get_word_data(word):
    """For a given word (expressed as a string) return various information
    about it : its name, the publication who should ignore it, and if
    it is to be ignored by all publications."""
    # Note : There should always be ONE word as a result.
    # Sure, a word can be proper and common at the same time,
    # e.g., mobile (the adjective) and Mobile (the town).
    # However, proper nouns are to be recorded with a capital
    # first letter, whereas common nouns are lowered before
    # being inserted. (See the get_stats function of the analyze module).
    res = db_session.query(Word, Forbidden.word_id, Forbidden.publication_id,
            Publication.id, Publication.name, 
            Forbidden.publication_id == Publication.id).\
            join(Publication, literal(1) == 1).outerjoin(Forbidden,
            Forbidden.word_id == Word.id).\
            filter(Word.word == word).all()
    if not res:
        raise NonExistingDataException("Word " + word + " does not exist.")
    else:
        result = {}
        result['forbidden_all'] = res[0][1] is not None and res[0][2] is None
        result['word'] = res[0][0]
        result['publications'] = [{'id' : r[3], 'forbidden' : r[5],'name' : r[4]} for r in res] 
        return result

def get_publication_tops(names):
    # This is rather ugly. But getting limited result for grouped queries
    # is rather impracticable. Best solution will be to cache this result.
    results = {}
    for (p_id, p_name) in db_session.query(Publication.id, Publication.name).\
                        filter(Publication.name.in_(names)):
        results[p_name] = count_words_for(p_id, p_name)
    return results

def count_words_for(pub_id):
    q = word_counting_query().filter(Publication.id == p_id)
    return separate_propers_and_commons(q)

def get_publication_frequency(names):
    results = {}
    pubs_and_fp_number = db_session.query(Publication.id, Publication.name)
    for (p_id, p_name) in pubs_and_fp_number:
        results[p_name] = count_frequency_for(p_id)
    return results

def count_frequency_for(p_id):
    def to_frequency(occurences, measurements):
        return round((occurences / measurements), 2)

    q = word_counting_query().filter(Publication.id == p_id)
    res = separate_propers_and_commons(q)
    n_frontpages = db_session.query(func.count(FrontPage.id)).\
            filter(FrontPage.publication_id == p_id).one()[0]
    res['propers'] = [(p[0], to_frequency(p[1], n_frontpages)) for p in res['propers']]
    res['commons'] = [(c[0], to_frequency(c[1], n_frontpages)) for c in res['commons']]
    return res

def get_history_for(word):
    # This is way to tiresome to do with ORM.
    # So... let's do it the old way !
    query = """select pubs.pubdate,
                      p.name,
                      coalesce(cnt.count, 0)
               from 
                    (select c.count, 
                            to_char(f.time_of_publication, 'YYYY/MM/DD') 
                            as pdate,
                            p.id from wordcount c 
                            left join frontpage f 
                                on f.id = c.frontpage_id 
                            left join publication p 
                                on f.publication_id = p.id 
                            left join word w 
                                on c.word_id = w.id 
                     where word = :x) cnt 
                full outer join 
                    (select 
                        distinct to_char(f.time_of_publication, 'YYYY/MM/DD')
                            as pubdate, 
                        p.id from frontpage f 
                        cross join publication p) pubs 
                on cnt.id = pubs.id 
                and cnt.pdate = pubs.pubdate
                left outer join publication p on p.id = pubs.id;"""
    return to_stats(engine.execute(text(query), x=word).fetchall(), "date")

def to_stats(elems, first_column_name):
    """Given a list of tuples, typically a SQL query result,
    put the 2nd colum in top.
    >>> a = [('date1', 'newspaper1', 2),
    ... ('date1', 'newspaper2', 3),
    ... ('date1', 'newspaper3', 4),
    ... ('date2', 'newspaper1', 5),
    ... ('date2', 'newspaper2', 6),
    ... ('date2', 'newspaper3', 7)]
    >>> to_stats(a, 'date')
    [['date', 'newspaper1', 'newspaper2', 'newspaper3'], ['date1', 2, 3, 4], ['date2', 5, 6, 7]]
    """
    # Sort
    by1 = sorted(elems, key=lambda k : k[1])
    by0 = sorted(elems, key=lambda k : k[0])
    # Extract the 2nd column
    column2 = itertools.groupby(by1, lambda x: x[1])
    column2 = [k for k, v in column2]
    column2.insert(0, first_column_name)
    # Extract data without the 2nd column
    grouped = itertools.groupby(by0, lambda y: y[0])
    res = []
    for k, v in grouped:
        list_value = list(v)
        pertinent = [list(v)[2:] for v in list_value]
        pertinent = list(itertools.chain(*pertinent))
        pertinent.insert(0, k)
        res.append(pertinent)
    # Concatenate both
    return [column2] + res

def get_all_tops():
    return separate_propers_and_commons(word_counting_query())

def get_publications():
    return db_session.query(Publication).all()

def word_counting_query():
    q = db_session.query(Word.word, func.sum(WordCount.count).label('sumcount')
                        ,func.min(FrontPage.time_of_publication)
                        ,func.max(FrontPage.time_of_publication))
    q = join_from_words_to_publication(q)
    return q.group_by(Word.word).order_by(desc('sumcount'))

def separate_propers_and_commons(query):
    results = {}
    propers = query.filter(Word.proper == True).all()[:10]
    results['propers'] = [(r[0], r[1]) for r in propers]
    results['commons'] = [(r[0], r[1]) for r
                         in query.filter(Word.proper == False).all()[:10]]
    # For new publications
    if len(propers) > 0 and propers[0] > 4:
        results['mindate'] = propers[0][2].strftime('%d/%m/%Y')
        results['maxdate'] = propers[0][3].strftime('%d/%m/%Y')
    return results

def see_words_for(publication_name, proper, limit = 10):
    q = word_counting_query().filter(Publication.name == publication_name).\
            filter(Word.proper == proper).\
            all()[:limit]
    return q

def join_from_words_to_publication(q):
    return q.join(WordCount, Word.id == WordCount.word_id).\
      join(FrontPage, WordCount.frontpage_id == FrontPage.id).\
      join(Publication, Publication.id == FrontPage.publication_id).\
      outerjoin(Forbidden, Forbidden.word_id == Word.id).\
      filter(or_(and_(Forbidden.word_id == None, Forbidden.publication_id == None),
                (and_(Forbidden.word_id != None,Forbidden.publication_id != Publication.id))))

# Update functions
#------------------------------
def modify_word(id_w, proper, forbid_all, forbidden):
    # First, let's udpate the word table
    db_session.query(Word).filter(Word.id == id_w).update({"proper": proper})
    # Then, remove every forbidden properties for this word
    for forb in db_session.query(Forbidden).filter(Forbidden.word_id == id_w):
        db_session.delete(forbidden_all)
    # Then if forbid_all : insert only word_id
    db_session.begin()
    if forbid_all:
        newForbidden = Forbidden(word_id = id_w)
        db_session.add(newForbidden)
    else:
        for fpub in forbidden:
            newForbidden = Forbidden(word_id = id_w, publication_id = fpub)
            db_session.add(newForbidden)
    db_session.commit()
    return "Updated."

def modify_publication(id_p, name, url, start, end):
    db_session.query(Publication).filter(Publication.id == id_p).\
            update({"name":name, "url":url, "start":start, "end":end })

# Create functions
#------------------------------

def follow_publication(name, url):
    db_session.begin()
    new_publication = Publication(name=name, url=url)
    db_session.add(new_publication)
    db_session.commit()
    return "Following publication {} at {} ".format(name, url)

def save_all(q):
    while not q.empty():
        pair = q.get()
        # This will get us a pair (Publication, (Stats))
        publication = pair[0]
        stats = pair[1]
        new_front_page = FrontPage(publication_id = publication.id
                              ,lexical_richness = stats[2])
        db_session.begin()
        db_session.add(new_front_page)
        db_session.commit()
        save_words(new_front_page.id, stats[0], stats[1])

def save_words(publication_id, propers, commons):
        # Get id for words - this is going to be slow - particularly for new words
        # but session cache-like abilities could help us
        proper_nouns = [(get_word_id_or_add_it(w[0], True), w[1]) 
                        for w in propers.items()]
        common_nouns = [(get_word_id_or_add_it(w[0], False), w[1]) 
                        for w in commons.items()]

        # This being bulk inserts, we're going to use SqlAlchemy Core
        if common_nouns:
            engine.execute(
                WordCount.__table__.insert(),
                [{'count' : w[1], 'frontpage_id' : publication_id
                ,'word_id' : w[0]} for w in common_nouns])
        if proper_nouns:
            engine.execute(
                WordCount.__table__.insert(),
                [{'count' : w[1], 'frontpage_id' : publication_id
                ,'word_id' : w[0]} for w in proper_nouns])

def analyze_process():
    """Read every frontpages followed.
    Get the followed publications from the database,
    then read them. This being a lengthy process, we'll
    try and multiprocess it to see if it helps."""
    t0 = time.time()
    publications = db_session.query(Publication).all()
    processes = []
    results = multiprocessing.Queue()
    for pub in publications:
        processes.append(multiprocessing.Process(target=read_and_analyze, args=(pub, results,)))
    [p.start() for p in processes]
    [p.join() for p in processes]
    save_all(results)
    return "Read and analyzed {} front pages in {} secs.".format(len(publications), str(time.time() - t0))

def read_and_analyze(publication, queue):
    """Read a frontpage using the reader module.
    Put the result in a queue."""
    page = read_front_page(publication.url)
    stats = get_stats(page)
    queue.put((publication, stats))

def get_word_id_or_add_it(w, p):
    """Get the id of w in the database.
    If w doesn't exist, insert it and give return its id."""
    found = db_session.query(Word).filter_by(word = w, proper = p).first()
    if found:
        return found.id
    else:
        new_word = Word(word = w, proper = p)
        db_session.begin()
        db_session.add(new_word)
        db_session.commit()
        return new_word.id

# Delete
#------------------------------
def delete_stuff(q):
    try:
        db_session.begin()
        db_session.delete(q.one())
        db_session.commit()
        return "Deleted."
    except NoResultFound:
        return "No such publication."

def delete_publication(p_id):
    """Delete ONE publication from the database.
    Must delete teh dependents frontpage & wordcounts."""
    return delete_stuff(db_session.query(Publication).filter(Publication.id==p_id))

def delete_front_page(fp_id):
    """Delete ONE front page from the database.
    Must delete the dependent wordcounts."""
    return delete_stuff(db_session.query(FrontPage).filter(FrontPage.id==fp_id))


# Utilities (should move soon)
#------------------------------
def boot_sql_alchemy():
    global engine
    engine = get_engine(config.DB_URI
                    ,config.DB_USER
                    ,config.DB_PASSWORD
                    ,config.DB_HOST
                    ,config.DB_PORT
                    ,config.DB_NAME)
    
def init_db():
    Base.metadata.create_all(engine)
    return "Created database."
