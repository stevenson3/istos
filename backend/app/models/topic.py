from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Topic(Base):
    __tablename__ = "topic"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    verse_topics: Mapped[list["VerseTopic"]] = relationship("VerseTopic", back_populates="topic")


class VerseTopic(Base):
    __tablename__ = "verse_topic"
    __table_args__ = (
        UniqueConstraint("verse_id", "topic_id", name="uq_verse_topic"),
    )

    verse_id: Mapped[int] = mapped_column(ForeignKey("verse.id"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topic.id"), primary_key=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    verse: Mapped["Verse"] = relationship("Verse", back_populates="topics")  # noqa: F821
    topic: Mapped["Topic"] = relationship("Topic", back_populates="verse_topics")
