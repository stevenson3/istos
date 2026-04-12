"""
Graph traversal endpoint.

Uses iterative BFS in Python over the edge table.  This is fast enough for
depth ≤ 3 with the ~31 k-node dataset.  At depth ≥ 4 the frontier can explode;
the endpoint caps depth at 3 and the caller controls which edge types to follow.
"""

from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.edge import Edge, EdgeType
from app.models.verse import Verse
from app.schemas.graph import VerseGraph
from app.schemas.verse import VerseRead
from app.schemas.edge import EdgeRead

router = APIRouter(prefix="/verses", tags=["graph"])

MAX_DEPTH = 3


@router.get("/{osis_ref}/graph", response_model=VerseGraph)
def get_verse_graph(
    osis_ref: str,
    depth: int = Query(default=1, ge=1, le=MAX_DEPTH),
    edge_types: list[EdgeType] = Query(default=list(EdgeType)),
    db: Session = Depends(get_db),
):
    root = db.scalar(
        select(Verse)
        .options(selectinload(Verse.texts), selectinload(Verse.tokens))
        .where(Verse.osis_ref == osis_ref)
    )
    if not root:
        raise HTTPException(status_code=404, detail=f"Verse '{osis_ref}' not found")

    visited_ids: set[int] = {root.id}
    frontier: deque[int] = deque([root.id])
    collected_edges: list[Edge] = []
    verse_map: dict[int, Verse] = {root.id: root}

    for _ in range(depth):
        if not frontier:
            break
        current_ids = list(frontier)
        frontier.clear()

        edges = db.scalars(
            select(Edge).where(
                or_(
                    Edge.source_verse_id.in_(current_ids),
                    Edge.target_verse_id.in_(current_ids),
                ),
                Edge.edge_type.in_(edge_types),
            )
        ).all()

        new_verse_ids: set[int] = set()
        for edge in edges:
            collected_edges.append(edge)
            for vid in (edge.source_verse_id, edge.target_verse_id):
                if vid not in visited_ids:
                    visited_ids.add(vid)
                    frontier.append(vid)
                    new_verse_ids.add(vid)

        if new_verse_ids:
            new_verses = db.scalars(
                select(Verse)
                .options(selectinload(Verse.texts), selectinload(Verse.tokens))
                .where(Verse.id.in_(new_verse_ids))
            ).all()
            for v in new_verses:
                verse_map[v.id] = v

    return VerseGraph(
        root=VerseRead.model_validate(root),
        nodes=[VerseRead.model_validate(v) for v in verse_map.values()],
        edges=[EdgeRead.model_validate(e) for e in collected_edges],
        depth=depth,
    )
