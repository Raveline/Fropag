import argparse
import time
import multiprocessing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from publication import Publication, Base, path_to_corpus, Word, FrontPage, WordCount
from os import mkdir

from reader import read_front_page
from analyze import get_stats

engine = create_engine("sqlite:///example.db")
Base.metadata.bind = engine

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

def init_db(args):
    engine = create_engine("sqlite:///example.db")
    Base.metadata.create_all(engine)
    return "Created database."

def get_session():
    DBSession = sessionmaker(bind=engine)
    return DBSession()

def read_all(args):
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
        print("Preparing to read words...")
        proper_nouns = [(get_word_id(session, w[0], True), w[1]) for w in stats[0].items()]
        print("Read proper, now doing commons...")
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

def add_publication(args):
    name = args.name
    url = args.url
    session = get_session()
    new_publication = Publication(name=name, url=url
                        , start=args.start, end=args.end)
    session.add(new_publication)
    session.commit()
    return "Following publication {} at {} ".format(name, url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    follow = subparsers.add_parser("follow", help="follow help")
    follow.add_argument("name", help="Name of the publication to follow.")
    follow.add_argument("url", help="URL of the front page for this publication.")
    follow.add_argument("start", help="Expression identifying the beginning of the front page.")
    follow.add_argument("end", help="Expression identifying the ending of the front page.")
    init = subparsers.add_parser("init", help="Setup database.")
    read = subparsers.add_parser("read", help="Read followed front pages and analyze them.")
    follow.set_defaults(func=add_publication)
    init.set_defaults(func=init_db)
    read.set_defaults(func=read_all)
    
    args = parser.parse_args()
    res = args.func(args)
    print(res)
