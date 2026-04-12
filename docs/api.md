# API Reference

Base URL (local): `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## Books

### `GET /books`

Returns all 66 books in canonical order (Genesis → Revelation).

**Response:** `BookRead[]`

```json
[
  {
    "id": 1,
    "osis_id": "Gen",
    "name": "Genesis",
    "abbreviation": "Gen",
    "testament": "OT",
    "genre": "Law",
    "language_original": "Hebrew",
    "order_num": 1,
    "author": { "id": 1, "name": "Moses", "period": null }
  }
]
```

---

### `GET /books/{osis_id}`

Single book by OSIS ID (e.g. `Gen`, `Matt`, `Rev`).

**404** if not found.

---

### `GET /books/{osis_id}/verses`

Paginated verse list for a book.

**Query params:**

| Param | Default | Notes |
|-------|---------|-------|
| `chapter` | — | Filter to a specific chapter number |
| `page` | 1 | 1-based |
| `page_size` | 50 | |

**Response:** `VerseListItem[]` (id, osis_ref, number — no text or tokens)

---

## Verses

### `GET /verses/{osis_ref}`

Full verse with all textual expressions and morphological tokens.

`osis_ref` format: `Book.Chapter.Verse` — e.g. `Gen.1.1`, `John.3.16`, `Ps.119.105`

**Response:** `VerseRead`

```json
{
  "id": 1,
  "osis_ref": "John.3.16",
  "number": 16,
  "book_id": 43,
  "chapter_id": 1002,
  "texts": [
    {
      "id": 1,
      "language_code": "grc",
      "script_direction": "ltr",
      "text": "Οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον...",
      "translation_name": "SBLGNT",
      "is_virtual": false
    },
    {
      "id": 2,
      "language_code": "eng",
      "text": "For God so loved the world...",
      "translation_name": "BSB",
      "is_virtual": false
    },
    {
      "id": 3,
      "language_code": "heb-virtual",
      "script_direction": "rtl",
      "text": "כִּי כָּכָה אָהַב אֱלֹהִים...",
      "translation_name": "Delitzsch",
      "is_virtual": true
    }
  ],
  "tokens": [
    {
      "id": 1,
      "position": 0,
      "surface_form": "Οὕτως",
      "lemma": "οὕτως",
      "strong_number": "G3779",
      "morph_code": "D",
      "part_of_speech": "D",
      "gloss": "thus, in this way"
    }
  ]
}
```

**404** if `osis_ref` not found.

---

### `GET /verses/{osis_ref}/graph`

BFS subgraph centred on the given verse.

**Query params:**

| Param | Default | Notes |
|-------|---------|-------|
| `depth` | 1 | Hops from root. Capped at 3. |
| `edge_types` | all | Repeatable: `?edge_types=CITATIONAL&edge_types=LINGUISTIC` |

**Response:** `VerseGraph`

```json
{
  "root": { "osis_ref": "John.3.16", ... },
  "nodes": [ ... ],   // all verses in the subgraph, including root
  "edges": [ ... ],   // all edges traversed
  "depth": 1
}
```

At `depth=1`, returns all verses one edge away from the root (across the requested edge types). At `depth=2`, expands each of those verses one further hop. DB queries are issued once per depth level (breadth-first), not per node.

**Performance note:** At `depth=3` with all edge types, the frontier can reach thousands of nodes in heavily connected passages. If the response is too large, narrow `edge_types` first.

---

## Search

### `GET /search`

Verse search by text substring or Strong's number.

**Query params:**

| Param | Notes |
|-------|-------|
| `q` | Required (min 1 char). Text substring matched with `ILIKE %q%`. |
| `lang` | Optional. Filter to one language: `heb`, `grc`, `eng`, `arc`, `heb-virtual` |
| `strong` | Optional. If provided, `q` is ignored and verses are matched by Strong's number (e.g. `G26`, `H157`). Case-insensitive. |
| `page` | 1-based, default 1 |
| `page_size` | Default 20 |

**Response:** `VerseRead[]` (full verse objects with texts and tokens)

```bash
# All verses containing "love" in English
GET /search?q=love&lang=eng

# All verses that contain Strong's G26 (ἀγάπη)
GET /search?strong=G26

# Cross-lingual: all Greek verses with the lemma for "faith"
GET /search?strong=G4102
```

---

### `GET /search/edges`

Query edges by source verse or type.

**Query params:**

| Param | Notes |
|-------|-------|
| `source` | OSIS ref of the source/target verse |
| `edge_type` | `CITATIONAL`, `TOPICAL`, `LINGUISTIC`, `AUTHORIAL`, `SEMANTIC` |
| `page` | 1-based |
| `page_size` | Default 50 |

When `source` is provided, returns all edges where that verse is either `source_verse_id` or `target_verse_id` (handles undirected edges correctly).

---

## Schemas

### `VerseRead`
```
id, osis_ref, number, book_id, chapter_id
texts: VerseTextRead[]
tokens: TokenRead[]
```

### `VerseTextRead`
```
id, language_code, script_direction, text, translation_name, is_virtual
```
Note: embedding vectors are not included in API responses.

### `TokenRead`
```
id, position, surface_form, lemma, strong_number, morph_code, part_of_speech, gloss
```

### `EdgeRead`
```
id, source_verse_id, target_verse_id, edge_type, weight, is_directed, metadata, created_at
```

### `VerseGraph`
```
root: VerseRead
nodes: VerseRead[]
edges: EdgeRead[]
depth: int
```

### `BookRead`
```
id, osis_id, name, abbreviation, testament, genre, language_original, order_num
author: AuthorRead | null
```
