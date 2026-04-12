from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.book import Book
from app.models.verse import Verse
from app.schemas.book import BookRead
from app.schemas.verse import VerseListItem

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookRead])
def list_books(db: Session = Depends(get_db)):
    books = db.scalars(
        select(Book).options(selectinload(Book.author)).order_by(Book.order_num)
    ).all()
    return books


@router.get("/{osis_id}", response_model=BookRead)
def get_book(osis_id: str, db: Session = Depends(get_db)):
    book = db.scalar(
        select(Book).options(selectinload(Book.author)).where(Book.osis_id == osis_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail=f"Book '{osis_id}' not found")
    return book


@router.get("/{osis_id}/verses", response_model=list[VerseListItem])
def list_book_verses(
    osis_id: str,
    chapter: int | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    book = db.scalar(select(Book).where(Book.osis_id == osis_id))
    if not book:
        raise HTTPException(status_code=404, detail=f"Book '{osis_id}' not found")

    stmt = select(Verse).where(Verse.book_id == book.id).order_by(Verse.id)
    if chapter is not None:
        stmt = stmt.join(Verse.chapter).where(Verse.chapter.has(number=chapter))

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    return db.scalars(stmt).all()
