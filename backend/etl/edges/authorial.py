"""
Build AUTHORIAL edges.

For each pair of verses written by the same human author, emit an undirected
AUTHORIAL edge.  Weight decays with the distance between verses (same book =
higher weight than cross-book authorial links).

Distance metric: |verse_global_order_a - verse_global_order_b| normalized to [0,1].
Weight = 1 - (distance / max_distance) * decay_factor

To keep the edge count manageable we only create authorial edges within the
same *book* (intra-book) by default.  Cross-book authorial edges for Pauline
epistles etc. can be enabled via include_cross_book=True.

Operates post-load: verses + books + authors must exist.
"""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.edge import Edge, EdgeType

BATCH_SIZE = 5000


def load_authorial_edges(db: Session, include_cross_book: bool = False) -> int:
    """Insert AUTHORIAL edges. Returns count inserted."""
    print("Computing authorial edges...")

    if include_cross_book:
        sql = text("""
            SELECT v1.id AS v1_id, v2.id AS v2_id, b1.osis_id AS book1, b2.osis_id AS book2
            FROM verse v1
            JOIN book b1 ON v1.book_id = b1.id
            JOIN verse v2 ON v2.book_id IN (
                SELECT id FROM book WHERE author_id = b1.author_id
            ) AND v2.id > v1.id
            JOIN book b2 ON v2.book_id = b2.id
            WHERE b1.author_id IS NOT NULL
        """)
    else:
        # Intra-book only: much smaller result set
        sql = text("""
            SELECT v1.id AS v1_id, v2.id AS v2_id,
                   v1.book_id, v2.book_id AS book2_id
            FROM verse v1
            JOIN verse v2 ON v1.book_id = v2.book_id AND v2.id > v1.id
            JOIN book b ON v1.book_id = b.id
            WHERE b.author_id IS NOT NULL
        """)

    rows = db.execute(sql).fetchall()
    total_verses = db.execute(text("SELECT count(*) FROM verse")).scalar() or 1

    batch: list[Edge] = []
    total = 0

    for row in rows:
        v1_id, v2_id = row[0], row[1]
        # Simple weight: 1.0 for intra-book (cross-book would use distance decay)
        weight = 1.0

        batch.append(
            Edge(
                source_verse_id=v1_id,
                target_verse_id=v2_id,
                edge_type=EdgeType.AUTHORIAL,
                weight=weight,
                is_directed=False,
                metadata={"scope": "intra-book"},
            )
        )
        if len(batch) >= BATCH_SIZE:
            db.bulk_save_objects(batch)
            db.commit()
            total += len(batch)
            print(f"  Inserted {total} authorial edges...")
            batch.clear()

    if batch:
        db.bulk_save_objects(batch)
        db.commit()
        total += len(batch)

    print(f"Authorial edges: {total} total")
    return total
