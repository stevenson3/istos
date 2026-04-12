# Graph Traversal

## How traversal works

The `GET /verses/{osis_ref}/graph` endpoint implements BFS (breadth-first search) in Python over the `edge` table. Each depth level is one round of DB queries — not one query per node.

```
depth=0  →  root verse only
depth=1  →  root + all verses one edge away
depth=2  →  depth-1 result + all verses one more hop away
depth=3  →  depth-2 result + one more hop (maximum)
```

**Code path:** `backend/app/routers/graph.py` → `get_verse_graph()`

### Algorithm

```
frontier = {root.id}
visited  = {root.id}
verse_map = {root.id: root}
edges_collected = []

for _ in range(depth):
    query edge table WHERE source OR target IN frontier AND edge_type IN requested_types
    for each edge:
        add to edges_collected
        for each endpoint not yet visited:
            add to next_frontier
    load full verse objects for next_frontier
    merge into verse_map
    frontier = next_frontier
```

This issues exactly `2 × depth` queries to the database: one for edges, one for verses, per depth level.

## Why BFS in Python, not recursive CTEs

Recursive CTEs (`WITH RECURSIVE`) are an alternative but they:
1. Cannot easily filter by edge type mid-recursion without complex lateral joins
2. Do not return the full verse data in a single pass — you still need a follow-up join
3. Are harder to cap safely at depth 3 without a cycle-detection clause

For this dataset size (~31k nodes), the Python BFS approach is simpler and fast enough. At depth=3 with all edge types, the total query time is typically under 200ms on local hardware.

## Undirected edge handling

All undirected edges (TOPICAL, LINGUISTIC, AUTHORIAL, SEMANTIC) are stored once with `is_directed = false`. The traversal queries both directions:

```python
select(Edge).where(
    or_(
        Edge.source_verse_id.in_(current_ids),
        Edge.target_verse_id.in_(current_ids),
    )
)
```

This means the `idx_edge_source` and `idx_edge_target` indexes are both used depending on which side the current frontier hits.

## Frontier explosion risk

At `depth=3` with `edge_types=LINGUISTIC`, a single verse can fan out to thousands of nodes — every verse sharing any of its lemmas. Callers should filter `edge_types` to the types they need. Practical combinations:

| Use case | Recommended edge_types |
|----------|------------------------|
| Citation network | `CITATIONAL` |
| Thematic cluster | `TOPICAL,AUTHORIAL` |
| Lexical web | `LINGUISTIC` |
| Full interconnect | all (use depth=1 only) |

The endpoint enforces `depth ≤ 3` as a hard cap.

## Graph storage decisions

**No graph extension.** No Apache AGE, no Neo4j, no graph database. PostgreSQL + proper indexes is sufficient for this dataset. The edge table has ~2–5M rows at full load, which is comfortably within the range where standard B-tree indexes on FK columns give sub-millisecond point lookups.

**Undirected edges stored once.** The alternative — duplicating each undirected edge in both directions — would halve query complexity (`WHERE source = X`) at the cost of doubling storage and insertion time. Given the dataset size, storing once and querying with `OR` is the right trade-off.

**Cycle detection.** The BFS `visited` set prevents infinite loops through cycles in the edge graph. A verse can appear in `edges_collected` multiple times (once per edge connecting it) but only appears in `verse_map` once.

## Example: John 3:16 at depth 2

```
GET /verses/John.3.16/graph?depth=2&edge_types=CITATIONAL
```

**Depth 1 frontier:** Verses with CITATIONAL edges to/from John 3:16 — typically Isaiah 53:12, Numbers 21:9, Psalm 22, and several Johannine parallels.

**Depth 2 frontier:** For each of those verses, their own CITATIONAL neighbours — expanding the network outward to OT passages those verses reference, and NT passages that quote the same OT texts.

The response `nodes` array contains all distinct verses encountered (including the root), and `edges` contains all edges traversed, allowing the frontend to reconstruct the full subgraph.
