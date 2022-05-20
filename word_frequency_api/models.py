from email.policy import default
from enum import unique
from sqlalchemy import ForeignKey, Column, Integer, String, Table
from sqlalchemy.orm import relationship

from database import Base

section_words = Table(
    'section_words',
    Base.metadata,
    Column('section_id', ForeignKey(
        'sections.id'), primary_key=True),
    Column('word_id', ForeignKey('words.id'), primary_key=True)
)


class Section(Base):
    __tablename__ = 'sections'

    id = Column(Integer, primary_key=True, index=True)
    department_and_number = Column(String, index=True)
    year = Column(Integer)
    quarter = Column(String)
    number = Column(Integer)
    words = relationship('Word', secondary='section_words',
                         backref='words')


class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, index=True)
    sections = relationship(
        'Section', secondary='section_words', backref='sections')
