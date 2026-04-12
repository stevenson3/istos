from datetime import datetime

from pydantic import BaseModel

from app.models.edge import EdgeType


class EdgeRead(BaseModel):
    id: int
    source_verse_id: int
    target_verse_id: int
    edge_type: EdgeType
    weight: float
    is_directed: bool
    metadata: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
