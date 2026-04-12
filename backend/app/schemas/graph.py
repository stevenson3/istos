from pydantic import BaseModel

from app.schemas.edge import EdgeRead
from app.schemas.verse import VerseRead


class VerseGraph(BaseModel):
    """A verse together with its N-hop neighbourhood."""

    root: VerseRead
    nodes: list[VerseRead]   # all verses in the subgraph (includes root)
    edges: list[EdgeRead]
    depth: int
