# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy import DateTime, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from reader import read_front_page
import datetime

def today_string():
    return strftime("%Y%m%d%H%M%S")

path_to_corpus = "corpus/"
Base = declarative_base()

class Word(Base):
    __tablename__ = "word"
    id = Column(Integer, primary_key=True)
    word = Column(String, index=True)
    proper = Column(Boolean)
    UniqueConstraint('word', 'proper')

class Forbidden(Base):
    __tablename__ = "forbidden"
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("word.id")
                ,nullable = False)
    # Can and SHOULD be null for general interdictions
    publication_id = Column(Integer, ForeignKey("publication.id"))

class Publication(Base):
    __tablename__ = "publication"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    # Front page begin AFTER this value (cutting the header)
    start = Column(String)
    # Front page stops BEFORE this value (cutting the footer)
    end = Column(String)
    front_pages = relationship("FrontPage", cascade="delete"
                            , backref="publication")

class FrontPage(Base):
    __tablename__ = "frontpage"
    id = Column(Integer, primary_key=True)
    publication_id = Column(Integer, ForeignKey("publication.id")
                    ,nullable = False, index=True)
    time_of_publication = Column(DateTime
            , default=datetime.datetime.utcnow, index=True)
    lexical_richness = Column(Float)
    words = relationship("WordCount", cascade="delete")

class WordCount(Base):
    __tablename__ = "wordcount"
    id = Column(Integer, primary_key=True)
    frontpage_id = Column(Integer, ForeignKey("frontpage.id")
                ,nullable = False, index=True)
    word_id = Column(Integer, ForeignKey("word.id")
                ,nullable = False, index=True)
    count = Column(Integer)

