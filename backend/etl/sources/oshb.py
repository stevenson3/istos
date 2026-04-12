"""
Parse the Open Scriptures Hebrew Bible (OSHB) OSIS XML files.

Input:  data/raw/morphhb-master.zip  (extracted on the fly)
Output: list of dicts ready for bulk insert into verse_token table.

Each OSHB word element looks like:
  <w lemma="strong:H07225 lemma.oshb:..." morph="oshb:HR/Ncfsa">בְּרֵאשִׁ֖ית</w>
"""

import io
import re
import zipfile
from pathlib import Path
from typing import Generator

from lxml import etree

RAW = Path(__file__).parent.parent.parent.parent / "data" / "raw"
OSHB_ZIP = RAW / "morphhb-master.zip"

OSIS_NS = "http://www.bibletimeimes.org/2011/OSIS"
NS = {"osis": "http://www.bibletexts.org/2011/OSIS"}

# Canonical OSIS book IDs for the Hebrew Bible (ordering matches MT)
OT_BOOKS_ORDER = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth",
    "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh",
    "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer",
    "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah",
    "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
]

STRONG_RE = re.compile(r"strong:(H\d+[a-z]?)")


def _strong(lemma_attr: str) -> str | None:
    m = STRONG_RE.search(lemma_attr or "")
    return m.group(1) if m else None


def iter_tokens(book_osis_id: str, xml_bytes: bytes) -> Generator[dict, None, None]:
    """Yield one token dict per word in the OSHB XML for a single book."""
    root = etree.fromstring(xml_bytes)
    # OSHB uses a flat namespace; use localname matching to be safe
    position_counter: dict[str, int] = {}  # osis_ref -> position

    for verse_el in root.iter("{*}verse"):
        osis_ref = verse_el.get("osisID")
        if not osis_ref:
            continue

        pos = 0
        for w in verse_el.iter("{*}w"):
            surface = (w.text or "").strip()
            if not surface:
                continue
            lemma_attr = w.get("lemma", "")
            morph_attr = w.get("morph", "")
            strong = _strong(lemma_attr)
            # Aramaic marker in OSHB morph codes starts with 'A'
            lang = "arc" if morph_attr.startswith("oshb:A") else "heb"

            yield {
                "osis_ref": osis_ref,
                "language_code": lang,
                "position": pos,
                "surface_form": surface,
                "lemma": lemma_attr,
                "strong_number": strong,
                "morph_code": morph_attr,
                "part_of_speech": morph_attr.split("/")[0].replace("oshb:", "") if "/" in morph_attr else None,
                "gloss": None,  # glosses loaded separately from Strong's JSON
            }
            pos += 1


def iter_all_tokens() -> Generator[dict, None, None]:
    """Iterate tokens from all OSHB book XML files inside the zip."""
    if not OSHB_ZIP.exists():
        raise FileNotFoundError(f"OSHB zip not found: {OSHB_ZIP}. Run etl.download first.")

    with zipfile.ZipFile(OSHB_ZIP) as zf:
        xml_names = [n for n in zf.namelist() if n.endswith(".xml") and "/wlc/" in n]
        for name in sorted(xml_names):
            book_id = Path(name).stem  # e.g. "Gen"
            if book_id not in OT_BOOKS_ORDER:
                continue
            with zf.open(name) as fh:
                xml_bytes = fh.read()
            yield from iter_tokens(book_id, xml_bytes)
