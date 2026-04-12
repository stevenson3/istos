from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.verse import Verse
from app.models.verse_text import LanguageCode, VerseText
from app.models.verse_token import VerseToken
from app.schemas.verse import VerseRead

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[VerseRead])
def search_verses(
    q: str = Query(min_length=1),
    lang: LanguageCode | None = None,
    strong: str | None = Query(default=None, description="Strong's number e.g. G26 or H157"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    if strong:
        # Lemma / Strong's number search
        verse_ids_subq = (
            select(VerseToken.verse_id)
            .where(VerseToken.strong_number == strong.upper())
            .scalar_subquery()
        )
        stmt = (
            select(Verse)
            .options(selectinload(Verse.texts), selectinload(Verse.tokens))
            .where(Verse.id.in_(verse_ids_subq))
        )
    else:
        # Full-text search against VerseText rows
        text_filter = VerseText.text.ilike(f"%{q}%")
        if lang:
            text_filter = (VerseText.language_code == lang) & text_filter

        verse_ids_subq = (
            select(VerseText.verse_id).where(text_filter).scalar_subquery()
        )
        stmt = (
            select(Verse)
            .options(selectinload(Verse.texts), selectinload(Verse.tokens))
            .where(Verse.id.in_(verse_ids_subq))
        )

    stmt = stmt.order_by(Verse.id).offset((page - 1) * page_size).limit(page_size)
    return db.scalars(stmt).all()


@router.get("/edges", response_model=list)
def list_edges(
    source: str | None = None,
    edge_type: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    from app.models.edge import Edge, EdgeType
    from app.schemas.edge import EdgeRead

    stmt = select(Edge)
    if source:
        source_verse = db.scalar(select(Verse).where(Verse.osis_ref == source))
        if source_verse:
            stmt = stmt.where(
                or_(
                    Edge.source_verse_id == source_verse.id,
                    Edge.target_verse_id == source_verse.id,
                )
            )
    if edge_type:
        stmt = stmt.where(Edge.edge_type == EdgeType(edge_type.upper()))

    stmt = stmt.order_by(Edge.id).offset((page - 1) * page_size).limit(page_size)
    edges = db.scalars(stmt).all()
    return [EdgeRead.model_validate(e) for e in edges]
