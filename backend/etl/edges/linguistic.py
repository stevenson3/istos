"""
Build LINGUISTIC edges.

Strategy: for each Strong's number that appears in >= 2 verses, create an
undirected edge between every pair of verses sharing that number.

To avoid O(n²) explosion for high-frequency words (e.g. H853 "et", G2532 "kai"),
we cap the maximum number of edges per lemma (MAX_PAIRS_PER_LEMMA).

Operates post-load: verse_token rows must already exist.
"""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.edge import Edge, EdgeType

# Lemmas with more than this many verses are skipped (function words)
MAX_VERSES_PER_LEMMA = 200
BATCH_SIZE = 5000


def load_linguistic_edges(db: Session) -> int:
    """
    Use a SQL GROUP BY to find all (strong_number, verse_id) pairs, then
    emit edges for co-occurring verse pairs per lemma.
    """
    print("Computing linguistic edges via Strong's numbers...")

    # Fetch (strong_number, verse_ids[]) grouped, filtering high-frequency lemmas
    rows = db.execute(
        text("""
            SELECT strong_number, array_agg(DISTINCT verse_id ORDER BY verse_id) AS verse_ids
            FROM verse_token
            WHERE strong_number IS NOT NULL
            GROUP BY strong_number
            HAVING count(DISTINCT verse_id) BETWEEN 2 AND :max_verses
        """),
        {"max_verses": MAX_VERSES_PER_LEMMA},
    ).fetchall()

    batch: list[Edge] = []
    total = 0

    for strong_number, verse_ids in rows:
        # Generate all pairs for this lemma
        for i in range(len(verse_ids)):
            for j in range(i + 1, len(verse_ids)):
                batch.append(
                    Edge(
                        source_verse_id=verse_ids[i],
                        target_verse_id=verse_ids[j],
                        edge_type=EdgeType.LINGUISTIC,
                        weight=1.0,
                        is_directed=False,
                        metadata={"strong_number": strong_number},
                    )
                )
                if len(batch) >= BATCH_SIZE:
                    db.bulk_save_objects(batch)
                    db.commit()
                    total += len(batch)
                    print(f"  Inserted {total} linguistic edges...")
                    batch.clear()

    if batch:
        db.bulk_save_objects(batch)
        db.commit()
        total += len(batch)

    print(f"Linguistic edges: {total} total")
    return total
