from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Chapter(Base):
    __tablename__ = "chapter"
    __table_args__ = (UniqueConstraint("book_id", "number", name="uq_chapter_book_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)

    book: Mapped["Book"] = relationship("Book", back_populates="chapters")  # noqa: F821
    verses: Mapped[list["Verse"]] = relationship("Verse", back_populates="chapter")  # noqa: F821
