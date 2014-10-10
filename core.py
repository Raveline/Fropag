# -*- coding: utf-8 -*-
import multiprocessing
import time
from sqlalchemy import func, desc
from sqlalchemy.sql.expression import literal
from sqlalchemy.orm.exc import NoResultFound
from database import Base, engine, get_engine, db_session
from publication import Publication, Word, FrontPage, WordCount, Forbidden
import config

from reader import read_front_page
from analyze import get_stats

# CONSTANTS
#------------------------------
propers_prelude = [("Noms propres", "Décompte")]
commons_prelude = [("Noms communs", "Décompte")]

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
        q = word_counting_query().filter(Publication.id == p_id)
        results[p_name] = separate_propers_and_commons(q)
    return results

def get_all_tops():
    return separate_propers_and_commons(word_counting_query())

def get_publications():
    return db_session.query(Publication).all()

def word_counting_query():
    q = db_session.query(Word.word, func.sum(WordCount.count).label('sumcount'))
    q = join_from_words_to_publication(q)
    return q.group_by(Word.word).order_by(desc('sumcount'))

def separate_propers_and_commons(query):
    results = {}
    propers = query.filter(Word.proper == True).all()[:10]
    commons = query.filter(Word.proper == False).all()[:10]
    results['propers'] = propers_prelude + propers;
    results['commons'] = commons_prelude + commons;
    return results

def see_words_for(publication_name, proper, limit = 10):
    q = word_counting_query().filter(Publication.name == publication_name).\
            filter(Word.proper == proper).\
            all()[:limit]
    return q

def join_from_words_to_publication(q):
    return q.join(WordCount, Word.id == WordCount.word_id).\
      join(FrontPage, WordCount.frontpage_id == FrontPage.id).\
      join(Publication, Publication.id == FrontPage.publication_id)

# Update functions
#------------------------------
def modify_word(id_w, proper, forbid_all, forbidden):
    # First, let's udpate the word table
    found = db_session.query(Word).filter(Word.id == id_w).\
            update({"proper": proper})
    # Then, remove every forbidden properties for this word
    for forb in db_session.query(Forbidden).filter(Forbidden.word_id == id_w):
        db_session.delete(forbidden_all)
    # Then if forbid_all : insert only word_id
    if forbid_all:
        newForbidden = Forbidden(word_id = id_w)
        db_session.add(newForbidden)
    else:
        for fpub in forbidden:
            newForbidden = Forbidden(word_id = id_w, publication_id = fpub)
            db_session.add(newForbidden)
    return "Updated."

def modify_publication(id_p, name, url, start, end):
    db_session.query(Publication).filter(Publication.id == id_p).\
            update({"name":name, "url":url, "start":start, "end":end })

# Create functions
#------------------------------

def follow_publication(name, url, start, end):
    db_session.begin()
    new_publication = Publication(name=name, url=url
                        , start=start, end=end)
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
        engine.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : publication_id
            ,'word_id' : w[0]} for w in common_nouns])
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

def read_and_analyze(publication, q):
    page = read_front_page(publication.url, publication.start, publication.end)
    stats = get_stats(page)
    q.put((publication, stats))

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
