from pydantic import BaseModel


class Section(BaseModel):
    department_and_number: str
    year: int
    quarter: str
    number: int

    class Config:
        orm_mode = True


class Word(BaseModel):
    word: str
    count: int

    class Config:
        orm_mode = True
