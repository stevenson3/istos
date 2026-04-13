import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class EdgeType(str, enum.Enum):
    CITATIONAL = "CITATIONAL"   # NT quoting / echoing OT; directed
    TOPICAL = "TOPICAL"         # shared theme/topic tag; undirected
    LINGUISTIC = "LINGUISTIC"   # shared Strong's lemma; undirected
    AUTHORIAL = "AUTHORIAL"     # same human author; undirected
    SEMANTIC = "SEMANTIC"       # high embedding cosine similarity; undirected


class Edge(Base):
    __tablename__ = "edge"
    __table_args__ = (
        Index("idx_edge_source", "source_verse_id", "edge_type"),
        Index("idx_edge_target", "target_verse_id", "edge_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_verse_id: Mapped[int] = mapped_column(ForeignKey("verse.id"), nullable=False)
    target_verse_id: Mapped[int] = mapped_column(ForeignKey("verse.id"), nullable=False)
    edge_type: Mapped[EdgeType] = mapped_column(
        Enum(EdgeType, name="edge_type_enum"), nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 0.0–1.0
    is_directed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Flexible metadata: {"source": "openbible", "score": 0.87, "model": "LaBSE", ...}
    edge_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source_verse: Mapped["Verse"] = relationship(  # noqa: F821
        "Verse", foreign_keys=[source_verse_id], back_populates="source_edges"
    )
    target_verse: Mapped["Verse"] = relationship(  # noqa: F821
        "Verse", foreign_keys=[target_verse_id], back_populates="target_edges"
    )
