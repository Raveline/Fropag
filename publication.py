# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from reader import read_front_page

def today_string():
    return strfttime("%Y%m%d%H%M%S")

path_to_corpus = "corpus/"
Base = declarative_base()

class Word(Base):
    __tablename__ = "word"
    id = Column(Integer, primary_key=True)
    word = Column(String)

class Publication(Base):
    __tablename__ = "publication"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)

    def name_as_folder(self):
        return self.name.lower().replace(' ', '')

    def save_front_page(self):
        page = read_front_page(self.url)
        name = ''.join([path_to_corpus, self.name_as_folder, "/", today_string()])
        with open(name, 'w') as f:
            f.write(page)

class FrontPage(Base):
    __tablename__ = "frontpage"
    id = Column(Integer, primary_key=True)
    publication_id = Column(Integer, ForeignKey("publication.id"))
    time_of_publication = Column(DateTime)
    publication = relationship(Publication)

class WordCount(Base):
    __tablename__ = "wordcount"
    id = Column(Integer, primary_key=True)
    frontpage_id = Column(Integer, ForeignKey("frontpage.id"))
    word_id = Column(Integer, ForeignKey("word.id"))
    count = Column(Integer)

def init_db():
    engine = create_engine("sqlite:///example.db")
    Base.metadata.create_all(engine)
