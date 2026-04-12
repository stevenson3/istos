# Development Setup

## Prerequisites

- Python 3.11+
- Docker (for the database)
- `pip` or `uv`

## 1. Start the database

```bash
docker compose up db -d
```

This starts `pgvector/pgvector:pg16` on port 5432 with credentials `istos/istos/istos` (user/password/db). The `pgvector` extension is available but must be enabled per-database — the migration handles this.

## 2. Install backend dependencies

```bash
cd backend
pip install -e .
```

To include embedding support:

```bash
pip install -e ".[embeddings]"
```

To include dev tooling (pytest, ruff):

```bash
pip install -e ".[dev]"
```

## 3. Configure environment

```bash
cp .env.example .env
# Edit .env if your DB credentials differ from the defaults
```

The only required variable is `DATABASE_URL`. The default (`postgresql+psycopg://istos:istos@localhost:5432/istos`) matches the docker-compose service.

## 4. Run migrations

```bash
cd backend
alembic upgrade head
```

This creates all tables and indexes, including the HNSW vector indexes. The `pgvector` extension is enabled by the migration itself via `CREATE EXTENSION IF NOT EXISTS vector`.

## 5. Run the ETL pipeline

```bash
python -m etl.pipeline download   # fetch raw sources (~few hundred MB)
python -m etl.pipeline canon      # seed 31,102 verses
python -m etl.pipeline texts      # load BSB + optional LXX + Delitzsch
python -m etl.pipeline tokens     # load OSHB + MorphGNT morphology
python -m etl.pipeline edges      # build all edge types
```

Each step can be re-run independently. Steps that encounter a missing source file (e.g. LXX) skip cleanly with a log message.

## 6. Start the API

```bash
uvicorn app.main:app --reload
```

API is at `http://localhost:8000`. Swagger UI at `http://localhost:8000/docs`.

## Running with Docker (full stack)

```bash
docker compose up
```

This builds and starts both `db` and `backend` services. The backend mounts `./backend` as a volume with `--reload` so edits are reflected immediately. ETL can be run inside the container:

```bash
docker compose exec backend python -m etl.pipeline
```

## Database migrations

Create a new migration after changing any model:

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Alembic reads `DATABASE_URL` from the environment, overriding `alembic.ini`. The `alembic/env.py` imports all models via `import app.models` to ensure the full metadata is available for autogeneration.

## Running tests

```bash
cd backend
pytest
```

Tests live in `backend/tests/` (not yet created). The test setup requires a live database — do not mock it. Use a separate `istos_test` database or a transaction-per-test fixture that rolls back after each test.

## Linting

```bash
ruff check .
ruff format .
```

## Verification queries

After a full ETL run, these SQL queries confirm data integrity:

```sql
-- Verse count (expect ~31,102)
SELECT count(*) FROM verse;

-- VerseText breakdown by language
SELECT language_code, translation_name, count(*)
FROM verse_text
GROUP BY language_code, translation_name
ORDER BY language_code;

-- Edge type distribution
SELECT edge_type, count(*) FROM edge GROUP BY edge_type;

-- John 3:16 in all languages
SELECT language_code, translation_name, left(text, 80)
FROM verse_text
WHERE verse_id = (SELECT id FROM verse WHERE osis_ref = 'John.3.16');

-- LINGUISTIC edges for ἀγάπη (G26)
SELECT count(*) FROM edge
WHERE edge_type = 'LINGUISTIC'
  AND metadata->>'strong_number' = 'G26';
```
