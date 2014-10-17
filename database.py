# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, create_session
from sqlalchemy.ext.declarative import declarative_base
from config import check_config

def set_engine(uri, user, password, host, port, name):
    global engine
    check_config()
    connection_string = ''.join([uri,
                                 user,
                                 ':',
                                 password,
                                 '@',
                                 host,
                                 ':',
                                 port,
                                 '/',
                                 name])
    engine = create_engine(connection_string, isolation_level="AUTOCOMMIT")
    Base.metadata.bind = engine

def get_engine():
    return engine

def get_session():
    if engine is None:
        set_engine(config.DB_URI,
                   config.DB_USER,
                   config.DB_PASSWORD,
                   config.DB_HOST,
                   config.DB_PORT,
                   config.DB_NAME)

Base = declarative_base()
engine = None
db_session = scoped_session(lambda: create_session(bind=engine))
