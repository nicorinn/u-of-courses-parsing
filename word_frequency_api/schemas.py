from typing import List
from pydantic import BaseModel


class SectionBase(BaseModel):
    department_and_number: str
    year: int
    quarter: str
    number: int

    class Config:
        orm_mode = True


class WordBase(BaseModel):
    word: str

    class Config:
        orm_mode = True


class SectionSchema(SectionBase):
    word: List[WordBase]


class WordSchema(WordBase):
    sections: List[SectionBase]


class SectionAndWordsSchema(BaseModel):
    section: SectionBase
    words: List[str]
