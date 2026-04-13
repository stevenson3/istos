# Istos — Claude Code Guide

Istos is a Bible-as-graph application. Each verse is a node; edges capture citational, topical, linguistic, authorial, and semantic relationships. Stack: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + pgvector. ETL pipeline in `backend/etl/`.

Whenever you perform a code change, assess whether you should make an accompanying documentation change.

## Docs index

| Doc | What it covers |
|-----|---------------|
| [docs/architecture.md](docs/architecture.md) | Overall structure, request lifecycle, graph storage rationale, embedding column overview |
| [docs/data-model.md](docs/data-model.md) | Every table and column, edge types, directionality storage, indexes |
| [docs/etl-pipeline.md](docs/etl-pipeline.md) | Pipeline steps, how to run each one, details of every source parser and edge builder |
| [docs/data-sources.md](docs/data-sources.md) | Licenses, formats, and quirks of OSHB, MorphGNT, LXX, BSB, Delitzsch, OpenBible |
| [docs/api.md](docs/api.md) | All endpoints, query params, response shapes, example JSON |
| [docs/graph-traversal.md](docs/graph-traversal.md) | BFS algorithm, why Python over recursive CTEs, frontier explosion risk, undirected edge handling |
| [docs/embeddings.md](docs/embeddings.md) | The two-vector strategy (LaBSE + language-specific), model choices per language code, HNSW indexes, SEMANTIC edge generation |
| [docs/development.md](docs/development.md) | Local setup, migrations, running the ETL, verification queries |

## Key facts for working in this codebase

**OSIS refs** are the stable verse identifier everywhere: `"Gen.1.1"`, `"John.3.16"`. Never use raw integer IDs in inter-component contracts.

**Language codes** (`heb`, `arc`, `heb-virtual`, `grc`, `eng`) — `heb-virtual` is a distinct code (not `heb`) for the Delitzsch NT and any LLM-generated text. Filter by it to exclude virtual texts.

**Edge directionality** — only `CITATIONAL` edges are directed. All other types are stored once with `is_directed=false`. Any query that follows edges must use `WHERE source = X OR target = X`.

**Embedding columns are nullable** — `embedding_cross` and `embedding_lang` on `verse_text` are null until a separate embedding pass runs. Code that touches these must handle null.

**ETL is idempotent** — `seed_canon()` checks for existing rows before inserting. Re-running any step is safe. Source parsers that can't find their input file raise `FileNotFoundError`; the pipeline catches this and continues.

**No graph extension** — traversal uses Python BFS over the `edge` table. Do not introduce AGE, pgRouting, or other graph extensions without discussion.

## File map

```
backend/
  app/
    config.py          — Settings (DATABASE_URL via pydantic-settings)
    database.py        — engine, SessionLocal, get_db(), ensure_extensions()
    main.py            — FastAPI app, CORS, router registration
    models/            — SQLAlchemy ORM
      author.py        — Author
      book.py          — Book (+ Testament, Genre, OriginalLanguage enums)
      chapter.py       — Chapter
      verse.py         — Verse (the graph node)
      verse_text.py    — VerseText (+ LanguageCode, ScriptDirection enums)
      verse_token.py   — VerseToken (morphological words)
      edge.py          — Edge (+ EdgeType enum)
      topic.py         — Topic, VerseTopic
    schemas/           — Pydantic v2 read schemas
      verse.py         — VerseRead, VerseListItem, VerseTextRead, TokenRead
      edge.py          — EdgeRead
      graph.py         — VerseGraph
      book.py          — BookRead, ChapterRead, AuthorRead
    routers/
      books.py         — GET /books, /books/{osis_id}, /books/{osis_id}/verses
      verses.py        — GET /verses/{osis_ref}
      graph.py         — GET /verses/{osis_ref}/graph (BFS traversal)
      search.py        — GET /search, GET /search/edges
  etl/
    download.py        — fetch raw sources to data/raw/
    transform.py       — CANON list (66 books with metadata)
    load.py            — VERSE_COUNTS + seed_canon(), load_verse_texts(), load_verse_tokens()
    pipeline.py        — orchestrator; entry point via python -m etl.pipeline
    sources/
      oshb.py          — parse OSHB OSIS XML → VerseToken dicts
      morphgnt.py      — parse MorphGNT TSV → VerseToken dicts
      bsb.py           — parse BSB XLSX → VerseText dicts
      lxx.py           — parse LXX TXT/XML → VerseText dicts (manual download required)
      delitzsch.py     — parse Delitzsch HNT → VerseText dicts (is_virtual=True)
      openbible.py     — parse cross-ref CSV → Edge dicts
    edges/
      citational.py    — insert CITATIONAL edges from OpenBible
      linguistic.py    — compute LINGUISTIC edges from shared Strong's numbers
      authorial.py     — compute AUTHORIAL edges from book.author_id
  alembic/
    env.py             — Alembic config; imports app.models to register all tables
    versions/
      0001_initial_schema.py  — full DDL including HNSW vector indexes
```
