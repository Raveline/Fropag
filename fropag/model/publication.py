'''Model of Fropag, containing the classes we deal with.'''
# -*- coding: utf-8 -*-
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Enum
from sqlalchemy import DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime

from database import Base

class Word(Base):
    """A single word, identified as proper (ex. Mobile)
    or common (ex. mobile). Can be adjective, verb, substantive,
    etc."""
    __tablename__ = "word"
    id = Column(Integer, primary_key=True)
    word = Column(String, index=True)
    proper = Column(Boolean)
    UniqueConstraint('word', 'proper')

class Forbidden(Base):
    __tablename__ = "forbidden"
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("word.id"),
                     nullable=False)
    # Can and SHOULD be null for general interdictions
    publication_id = Column(Integer, ForeignKey("publication.id"))

class Publication(Base):
    """A newspaper, magazine or any kind of periodic publication
    we want to examine regularly."""
    __tablename__ = "publication"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    rythm = Column(Enum('DAILY', 'EVERY_TWO_DAYS',
                        'WEEKLY', 'EVERY_TWO_WEEKS', 'MONTHLY',
                        name='rythm'), default='DAILY')
    front_pages = relationship("FrontPage", cascade="delete",
                               backref="publication")

    def prefix_url_if_needed(self):
        """Append "http://" to a URL if it is missing.

        >>> p = Publication(url = "www.google.com")
        >>> p.prefix_url_if_needed()
        'http://www.google.com'

        >>> p = Publication(url = "http://www.google.com")
        >>> p.prefix_url_if_needed()
        'http://www.google.com'
        """
        if self.url.startswith("http"):
            return self.url
        else:
            return "http://" + self.url


class FrontPage(Base):
    """FrontPages are regular instances of publications.
    Each time we read the frontpage of a publication, we create
    one of those."""
    __tablename__ = "frontpage"
    id = Column(Integer, primary_key=True)
    publication_id = Column(Integer, ForeignKey("publication.id"),
                            nullable=False, index=True)
    time_of_publication = Column(DateTime, default=datetime.datetime.utcnow,
                                 index=True)
    lexical_richness = Column(Float)
    words = relationship("WordCount", cascade="delete")

class WordCount(Base):
    """WordCount link FrontPages and Words. They allow us to know
    how many time a word was counted on one frontpage."""
    __tablename__ = "wordcount"
    id = Column(Integer, primary_key=True)
    frontpage_id = Column(Integer, ForeignKey("frontpage.id"), nullable=False,
                          index=True)
    word_id = Column(Integer, ForeignKey("word.id"), nullable=False, index=True)
    count = Column(Integer)
