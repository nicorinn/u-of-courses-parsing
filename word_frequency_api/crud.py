from sqlalchemy import select, func
from sqlalchemy.orm import Session

import models
import schemas


def get_section(db: Session, section: schemas.SectionSchema):
    statement = select(models.Section).filter_by(
        department_and_number=section.department_and_number,
        year=section.year,
        quarter=section.quarter,
        number=section.number
    )
    return db.execute(statement).scalar_one_or_none()


def get_word(db: Session, word: str):
    statement = select(models.Word).filter_by(
        word=word
    )
    return db.execute(statement).scalar_one_or_none()


def count_sections(db: Session):
    return db.query(models.Section).count()


def add_section(db: Session, section_and_words: schemas.SectionAndWordsSchema):
    # only add section if it already exists
    existing_section = get_section(section_and_words.section)
    if existing_section:
        return None
    words = section_and_words.words
    query_results = db.query(models.Word.word).filter(
        models.Word.word.in_(words)).all()
    db_words = [w[0] for w in query_results]

    new_section = models.Section(**section_and_words.section.dict())
    # add sections words that are not currently in database
    for word in words:
        if word not in db_words:
            new_word = models.Word()
            new_word.word = word
            db.add(new_word)

    db.commit()
    # get all words for this section
    db_words = query_results = db.query(models.Word).filter(
        models.Word.word.in_(words)).all()

    new_section.words = db_words

    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    return new_section


def add_word(db: Session, word_and_count: schemas.WordSchema):
    existing_word = get_word(db, word_and_count.word)
    if existing_word != None:
        db.commit()
        db.refresh(existing_word)
        return existing_word
    else:
        print(word_and_count)
        new_word = models.Word(word=word_and_count.word)
        print(new_word)
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        return new_word
