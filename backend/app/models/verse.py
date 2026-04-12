from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Verse(Base):
    __tablename__ = "verse"
    __table_args__ = (
        Index("idx_verse_osis_ref", "osis_ref"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapter.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"), nullable=False)  # denormalized
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    osis_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # "Gen.1.1"

    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="verses")  # noqa: F821
    book: Mapped["Book"] = relationship("Book", back_populates="verses")  # noqa: F821
    texts: Mapped[list["VerseText"]] = relationship("VerseText", back_populates="verse")  # noqa: F821
    tokens: Mapped[list["VerseToken"]] = relationship("VerseToken", back_populates="verse")  # noqa: F821
    source_edges: Mapped[list["Edge"]] = relationship(  # noqa: F821
        "Edge", foreign_keys="Edge.source_verse_id", back_populates="source_verse"
    )
    target_edges: Mapped[list["Edge"]] = relationship(  # noqa: F821
        "Edge", foreign_keys="Edge.target_verse_id", back_populates="target_verse"
    )
    topics: Mapped[list["VerseTopic"]] = relationship("VerseTopic", back_populates="verse")  # noqa: F821
