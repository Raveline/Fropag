# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import config

class ConfigException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

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
    return engine

Base = declarative_base()
engine = get_engine()
db_session = scoped_session(sessionmaker(bind=engine))
