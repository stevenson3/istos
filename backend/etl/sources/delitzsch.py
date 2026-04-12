"""
Parse the Franz Delitzsch Hebrew NT (public domain).

The HebrewNT GitHub repository contains plain-text or XML files.
We emit VerseText dicts with:
  language_code="heb-virtual"
  is_virtual=True
  translation_name="Delitzsch"

Input:  data/raw/HebrewNT-master.zip
"""

import zipfile
from pathlib import Path
from typing import Generator

RAW = Path(__file__).parent.parent.parent.parent / "data" / "raw"
HNT_ZIP = RAW / "HebrewNT-master.zip"

SOURCE_URL = "https://github.com/openscriptures/HebrewNT"

# MorphGNT NT book → OSIS mapping (re-used here)
NT_BOOKS = [
    "Matt", "Mark", "Luke", "John", "Acts",
    "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col",
    "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm",
    "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
]


def iter_verse_texts() -> Generator[dict, None, None]:
    """
    Yield verse-text dicts from the Delitzsch HNT zip.

    The exact file layout inside the zip depends on the repository structure.
    This parser handles the plain-text layout where each line is:
        <Book> <chapter>:<verse>  <Hebrew text>
    or OSIS XML files per book (similar to OSHB).
    """
    if not HNT_ZIP.exists():
        raise FileNotFoundError(f"Delitzsch HNT zip not found: {HNT_ZIP}. Run etl.download first.")

    with zipfile.ZipFile(HNT_ZIP) as zf:
        # Try text files first
        txt_files = [n for n in zf.namelist() if n.endswith(".txt") and "HebrewNT" in n]
        xml_files = [n for n in zf.namelist() if n.endswith(".xml") and "HebrewNT" in n]

        if txt_files:
            yield from _parse_txt(zf, txt_files)
        elif xml_files:
            yield from _parse_xml(zf, xml_files)


def _parse_txt(zf: zipfile.ZipFile, names: list[str]) -> Generator[dict, None, None]:
    for name in sorted(names):
        with zf.open(name) as fh:
            for line in fh:
                line = line.decode("utf-8").strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 2)
                if len(parts) < 3:
                    continue
                book_str, cv, text = parts
                try:
                    ch, v = cv.split(":")
                    chapter, verse = int(ch), int(v)
                except ValueError:
                    continue

                osis_ref = f"{book_str}.{chapter}.{verse}"
                yield {
                    "osis_ref": osis_ref,
                    "language_code": "heb-virtual",
                    "script_direction": "rtl",
                    "text": text.strip(),
                    "translation_name": "Delitzsch",
                    "is_virtual": True,
                    "source_url": SOURCE_URL,
                }


def _parse_xml(zf: zipfile.ZipFile, names: list[str]) -> Generator[dict, None, None]:
    from lxml import etree

    for name in sorted(names):
        with zf.open(name) as fh:
            root = etree.fromstring(fh.read())
        for verse_el in root.iter("{*}verse"):
            osis_id = verse_el.get("osisID")
            if not osis_id:
                continue
            text = "".join(verse_el.itertext()).strip()
            if not text:
                continue
            yield {
                "osis_ref": osis_id,
                "language_code": "heb-virtual",
                "script_direction": "rtl",
                "text": text,
                "translation_name": "Delitzsch",
                "is_virtual": True,
                "source_url": SOURCE_URL,
            }
