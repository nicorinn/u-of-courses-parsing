from database import SessionLocal, engine
from crud import add_section, add_word, get_section, get_word, count_sections
import models
import schemas
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uvicorn
from typing import List
from dotenv import dotenv_values
from math import log

config = dotenv_values(".env")


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


@app.get("/api/words/{word}", response_model=int)
def getIdf(word: str, db: Session = Depends(get_db)):
    word_result = get_word(db, word)
    if word_result is None:
        raise HTTPException(status_code=404, detail="Word not found")
    docs_containing_term = len(word_result.sections)
    num_docs = count_sections(db)
    idf = float(log(1 + float(num_docs)/1 + docs_containing_term)) + 1
    return idf


@app.post("/api/words", response_model=List[schemas.WordSchema])
def saveWords(words: List[schemas.WordSchema], db: Session = Depends(get_db)):
    response_data = []
    for word_and_count in words:
        result = add_word(db, word_and_count)
        response_data.append(result)
    return response_data


@app.post("/api/words/word", response_model=schemas.WordSchema)
def saveWord(word: schemas.WordSchema, db: Session = Depends(get_db)):
    result = add_word(db, word)
    return result


@app.post("/api/sections")
def saveSection(section_and_words: schemas.SectionAndWordsSchema, db: Session = Depends(get_db)):
    section = section_and_words.section
    existing_section = get_section(db, section)
    if existing_section is None:
        result = add_section(db, section_and_words)
        return result
    return {"message": "Section already exists"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(config.get('API_PORT', 8001)))
