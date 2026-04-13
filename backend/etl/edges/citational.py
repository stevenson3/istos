"""
Build CITATIONAL edges.

Sources:
  1. OpenBible.info cross-reference CSV (bulk)
  2. (Future) Nestle-Aland NT apparatus for precise OT quotations

This module operates post-load: verses must already exist in the DB.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.edge import Edge, EdgeType
from app.models.verse import Verse
from etl.sources.openbible import iter_edges


def load_citational_edges(db: Session, batch_size: int = 2000) -> int:
    """Insert CITATIONAL edges from OpenBible. Returns count of edges inserted."""
    # Pre-load osis_ref → id map for fast lookup
    print("Loading verse ID map...")
    osis_to_id: dict[str, int] = {
        row.osis_ref: row.id for row in db.execute(select(Verse.osis_ref, Verse.id)).all()
    }

    batch: list[Edge] = []
    total = 0
    skipped = 0

    for raw in iter_edges():
        src_id = osis_to_id.get(raw["source_osis_ref"])
        tgt_id = osis_to_id.get(raw["target_osis_ref"])
        if not src_id or not tgt_id:
            skipped += 1
            continue

        batch.append(
            Edge(
                source_verse_id=src_id,
                target_verse_id=tgt_id,
                edge_type=EdgeType.CITATIONAL,
                weight=raw["weight"],
                is_directed=True,
                edge_metadata=raw["metadata"],
            )
        )
        if len(batch) >= batch_size:
            db.bulk_save_objects(batch)
            db.commit()
            total += len(batch)
            print(f"  Inserted {total} citational edges...")
            batch.clear()

    if batch:
        db.bulk_save_objects(batch)
        db.commit()
        total += len(batch)

    print(f"Citational edges: {total} inserted, {skipped} skipped (unknown refs)")
    return total
