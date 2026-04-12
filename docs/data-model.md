# Data Model

## Entity hierarchy

```
Author
  └── Book (osis_id, testament, genre, language_original)
        └── Chapter
              └── Verse  ←— the graph node (osis_ref: "Gen.1.1")
                    ├── VerseText  (one per language/translation)
                    ├── VerseToken (one per word)
                    └── VerseTopic (join to Topic)

Edge (source_verse → target_verse, typed)
```

## Verse — the central node

`verse` is the node table. Every other table hangs off it.

| Column | Type | Notes |
|--------|------|-------|
| `id` | int PK | |
| `osis_ref` | str UNIQUE | Stable identifier: `"Gen.1.1"`, `"John.3.16"` |
| `number` | int | Verse number within chapter |
| `chapter_id` | FK → chapter | |
| `book_id` | FK → book | Denormalized for query speed (avoids join through chapter) |

`osis_ref` is the primary handle used throughout the API and ETL. It never changes regardless of how the DB row ID is assigned.

## VerseText — textual expressions

Each verse can have multiple `verse_text` rows, one per language/translation combination. OT verses get up to three rows (Hebrew, Greek/LXX, English). NT verses get up to three rows (virtual Hebrew/Delitzsch, Greek/SBLGNT, English/BSB).

| Column | Notes |
|--------|-------|
| `language_code` | Enum: `heb`, `arc`, `heb-virtual`, `grc`, `eng` |
| `translation_name` | `"OSHB"`, `"LXX"`, `"SBLGNT"`, `"BSB"`, `"Delitzsch"` |
| `is_virtual` | `true` for Delitzsch HNT and any LLM-generated text |
| `script_direction` | `"rtl"` for Hebrew/Aramaic, `"ltr"` for Greek/English |
| `embedding_cross` | `vector(768)` — LaBSE, nullable until embedding pass |
| `embedding_lang` | `vector(768)` — language-specific model, nullable |

`heb-virtual` is a distinct language code (not `heb`) so callers can filter virtual text out of queries without inspecting `is_virtual` separately.

## VerseToken — morphological words

One row per word in each source. Tokens are the basis for LINGUISTIC edge generation.

| Column | Notes |
|--------|-------|
| `position` | 0-based word order within the verse |
| `surface_form` | The word as it appears in the text |
| `lemma` | Dictionary form (from OSHB or MorphGNT) |
| `strong_number` | `"H1234"` or `"G1234"` — the cross-reference key |
| `morph_code` | Source-specific morphology string (OSHB: `"HR/Ncfsa"`, MorphGNT: `"V-PAI-3S"`) |
| `part_of_speech` | Extracted from morph_code |
| `gloss` | English meaning from Strong's (populated separately) |

Aramaic tokens inside OSHB are identified by morph codes starting with `A` and assigned `language_code = "arc"` (ISO 639-3).

## Edge — the graph edge

| Column | Notes |
|--------|-------|
| `source_verse_id` / `target_verse_id` | The connected pair |
| `edge_type` | `CITATIONAL`, `TOPICAL`, `LINGUISTIC`, `AUTHORIAL`, `SEMANTIC` |
| `weight` | 0.0–1.0 float; meaning depends on edge type |
| `is_directed` | Only `CITATIONAL` edges are directed (NT → OT) |
| `metadata` | JSON; carries source provenance and model info |

### Edge types

| Type | Directed | Weight meaning | Source |
|------|----------|----------------|--------|
| CITATIONAL | Yes | OpenBible vote score, normalized to [0,1] | OpenBible cross-reference CSV |
| TOPICAL | No | Tag relevance weight | OpenBible topics (future) |
| LINGUISTIC | No | 1.0 (binary — lemma is shared) | Computed from `strong_number` in `verse_token` |
| AUTHORIAL | No | 1.0 (intra-book) | Derived from `book.author_id` |
| SEMANTIC | No | Cosine similarity score | pgvector ANN query (future embedding pass) |

### Directionality storage decision

Undirected edges are stored once (`is_directed = false`). The graph endpoint and any edge query must use:

```sql
WHERE (source_verse_id = :id OR target_verse_id = :id)
  AND edge_type IN (...)
```

Both `idx_edge_source` and `idx_edge_target` are composite indexes on `(verse_id, edge_type)`, so both directions are covered.

## Book metadata

`book` carries enough metadata to reconstruct the canon scaffold without any external data at runtime:

- `testament`: `OT` / `NT`
- `genre`: Law, History, Wisdom, Poetry, Prophecy, Gospel, Acts, Epistle, Apocalyptic
- `language_original`: Hebrew, Aramaic, Greek, HebrewAramaic
- `order_num`: 1–66 canonical ordering

## Key indexes

```sql
-- Primary lookup
CREATE UNIQUE INDEX ON verse(osis_ref);
-- Graph traversal
CREATE INDEX idx_edge_source ON edge(source_verse_id, edge_type);
CREATE INDEX idx_edge_target ON edge(target_verse_id, edge_type);
-- Linguistic edge generation and search
CREATE INDEX idx_verse_token_strong ON verse_token(strong_number);
-- VerseText retrieval
CREATE INDEX idx_verse_text_verse_lang ON verse_text(verse_id, language_code);
-- Vector ANN (HNSW, conditional on non-null)
CREATE INDEX ON verse_text USING hnsw (embedding_cross vector_cosine_ops)
  WHERE embedding_cross IS NOT NULL;
CREATE INDEX ON verse_text USING hnsw (embedding_lang vector_cosine_ops)
  WHERE embedding_lang IS NOT NULL;
```
