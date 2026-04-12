from pydantic import BaseModel

from app.models.verse_text import LanguageCode, ScriptDirection


class TokenRead(BaseModel):
    id: int
    position: int
    surface_form: str
    lemma: str | None = None
    strong_number: str | None = None
    morph_code: str | None = None
    part_of_speech: str | None = None
    gloss: str | None = None

    model_config = {"from_attributes": True}


class VerseTextRead(BaseModel):
    id: int
    language_code: LanguageCode
    script_direction: ScriptDirection
    text: str
    translation_name: str
    is_virtual: bool

    model_config = {"from_attributes": True}


class VerseListItem(BaseModel):
    id: int
    osis_ref: str
    number: int

    model_config = {"from_attributes": True}


class VerseRead(BaseModel):
    id: int
    osis_ref: str
    number: int
    book_id: int
    chapter_id: int
    texts: list[VerseTextRead] = []
    tokens: list[TokenRead] = []

    model_config = {"from_attributes": True}
