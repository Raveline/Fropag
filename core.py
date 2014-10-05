# -*- coding: utf-8 -*-

import multiprocessing
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from publication import Publication, Base, path_to_corpus, Word, FrontPage, WordCount

from reader import read_front_page
from analyze import get_stats

engine = create_engine("sqlite:///example.db")
Base.metadata.bind = engine

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
        
        # Get id for words - this is going to be slow - particularly for new words
        # but session cache-like abilities could help us
        proper_nouns = [(get_word_id(session, w[0], True), w[1]) for w in stats[0].items()]
        common_nouns = [(get_word_id(session, w[0], False), w[1]) for w in stats[1].items()]

        # This being bulk inserts, we're going to use SqlAlchemy Core
        engine.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : new_front_page.id
            ,'word_id' : w[0]} for w in common_nouns])
        engine.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : new_front_page.id
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
    engine = create_engine("sqlite:///example.db")
    Base.metadata.create_all(engine)
    return "Created database."

def get_session():
    DBSession = sessionmaker(bind=engine)
    return DBSession()
