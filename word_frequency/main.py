from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from word_frequency import schemas
from word_frequency import models
from word_frequency.crud import add_section, add_word, get_section, get_word
from word_frequency.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Word frequency API running"}


@app.get("/words/{word}", response_model=schemas.Word)
def getWord(word: str, db: Session = Depends(get_db)):
    word_result = get_word(db, word)
    if word_result is None:
        raise HTTPException(status_code=404, detail="Word not found")

    return word_result


@app.post("/words", response_model=schemas.Word)
def saveWord(word: schemas.Word, db: Session = Depends(get_db)):
    result = add_word(db, word)
    return result


@app.post("/sections")
def saveSection(section: schemas.Section, db: Session = Depends(get_db)):
    existing_section = get_section(db, section)
    if existing_section is None:
        result = add_section(db, section)
        return result
    return {"message": "Section already exists"}
