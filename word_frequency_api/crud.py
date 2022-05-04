from sqlalchemy import select, update
from sqlalchemy.orm import Session

import models
import schemas


def get_section(db: Session, section: schemas.Section):
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


def add_section(db: Session, section: schemas.Section):
    new_section = models.Section(**section.dict())

    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    return new_section


def add_word(db: Session, word_and_count: schemas.Word):
    existing_word = get_word(db, word_and_count.word)
    if existing_word != None:
        existing_word.count += word_and_count.count
        db.commit()
        db.refresh(existing_word)
        return existing_word
    else:
        print(word_and_count)
        new_word = models.Word(word=word_and_count.word,
                               count=word_and_count.count)
        print(new_word)
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        return new_word
