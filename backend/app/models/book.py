import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Testament(str, enum.Enum):
    OT = "OT"
    NT = "NT"


class Genre(str, enum.Enum):
    LAW = "Law"
    HISTORY = "History"
    WISDOM = "Wisdom"
    PROPHECY = "Prophecy"
    POETRY = "Poetry"
    GOSPEL = "Gospel"
    ACTS = "Acts"
    EPISTLE = "Epistle"
    APOCALYPTIC = "Apocalyptic"


class OriginalLanguage(str, enum.Enum):
    HEBREW = "Hebrew"
    ARAMAIC = "Aramaic"
    GREEK = "Greek"
    HEBREW_ARAMAIC = "HebrewAramaic"


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True)
    osis_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # "Gen", "Matt"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False)
    testament: Mapped[Testament] = mapped_column(Enum(Testament, name="testament_enum"), nullable=False)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("author.id"))
    genre: Mapped[Genre] = mapped_column(Enum(Genre, name="genre_enum"), nullable=False)
    language_original: Mapped[OriginalLanguage] = mapped_column(
        Enum(OriginalLanguage, name="original_language_enum"), nullable=False
    )
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)  # canonical 1-66

    author: Mapped["Author | None"] = relationship("Author", back_populates="books")  # noqa: F821
    chapters: Mapped[list["Chapter"]] = relationship("Chapter", back_populates="book")  # noqa: F821
    verses: Mapped[list["Verse"]] = relationship("Verse", back_populates="book")  # noqa: F821
