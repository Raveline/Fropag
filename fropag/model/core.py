'''Provide various utilities to extract information
from the database.'''
# -*- coding: utf-8 -*-
import itertools
from sqlalchemy import func, desc
from sqlalchemy import text
from sqlalchemy.sql.expression import literal, or_, and_
from sqlalchemy.orm.exc import NoResultFound
from database import Base, get_engine, set_engine, db_session
from model.publication import Publication, Word, FrontPage, WordCount, Forbidden
import config

# EXCEPTIONS
#------------------------------
class NonExistingDataException(Exception):
    '''This exception should be raised when user requested
    access to information on something that does not exist
    in the DB.'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# READ - DB AGGREGATION
#------------------------------

def get_publication(name):
    '''Given the name of a publication, return, if it exists,
    the Publication object.'''
    try:
        return db_session.query(Publication).\
                          filter(Publication.name == name).one()
    except:
        raise NonExistingDataException('No such publication')

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
    res = db_session.query(Word,
                           Forbidden.word_id,
                           Forbidden.publication_id,
                           Publication.id,
                           Publication.name,
                           Forbidden.publication_id == Publication.id).\
            join(Publication, literal(1) == 1).\
            outerjoin(Forbidden, Forbidden.word_id == Word.id).\
            filter(Word.word == word).all()
    if not res:
        raise NonExistingDataException("Word " + word + " does not exist.")
    else:
        result = {}
        result['forbidden_all'] = res[0][1] is not None and res[0][2] is None
        result['word'] = res[0][0]
        result['publications'] = [{'id' : r[3],
                                   'forbidden' : r[5],
                                   'name' : r[4]} for r in res]
        return result

def get_publication_tops(names):
    '''For every publication with the given names,
    get the top 10 most used common words and the
    top 10 most used proper words.'''
    # This is rather ugly. But getting limited result for grouped queries
    # is rather impracticable. Best solution will be to cache this result.
    results = {}
    for (p_id, p_name) in db_session.query(Publication.id, Publication.name).\
                        filter(Publication.name.in_(names)):
        results[p_name] = count_words_for(p_id)
    return results

def get_publication_most_used(name):
    '''For the publication with the given name,
    find the 100 most used common words
    and the 100 most used proper words.'''
    results = {}
    q = word_counting_query().filter(Publication.name == name)
    return separate_propers_and_commons(q, 100)

def count_words_for(p_id):
    '''Count the words for one publication identified
    through its primary key. Will get the 10th most common
    and proper words.'''
    q = word_counting_query().filter(Publication.id == p_id)
    return separate_propers_and_commons(q)

def get_publication_frequency(names):
    '''Count the 10 most frequent words for 
    the given publications, identified by their names.'''
    results = {}
    pubs_and_fp_number = db_session.query(Publication.id, Publication.name)
    for (p_id, p_name) in pubs_and_fp_number:
        results[p_name] = count_frequency_for(p_id)
    return results

def get_number_of_frontpages_for(pub_id):
    '''Return the number of frontpages registered
    for one publication, identified by its primary key.'''
    return db_session.query(func.count(FrontPage.id)).\
            filter(FrontPage.publication_id == pub_id).one()[0]

def count_frequency_for(p_id):
    '''Count the frequency of words for a publication
    identified by its primary key.'''
    def to_frequency(occurences, measurements):
        '''Simple frequency computation with 2 digits precision.'''
        return round((occurences / measurements), 2)
    n_frontpages = get_number_of_frontpages_for(p_id)
    q = word_counting_query().filter(Publication.id == p_id)
    res = separate_propers_and_commons(q)
    res['propers'] = [(p[0],
                      to_frequency(p[1], n_frontpages))
                      for p in res['propers']]
    res['commons'] = [(c[0],
                      to_frequency(c[1], n_frontpages))
                      for c in res['commons']]
    return res

def get_history_for(word):
    '''Given a word, get how many times it appeared
    for each frontpage of each publications followed.'''
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
    return to_stats(get_engine().execute(text(query),
                                         x=word).\
                                 fetchall(), "date")

def to_stats(elems, first_column_name):
    '''Given a list of tuples, typically a SQL query result,
    put the 2nd colum in top.
    >>> a = [('date1', 'newspaper1', 2),
    ... ('date1', 'newspaper2', 3),
    ... ('date1', 'newspaper3', 4),
    ... ('date2', 'newspaper1', 5),
    ... ('date2', 'newspaper2', 6),
    ... ('date2', 'newspaper3', 7)]
    >>> to_stats(a, 'date')
    [['date', 'newspaper1', 'newspaper2', 'newspaper3'], ['date1', 2, 3, 4], ['date2', 5, 6, 7]]
    '''
    # Sort
    by1 = sorted(elems, key=lambda k: k[1])
    by0 = sorted(elems, key=lambda k: k[0])
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
    '''Get 10 most common and 10 most proper words
    used in ALL publications.'''
    return separate_propers_and_commons(word_counting_query())

def get_publications():
    '''Return all tracked publication.'''
    return db_session.query(Publication).all()

def get_real_min_and_max(q):
    '''From the word_counting_query or a similar one where
    min and max of dates won't be absolute, due to the grouping,
    subquery this query in order to get the real absolutes min
    and max.'''
    subq = q.subquery()
    newq = db_session.query(func.min(subq.c.mindate),
                            func.max(subq.c.maxdate))
    return newq.first()

def word_counting_query():
    '''Our main query for counting words and getting
    the minimum and maximum date where they appeared.'''
    q = db_session.query(Word.word.label('word'),
                         func.sum(WordCount.count).label('sumcount'),
                         func.min(FrontPage.time_of_publication).\
                         label('mindate'),
                         func.max(FrontPage.time_of_publication).\
                         label('maxdate'))
    q = join_from_words_to_publication(q)
    return q.group_by(Word.word).order_by(desc('sumcount'))

def separate_propers_and_commons(query, nmb_return=10):
    '''Given a query, separate the proper and common words.
    Execute the query for both and return nmb_return rows.
    If the results exist, also get the datespan of our data.'''
    results = {}
    propers = query.filter(Word.proper == True).all()[:nmb_return]
    commons = query.filter(Word.proper == False).all()[:nmb_return]
    results['propers'] = [(r[0], r[1]) for r in propers]
    results['commons'] = [(r[0], r[1]) for r in commons]
    # For new publications
    if len(commons) > 0:
        minmax = get_real_min_and_max(query)
        results['mindate'] = minmax[0].strftime('%d/%m/%Y')
        results['maxdate'] = minmax[1].strftime('%d/%m/%Y')
    return results

def see_words_for(publication_name, proper, limit = 10):
    '''Get x most used words for the publication identified
    by its name. Words can be proper or not, according to
    the boolean second parameter.
    N.B. : mostly used for debug, this should disappear.'''
    q = word_counting_query().filter(Publication.name == publication_name).\
            filter(Word.proper == proper).\
            all()[:limit]
    return q

def join_from_words_to_publication(q):
    '''Join for word counting queries. This join mostly
    make sure forbidden words, words that we don't want to
    follow, are not going to be counted.'''
    return q.join(WordCount, Word.id == WordCount.word_id).\
      join(FrontPage, WordCount.frontpage_id == FrontPage.id).\
      join(Publication, Publication.id == FrontPage.publication_id).\
      outerjoin(Forbidden, Forbidden.word_id == Word.id).\
      filter(or_(and_(Forbidden.word_id == None, Forbidden.publication_id == None),
                (and_(Forbidden.word_id != None,Forbidden.publication_id != Publication.id))))

# Update functions
#------------------------------
def modify_word(id_w, proper, forbid_all, forbidden):
    '''Modify a word in the database. Change its proper
    status, the fact that its forbidden for all or some
    publications.'''
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

def modify_publication(id_p, name, url):
    '''Change the information of a publication.'''
    db_session.query(Publication).filter(Publication.id == id_p).\
            update({"name":name, "url":url})

# Create functions
#------------------------------

def follow_publication(name, url):
    '''Track a new publication by adding it to the database.'''
    db_session.begin()
    new_publication = Publication(name=name, url=url)
    db_session.add(new_publication)
    db_session.commit()
    return "Following publication {} at {} ".format(name, url)

# Delete
#------------------------------
def delete_stuff(q):
    '''Generic removal function. Receives a  query,
    and return an error or success message according
    to how the query went.'''
    try:
        db_session.begin()
        db_session.delete(q.one())
        db_session.commit()
        return "Deleted."
    except NoResultFound:
        return "No such publication."

def delete_publication(p_id):
    '''Delete ONE publication from the database
    Must delete teh dependents frontpage & wordcounts.'''
    return delete_stuff(db_session.query(Publication).\
                        filter(Publication.id == p_id))

def delete_front_page(fp_id):
    '''Delete ONE front page from the database.
    Must delete the dependent wordcounts.'''
    return delete_stuff(db_session.query(FrontPage).\
                        filter(FrontPage.id == fp_id))

# Utilities (should move soon)
#------------------------------
def boot_sql_alchemy():
    '''Prepare SQLAlchemy engine using the information
    in config.py.'''
    set_engine(config.DB_URI,
               config.DB_USER,
               config.DB_PASSWORD,
               config.DB_HOST,
               config.DB_PORT,
               config.DB_NAME)
    
def init_db():
    '''Create the database.'''
    Base.metadata.create_all(get_engine())
    return "Created database."
