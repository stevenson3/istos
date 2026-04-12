# Architecture

## What Istos is

Istos treats the Bible as a graph. Each verse is a node (~31,102 total). Nodes are connected by typed edges that capture four kinds of relationship: citational, topical, linguistic, and authorial. A fifth edge type, semantic, is generated from embedding similarity after a separate embedding pass.

The name comes from Greek ἱστός — web, loom, mast. A web of verses.

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.0 (sync sessions) |
| Database | PostgreSQL 16 + pgvector extension |
| Migrations | Alembic |
| ETL | Pure Python scripts (`backend/etl/`) |
| Frontend | Next.js (planned) |

## Top-level layout

```
istos/
├── backend/
│   ├── app/           — FastAPI application (models, schemas, routers)
│   ├── etl/           — data pipeline (download → parse → load → edges)
│   ├── alembic/       — database migrations
│   └── pyproject.toml
├── data/
│   ├── raw/           — downloaded source files (gitignored)
│   └── processed/     — intermediate files (gitignored)
├── frontend/          — Next.js (not yet scaffolded)
└── docker-compose.yml
```

## Request lifecycle

```
Client
  → FastAPI router (app/routers/)
  → SQLAlchemy Session (app/database.py)
  → PostgreSQL
  → Pydantic schema (app/schemas/)
  → JSON response
```

Sessions are injected via `get_db()` FastAPI dependency. All queries use SQLAlchemy 2.0 `select()` style with `selectinload` for eager-loading relationships to avoid N+1 queries.

## Graph storage

The graph is stored in plain PostgreSQL — no graph database extension (no AGE, no Neo4j). This is intentional:

- The dataset is small (~31k nodes, ~2–5M edges at full load)
- Standard SQL with composite indexes is fast enough for depth ≤ 3 BFS traversals
- Recursive CTEs handle deeper traversals when needed
- Fewer moving parts, easier deployment

For undirected edges (TOPICAL, LINGUISTIC, AUTHORIAL, SEMANTIC), each relationship is stored as a single row with `is_directed = false`. Queries use `WHERE source_verse_id = X OR target_verse_id = X` rather than duplicating rows.

## Embedding columns

Two `vector(768)` columns live on `verse_text`, both nullable until an embedding pass runs:

- `embedding_cross` — LaBSE; same vector space for all languages, enabling cross-lingual similarity
- `embedding_lang` — language-specific model (AlephBERT, Ancient-Greek-BERT, all-mpnet-base-v2, BEREL)

HNSW indexes are created on both columns at migration time (conditional on `IS NOT NULL`) so ANN queries work as soon as the first embeddings are populated. See [embeddings.md](embeddings.md) for the full embedding strategy.
