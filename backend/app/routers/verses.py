from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.verse import Verse
from app.schemas.verse import VerseRead

router = APIRouter(prefix="/verses", tags=["verses"])


def _load_verse(osis_ref: str, db: Session) -> Verse:
    verse = db.scalar(
        select(Verse)
        .options(selectinload(Verse.texts), selectinload(Verse.tokens))
        .where(Verse.osis_ref == osis_ref)
    )
    if not verse:
        raise HTTPException(status_code=404, detail=f"Verse '{osis_ref}' not found")
    return verse


@router.get("/{osis_ref}", response_model=VerseRead)
def get_verse(osis_ref: str, db: Session = Depends(get_db)):
    return _load_verse(osis_ref, db)
