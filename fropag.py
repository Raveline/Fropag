import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from publication import Publication, Base, path_to_corpus
from os import mkdir

engine = create_engine("sqlite:///example.db")
Base.metadata.bind = engine

def init_db(args):
    engine = create_engine("sqlite:///example.db")
    Base.metadata.create_all(engine)
    return "Created database."

def get_session():
    DBSession = sessionmaker(bind=engine)
    return DBSession()

def read_all(args):
    session = get_session()
    publications = session.query(Publication).all()
    for pub in publications:
        pub.save_front_page()
    return "Read {} front pages.".format(len(publications))

def add_publication(args):
    name = args.name
    url = args.url
    session = get_session()
    new_publication = Publication(name=name, url=url
                        , start=args.start, end=args.end)
    session.add(new_publication)
    session.commit()
    mkdir(path_to_corpus + new_publication.name_as_folder())
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
    read = subparsers.add_parser("read", help="Read followed front pages")
    follow.set_defaults(func=add_publication)
    init.set_defaults(func=init_db)
    read.set_defaults(func=read_all)
    
    args = parser.parse_args()
    res = args.func(args)
    print(res)
