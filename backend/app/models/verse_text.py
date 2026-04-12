import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LanguageCode(str, enum.Enum):
    HEB = "heb"          # Biblical Hebrew (OSHB / Delitzsch)
    ARC = "arc"          # Biblical Aramaic (~268 verses)
    HEB_VIRTUAL = "heb-virtual"  # virtual/back-translated Hebrew NT
    GRC = "grc"          # Ancient Greek (LXX or NT)
    ENG = "eng"          # English translation


class ScriptDirection(str, enum.Enum):
    LTR = "ltr"
    RTL = "rtl"


class VerseText(Base):
    __tablename__ = "verse_text"
    __table_args__ = (
        Index("idx_verse_text_verse_lang", "verse_id", "language_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey("verse.id"), nullable=False)
    language_code: Mapped[LanguageCode] = mapped_column(
        Enum(LanguageCode, name="language_code_enum"), nullable=False
    )
    script_direction: Mapped[ScriptDirection] = mapped_column(
        Enum(ScriptDirection, name="script_direction_enum"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    translation_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "OSHB", "LXX", "SBLGNT", "BSB", "Delitzsch"
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))

    # pgvector embeddings — null until embedding pass runs
    # LaBSE 768-dim: same space for ALL languages (cross-lingual)
    embedding_cross: Mapped[list[float] | None] = mapped_column(Vector(768))
    # Language-specific model (AlephBERT / Ancient-Greek-BERT / all-mpnet-base-v2 / BEREL)
    embedding_lang: Mapped[list[float] | None] = mapped_column(Vector(768))

    verse: Mapped["Verse"] = relationship("Verse", back_populates="texts")  # noqa: F821
