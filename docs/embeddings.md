# Embeddings

Embeddings are not populated by the main ETL pipeline. They require a separate pass using GPU-capable hardware (or a cloud inference endpoint). The schema is fully ready: two nullable `vector(768)` columns on `verse_text`, with HNSW indexes that activate as soon as the first vectors are written.

## Two vectors per VerseText

| Column | Model | Purpose |
|--------|-------|---------|
| `embedding_cross` | LaBSE (`sentence-transformers/LaBSE`) | Cross-lingual similarity — all languages in the same 768-dim space |
| `embedding_lang` | Language-specific (see below) | Within-language similarity with higher fidelity |

### Language-specific models

| `language_code` | Translation | Model | Notes |
|-----------------|-------------|-------|-------|
| `heb` | OSHB | `onlplab/aleph-bert-base` (AlephBERT) | Best available Hebrew BERT; trained on modern Hebrew but applicable to Biblical |
| `heb-virtual` | Delitzsch | AlephBERT | Same model — treat like any Hebrew text |
| `arc` | (embedded in OSHB) | `Dicta-IL/BEREL` | Trained on Hebrew-Aramaic code-switching in Rabbinic texts |
| `grc` (NT) | SBLGNT | `pranaydeeps/Ancient-Greek-BERT` | Trained on First1KGreek, Perseus, PROIEL — good Koine coverage |
| `grc` (OT/LXX) | LXX | `bowphs/PhilBerta` | RoBERTa on ancient Greek + Patristica — better for LXX register |
| `eng` | BSB | `sentence-transformers/all-mpnet-base-v2` | High-quality English sentence embeddings |

## Why two vectors

**Cross-lingual (`embedding_cross`)** enables the core insight of the graph: comparing a Hebrew OT verse directly with a Greek NT verse. LaBSE maps all languages into the same space. This is how SEMANTIC edges across the testaments are generated.

**Language-specific (`embedding_lang`)** provides higher-quality comparisons within a single language. Within-Hebrew similarity using AlephBERT is more nuanced than LaBSE's cross-lingual projection. This column powers within-language SEMANTIC edges and interlinear search features.

## Generating SEMANTIC edges

After both embedding columns are populated, SEMANTIC edges are created by k-NN queries via pgvector:

```python
# Cross-lingual SEMANTIC edges (e.g. Hebrew OT ↔ Greek NT)
SELECT t1.verse_id, t2.verse_id,
       1 - (t1.embedding_cross <=> t2.embedding_cross) AS cosine_sim
FROM verse_text t1, verse_text t2
WHERE t1.language_code != t2.language_code
  AND 1 - (t1.embedding_cross <=> t2.embedding_cross) > 0.85
  AND t1.verse_id < t2.verse_id  -- deduplicate pairs
LIMIT 1000000;
```

The threshold of 0.85 cosine similarity is a starting point; tune it based on the density and quality of results.

Store the result as `Edge(edge_type=SEMANTIC, weight=cosine_sim, metadata={"model": "LaBSE", "lang_pair": "heb-grc"})`.

## HNSW indexes

The migration creates partial HNSW indexes at DDL time:

```sql
CREATE INDEX ON verse_text USING hnsw (embedding_cross vector_cosine_ops)
  WHERE embedding_cross IS NOT NULL;

CREATE INDEX ON verse_text USING hnsw (embedding_lang vector_cosine_ops)
  WHERE embedding_lang IS NOT NULL;
```

Partial indexes mean there is no overhead from null rows during the pre-embedding phase. Once vectors are populated, the HNSW index is used automatically by pgvector's `<=>` cosine distance operator.

## Suggested embedding pass script (not yet implemented)

```python
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, update
from app.database import SessionLocal
from app.models.verse_text import VerseText

model = SentenceTransformer("sentence-transformers/LaBSE")

with SessionLocal() as db:
    rows = db.scalars(
        select(VerseText).where(VerseText.embedding_cross.is_(None))
    ).all()

    texts = [r.text for r in rows]
    vectors = model.encode(texts, batch_size=64, show_progress_bar=True)

    for row, vec in zip(rows, vectors):
        row.embedding_cross = vec.tolist()

    db.commit()
```

Run once per language, swapping the model for `embedding_lang` using the language-specific model for each `language_code`.
