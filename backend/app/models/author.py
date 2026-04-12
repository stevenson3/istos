from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    period: Mapped[str | None] = mapped_column(String(100))   # e.g. "8th century BCE"
    description: Mapped[str | None] = mapped_column(Text)

    books: Mapped[list["Book"]] = relationship("Book", back_populates="author")  # noqa: F821
