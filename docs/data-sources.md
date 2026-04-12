# Data Sources

All sources are open-licensed. The pipeline downloads them automatically except where noted.

## Hebrew Old Testament — OSHB

**Open Scriptures Hebrew Bible**
- Repository: `openscriptures/morphhb` on GitHub
- Format: OSIS XML (one file per book, inside `wlc/`)
- License: CC BY 4.0
- Contents: Morphologically tagged Westminster Leningrad Codex; every word has a `lemma` attribute containing the Strong's number (`strong:H01234`) and a `morph` attribute with the OSHB morphology code

The morph code prefix encodes language: codes starting with `oshb:A` indicate Biblical Aramaic; all others are Hebrew. The parser (`etl/sources/oshb.py`) uses this to assign `language_code = "arc"` to ~268 Aramaic verses scattered across Daniel, Ezra, and Jeremiah 10:11.

## Greek New Testament — MorphGNT (SBLGNT)

**Morphologically tagged SBL Greek New Testament**
- Repository: `morphgnt/sblgnt` on GitHub
- Format: space-delimited text files, one word per line
- License: CC BY-SA 3.0
- Column layout: `book/chapter/verse  word-num  pos-code  parse-code  text  word  normalized  lemma`

The book/chapter/verse field uses MorphGNT's own two-digit book numbering (61 = Matthew, 87 = Revelation). The parser (`etl/sources/morphgnt.py`) maps these to OSIS IDs.

**Note:** Strong's numbers are not included in MorphGNT. LINGUISTIC edges for NT Greek require a separate Strong's-to-GNT-lemma concordance (not yet implemented). The `strong_number` field will be `null` for NT tokens until this is added.

## Greek Old Testament — LXX

**Septuagint (CATSS / Rahlfs)**
- Not automatically downloaded — CATSS requires academic registration
- Place `lxx.txt` or `lxx.xml` in `data/raw/` manually
- The parser (`etl/sources/lxx.py`) accepts both a plain-text format (`Gen 1:1 Ἐν ἀρχῇ...`) and OSIS XML
- License: Academic/public domain depending on edition

Including the LXX is what makes the cross-testament linguistic graph possible: the same Greek lemma (e.g. ἀγάπη, G26) appears in both LXX and NT, creating LINGUISTIC edges that bridge the two testaments.

If the LXX file is absent, the pipeline skips that step and prints a clear message. All other steps still run.

## English Translation — BSB

**Berean Standard Bible**
- URL: `bereanbible.com/bsb.xlsx`
- Format: Excel spreadsheet (XLSX); parsed with openpyxl
- License: CC BY-SA 4.0
- Verse reference column uses full English book names (`"Genesis 1:1"`); the parser maps these to OSIS IDs

A Strong's-aligned BSB CSV edition is also available from `Clear-Bible/OpenEnglishBible` and may be preferable in future for alignment data.

## Virtual Hebrew NT — Delitzsch

**Franz Delitzsch Hebrew New Testament**
- Repository: `openscriptures/HebrewNT` on GitHub
- Format: either plain text or OSIS XML depending on repository state
- License: Public domain (19th century translation)

Every verse loaded from this source has `is_virtual = true` and `language_code = "heb-virtual"`. This distinguishes it from OSHB Hebrew (`heb`) so callers can opt in or out of virtual texts explicitly.

## Cross-References — OpenBible

**OpenBible.info cross-reference dataset**
- URL: `a.openbible.info/bulk/cross-references.zip`
- Format: tab-separated CSV inside the zip
- License: CC BY 3.0
- ~340,000 verse pairs with a `votes` column (upvotes minus downvotes from community curation)

Votes are normalized to a weight in [0, 1] using `max(0.0, min(1.0, (votes + 5) / 55.0))`. A verse pair with 50 upvotes gets weight ≈ 1.0; a pair with 0 votes gets weight ≈ 0.09; negative-voted pairs get weight 0.

All OpenBible pairs are loaded as `CITATIONAL` edges. They include both genuine OT quotations in the NT and thematic parallels; finer classification (quotation vs. allusion) would require NLP analysis not yet implemented.

## OSIS Reference System

All verse addressing uses the **Open Scripture Information Standard (OSIS)** reference format: `BookID.Chapter.Verse` — e.g. `Gen.1.1`, `Ps.119.105`, `Rev.22.21`.

OSIS IDs for books: `Gen Exod Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr 2Chr Ezra Neh Esth Job Ps Prov Eccl Song Isa Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal Matt Mark Luke John Acts Rom 1Cor 2Cor Gal Eph Phil Col 1Thess 2Thess 1Tim 2Tim Titus Phlm Heb Jas 1Pet 2Pet 1John 2John 3John Jude Rev`
