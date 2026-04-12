"""
Parse MorphGNT (SBLGNT) TSV files.

Column layout (tab-separated, no header):
  book/chapter/verse  word-number  part-of-speech  parsing-code  text  word  normalized  lemma

Input:  data/raw/sblgnt-master.zip
Output: token dicts for verse_token table (language_code="grc")

Strong's numbers are NOT in MorphGNT natively. We attach them via a
separate Strong's concordance JSON file when available; otherwise strong_number=None.
"""

import csv
import io
import zipfile
from pathlib import Path
from typing import Generator

RAW = Path(__file__).parent.parent.parent.parent / "data" / "raw"
MORPHGNT_ZIP = RAW / "sblgnt-master.zip"

# MorphGNT uses OSIS-like book codes in the filename
NT_BOOK_MAP = {
    "61": "Matt", "62": "Mark", "63": "Luke", "64": "John", "65": "Acts",
    "66": "Rom", "67": "1Cor", "68": "2Cor", "69": "Gal", "70": "Eph",
    "71": "Phil", "72": "Col", "73": "1Thess", "74": "2Thess",
    "75": "1Tim", "76": "2Tim", "77": "Titus", "78": "Phlm",
    "79": "Heb", "80": "Jas", "81": "1Pet", "82": "2Pet",
    "83": "1John", "84": "2John", "85": "3John", "86": "Jude", "87": "Rev",
}


def _osis_ref(bcv: str) -> str:
    """Convert MorphGNT '61001001' → 'Matt.1.1'."""
    book_num = bcv[:2]
    chapter = int(bcv[2:5])
    verse = int(bcv[5:8])
    book_osis = NT_BOOK_MAP.get(book_num, f"Book{book_num}")
    return f"{book_osis}.{chapter}.{verse}"


def iter_tokens() -> Generator[dict, None, None]:
    if not MORPHGNT_ZIP.exists():
        raise FileNotFoundError(f"MorphGNT zip not found: {MORPHGNT_ZIP}. Run etl.download first.")

    with zipfile.ZipFile(MORPHGNT_ZIP) as zf:
        tsv_files = sorted(n for n in zf.namelist() if n.endswith(".txt") and "sblgnt-master" in n)

        for tsv_name in tsv_files:
            with zf.open(tsv_name) as fh:
                reader = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter=" ")
                current_ref = None
                pos = 0
                for row in reader:
                    if len(row) < 8:
                        continue
                    bcv, _, pos_code, parse_code, text_with_punct, word_form, normalized, lemma = row[:8]
                    osis_ref = _osis_ref(bcv)
                    if osis_ref != current_ref:
                        current_ref = osis_ref
                        pos = 0

                    yield {
                        "osis_ref": osis_ref,
                        "language_code": "grc",
                        "position": pos,
                        "surface_form": word_form,
                        "lemma": lemma,
                        "strong_number": None,  # enriched later via Strong's concordance
                        "morph_code": parse_code,
                        "part_of_speech": pos_code,
                        "gloss": None,
                    }
                    pos += 1
