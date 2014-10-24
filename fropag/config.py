# -*- coding: utf-8 -*-
# Config with constants
DB_USER = None
DB_PASSWORD = None
DB_HOST = None
DB_PORT = None
DB_NAME = None
DB_URI = None
SECRET_KEY = None
LOGIN = None
PASSWORD = None

class ConfigException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def check_config():
    config_values = [DB_USER, DB_PASSWORD, DB_HOST
                    ,DB_PORT, DB_NAME]
    is_there_none = any([v is None for v in config_values])
    if is_there_none:
        none_value = ""
        if DB_USER is None:
            none_value = "DB_USER"
        if DB_PASSWORD is None:
            none_value = "DB_PASSWORD"
        if DB_HOST is None:
            none_value = "DB_HOST"
        if DB_PORT is None:
            none_value = "DB_PORT"
        if DB_NAME is None:
            none_value = "DB_NAME"
        raise ConfigException(none_value + " in config.py is None. Fill it before using Fropag.")
