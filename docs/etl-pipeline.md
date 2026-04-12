# ETL Pipeline

## Overview

The ETL pipeline lives in `backend/etl/`. It runs as a series of discrete steps, each of which can be executed independently. All steps are orchestrated by `pipeline.py`.

```
Step 1: download      — fetch raw source files from GitHub / eBible.org
Step 2: canon         — seed the Book/Chapter/Verse scaffold
Step 3: texts         — load VerseText rows (BSB, LXX, Delitzsch)
Step 4: tokens        — load VerseToken rows (OSHB, MorphGNT)
Step 5: edges         — build CITATIONAL, LINGUISTIC, AUTHORIAL edges
```

## Running the pipeline

```bash
cd backend

# Full run (all steps in order)
python -m etl.pipeline

# Individual steps
python -m etl.pipeline download
python -m etl.pipeline canon
python -m etl.pipeline texts
python -m etl.pipeline tokens
python -m etl.pipeline edges

# Single edge type
python -m etl.pipeline edges:citational
python -m etl.pipeline edges:linguistic
python -m etl.pipeline edges:authorial
```

Steps are idempotent where possible — `seed_canon` checks for existing rows before inserting, so re-running it is safe.

## Step 1 — Download (`etl/download.py`)

Downloads five zip/xlsx files to `data/raw/`. Skips files that already exist (checks for file presence, not content hash). Uses `httpx` for streaming downloads with a `tqdm` progress bar.

| Key | URL | Destination |
|-----|-----|-------------|
| `oshb` | github.com/openscriptures/morphhb | `morphhb-master.zip` |
| `morphgnt` | github.com/morphgnt/sblgnt | `sblgnt-master.zip` |
| `bsb` | bereanbible.com/bsb.xlsx | `bsb.xlsx` |
| `openbible` | a.openbible.info/bulk/cross-references.zip | `cross-references.zip` |
| `delitzsch` | github.com/openscriptures/HebrewNT | `HebrewNT-master.zip` |

The LXX is not automatically downloaded — it requires academic registration with CATSS. Place `lxx.txt` (or `lxx.xml`) in `data/raw/` manually. The LXX step skips cleanly with a message if the file is absent.

## Step 2 — Canon scaffold (`etl/load.py` → `seed_canon`)

Inserts the complete Book/Chapter/Verse hierarchy from two static data structures in the ETL code:

- `CANON` in `etl/transform.py` — 66 dicts, one per book, with metadata (name, OSIS ID, testament, genre, language, author)
- `VERSE_COUNTS` in `etl/load.py` — dict mapping OSIS book ID to a list of per-chapter verse counts (KJV/Protestant baseline)

Insertion order: Author rows → Book rows → Chapter rows → Verse rows. Each level uses `db.flush()` to make IDs available before the next level is inserted.

The function returns a `dict[str, int]` mapping `osis_ref → verse.id`. This map is passed to all subsequent steps as the join key between source data and the DB.

## Step 3 — Verse texts (`etl/sources/`)

Each source parser is a generator that yields dicts with keys:

```python
{
    "osis_ref": "Gen.1.1",
    "language_code": "heb",        # or "grc", "eng", "heb-virtual"
    "text": "בְּרֵאשִׁ֖ית ...",
    "translation_name": "OSHB",
    "is_virtual": False,
    "source_url": "https://...",
}
```

`load_verse_texts()` in `etl/load.py` converts these to `VerseText` ORM objects and calls `db.bulk_save_objects()`. Rows whose `osis_ref` is not in the canon map (from step 2) are silently skipped and counted.

### Source parsers

**`bsb.py`** — reads `bsb.xlsx` with openpyxl. The BSB spreadsheet has a `Verse` column (`"Genesis 1:1"` format) and a `BSB` text column. A lookup dict maps full English book names to OSIS IDs.

**`lxx.py`** — handles both plain-text (one line per verse: `Gen 1:1 Ἐν ἀρχῇ...`) and OSIS XML. Has a CATSS/Rahlfs abbreviation → OSIS ID map for variant book spellings. Raises `FileNotFoundError` if no source file exists; the pipeline catches this and continues.

**`delitzsch.py`** — handles both plain-text and OSIS XML layouts from the HebrewNT repository. Sets `is_virtual=True` and `language_code="heb-virtual"` on all rows.

## Step 4 — Morphological tokens (`etl/sources/`)

Token parsers yield dicts with keys:

```python
{
    "osis_ref": "Gen.1.1",
    "language_code": "heb",
    "position": 0,               # 0-based word index within verse
    "surface_form": "בְּרֵאשִׁ֖ית",
    "lemma": "strong:H07225 ...",
    "strong_number": "H7225",    # extracted by regex
    "morph_code": "HR/Ncfsa",
    "part_of_speech": "HR",
    "gloss": None,               # populated separately from Strong's JSON
}
```

`load_verse_tokens()` batches inserts at 5,000 rows per commit.

**`oshb.py`** — opens `morphhb-master.zip`, reads each `wlc/<Book>.xml` file, and iterates `<w>` elements within `<verse osisID="Gen.1.1">` elements. Strong's number is extracted from the `lemma` attribute via regex (`strong:H\d+`). Aramaic tokens are identified by morph codes starting with `oshb:A` and tagged `language_code="arc"`.

**`morphgnt.py`** — opens `sblgnt-master.zip`, reads space-delimited text files (one word per line). Column layout: `bcv word-num pos-code parse-code text word normalized lemma`. The `bcv` field (e.g. `61001001`) encodes book/chapter/verse using MorphGNT's two-digit book numbering scheme (61 = Matthew). A `NT_BOOK_MAP` dict converts to OSIS IDs.

## Step 5 — Edges (`etl/edges/`)

All three edge modules operate post-load — they query the `verse` and `verse_token` tables that must already be populated.

### CITATIONAL (`edges/citational.py`)

Reads the OpenBible cross-reference CSV (inside `cross-references.zip`). Each row has `from_verse`, `to_verse`, and `votes`. Votes are converted to a `weight` in [0, 1]:

```python
weight = max(0.0, min(1.0, (votes + 5) / 55.0))
```

Rows are inserted in batches of 2,000 with `db.bulk_save_objects()`. Verse refs not present in the DB (e.g. deuterocanonical books) are skipped.

### LINGUISTIC (`edges/linguistic.py`)

Uses a single SQL query to group all `(strong_number, verse_id)` pairs:

```sql
SELECT strong_number, array_agg(DISTINCT verse_id ORDER BY verse_id)
FROM verse_token
WHERE strong_number IS NOT NULL
GROUP BY strong_number
HAVING count(DISTINCT verse_id) BETWEEN 2 AND 200
```

The upper bound of 200 verses filters out high-frequency function words (e.g. H853 "et", G2532 "kai") that would otherwise generate combinatorially explosive edge counts. For each qualifying lemma, every pair in the verse list gets one LINGUISTIC edge with `weight=1.0` and `metadata={"strong_number": "G26"}`.

### AUTHORIAL (`edges/authorial.py`)

Queries all verse pairs within the same book where the book has an `author_id`. Every such pair becomes an AUTHORIAL edge with `weight=1.0`. Intra-book scope is the default; cross-book Pauline linking can be enabled with `include_cross_book=True` (disabled by default because it would generate millions of edges across 13 Pauline epistles).
