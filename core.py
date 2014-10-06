# -*- coding: utf-8 -*-
import multiprocessing
import time
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
from publication import Publication, Base, path_to_corpus, Word, FrontPage, WordCount

from reader import read_front_page
from analyze import get_stats
import config

engine = None

class ConfigException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def see_words_for(publication_name, proper, limit = 10):
    s = get_session()
    q = s.query(Word.word, func.sum(WordCount.count).label('sumcount')).\
            join(WordCount, Word.id == WordCount.word_id).\
            join(FrontPage, WordCount.frontpage_id == FrontPage.id).\
            join(Publication, Publication.id == FrontPage.publication_id).\
            filter(Publication.name == publication_name).\
            filter(Word.proper == proper).\
            group_by(Word.word).\
            order_by(desc('sumcount')).all()[:limit]
    return q

def check_config():
    config_values = [config.DB_USER, config.DB_PASSWORD, config.DB_HOST
                    ,config.DB_PORT, config.DB_NAME]
    is_there_none = any([v is None for v in config_values])
    if is_there_none:
        none_value = ""
        if config.DB_USER is None:
            none_value = "DB_USER"
        if config.DB_PASSWORD is None:
            none_value = "DB_PASSWORD"
        if config.DB_HOST is None:
            none_value = "DB_HOST"
        if config.DB_PORT is None:
            none_value = "DB_PORT"
        if config.DB_NAME is None:
            none_value = "DB_NAME"
        raise ConfigException(none_value + " in config.py is None. Fill it before using Fropag.")

def get_engine():
    global engine
    if engine is None:
        check_config()
        connection_string = ''.join(["postgresql+psycopg2://"
                                    ,config.DB_USER
                                    ,':'
                                    ,config.DB_PASSWORD
                                    ,'@'
                                    ,config.DB_HOST
                                    ,':'
                                    ,config.DB_PORT
                                    ,'/'
                                    ,config.DB_NAME])
        engine = create_engine(connection_string, isolation_level="AUTOCOMMIT")
        Base.metadata.bind = engine
    else:
        return engine

def follow_publication(name, url, start, end):
    session = get_session()
    new_publication = Publication(name=name, url=url
                        , start=start, end=end)
    session.add(new_publication)
    session.commit()
    return "Following publication {} at {} ".format(name, url)

def save_all(session, q):
    while not q.empty():
        pair = q.get()
        # This will get us a pair (Publication, (Stats))
        publication = pair[0]
        stats = pair[1]
        new_front_page = FrontPage(publication_id = publication.id
                              ,lexical_richness = stats[2])
        session.add(new_front_page)
        session.commit()
        save_words(session, new_front_page.id, stats[0], stats[1])

def save_words(session, publication_id, propers, commons):
        # Get id for words - this is going to be slow - particularly for new words
        # but session cache-like abilities could help us
        proper_nouns = [(get_word_id(session, w[0], True), w[1]) for w in propers.items()]
        common_nouns = [(get_word_id(session, w[0], False), w[1]) for w in commons.items()]

        # This being bulk inserts, we're going to use SqlAlchemy Core
        eng = get_engine()
        eng.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : publication_id
            ,'word_id' : w[0]} for w in common_nouns])
        eng.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : publication_id
            ,'word_id' : w[0]} for w in proper_nouns])

def analyze_process():
    """Read every frontpages followed.
    Get the followed publications from the database,
    then read them. This being a lengthy process, we'll
    try and multiprocess it to see if it helps."""
    t0 = time.time()
    session = get_session()
    publications = session.query(Publication).all()
    processes = []
    results = multiprocessing.Queue()
    for pub in publications:
        processes.append(multiprocessing.Process(target=read_and_analyze, args=(pub, results,)))
    [p.start() for p in processes]
    [p.join() for p in processes]
    save_all(session, results)
    return "Read and analyzed {} front pages in {} secs.".format(len(publications), str(time.time() - t0))

def read_and_analyze(publication, q):
    page = read_front_page(publication.url, publication.start, publication.end)
    stats = get_stats(page)
    q.put((publication, stats))

def delete_front_page(fp_id):
    """Delete ONE front page from the database.
    Must delete the dependent wordcounts."""
    session = get_session()
    found = session.query(FrontPage).filter_by(id=fp_id).one()
    if found:
        session.delete(found)
        session.commit()
        return "Deleted."
    else:
        "No such frontpage."

### DB utilites
# Should most likely have their own module
def get_word_id(session, w, p):
    """Get the id of w in the database.
    If w doesn't exist, insert it and give return its id."""
    found = session.query(Word).filter_by(word = w, proper = p).first()
    if found:
        return found.id
    else:
        new_word = Word(word = w, proper = p)
        session.add(new_word)
        session.commit()
        return new_word.id

def init_db():
    eng = get_engine()
    Base.metadata.create_all(eng)
    return "Created database."

def get_session():
    eng = get_engine()
    DBSession = sessionmaker(bind=eng)
    return DBSession()
