from pydantic import BaseModel

from app.models.book import Genre, OriginalLanguage, Testament


class AuthorRead(BaseModel):
    id: int
    name: str
    period: str | None = None

    model_config = {"from_attributes": True}


class BookRead(BaseModel):
    id: int
    osis_id: str
    name: str
    abbreviation: str
    testament: Testament
    genre: Genre
    language_original: OriginalLanguage
    order_num: int
    author: AuthorRead | None = None

    model_config = {"from_attributes": True}


class ChapterRead(BaseModel):
    id: int
    book_id: int
    number: int

    model_config = {"from_attributes": True}
