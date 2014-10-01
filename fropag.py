import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from publication import Publication, Base

engine = create_engine("sqlite:///example.db")
Base.metadata.bind = engine

def get_session():
    DBSession = sessionmaker(bind=engine)
    return DBSession()

def add_publication(args):
    name = args.name
    url = args.url
    session = get_session()
    new_publication = Publication(name=name, url=url)
    session.add(new_publication)
    session.commit()
    return "Saving publication with {} and {} ".format(name, url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    follow = subparsers.add_parser("follow", help="follow help")
    follow.add_argument("name", help="Name of the publication to follow.")
    follow.add_argument("url", help="URL of the front page for this publication.")
    follow.set_defaults(func=add_publication)

    args = parser.parse_args()
    res = args.func(args)
    print(res)
