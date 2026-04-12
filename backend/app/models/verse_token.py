from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VerseToken(Base):
    __tablename__ = "verse_token"
    __table_args__ = (
        Index("idx_verse_token_strong", "strong_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey("verse.id"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # word order within verse
    surface_form: Mapped[str] = mapped_column(String(200), nullable=False)  # actual text
    lemma: Mapped[str | None] = mapped_column(String(200))
    strong_number: Mapped[str | None] = mapped_column(String(10))  # "H1234" or "G1234"
    morph_code: Mapped[str | None] = mapped_column(String(50))     # e.g. "Ncmsa" or "V-PAI-3S"
    part_of_speech: Mapped[str | None] = mapped_column(String(50))
    gloss: Mapped[str | None] = mapped_column(String(500))         # English gloss from Strong's

    verse: Mapped["Verse"] = relationship("Verse", back_populates="tokens")  # noqa: F821
