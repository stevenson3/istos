"""
Parse a plain-text LXX source (CATSS-style or similar).

The CATSS LXX format varies; this parser handles the most common plain-text
layout where each line is:
    <book_abbrev> <chapter>:<verse> <Greek text>

For structured OSIS XML, adapt _parse_xml below.

language_code = "grc" (same code as NT Greek)
translation_name = "LXX"

Input:  data/raw/lxx.txt  (or similar — user must place the file manually
        as the CATSS dataset requires academic registration)
"""

from pathlib import Path
from typing import Generator

RAW = Path(__file__).parent.parent.parent.parent / "data" / "raw"

# Acceptable filenames for an LXX source file
_CANDIDATES = ["lxx.txt", "lxx.xml", "catss_lxx.txt"]


# CATSS / Rahlfs abbreviation → OSIS ID (partial list; extend as needed)
_LXX_TO_OSIS: dict[str, str] = {
    "Gen": "Gen", "Ex": "Exod", "Lev": "Lev", "Num": "Num", "Deut": "Deut",
    "Josh": "Josh", "JoshA": "Josh", "Judg": "Judg", "JudgB": "Judg",
    "Ruth": "Ruth", "1Sam": "1Sam", "1Kgdms": "1Sam", "2Sam": "2Sam",
    "2Kgdms": "2Sam", "1Kgs": "1Kgs", "3Kgdms": "1Kgs", "2Kgs": "2Kgs",
    "4Kgdms": "2Kgs", "1Chr": "1Chr", "1Chron": "1Chr", "2Chr": "2Chr",
    "2Chron": "2Chr", "Ezra": "Ezra", "Neh": "Neh", "Esth": "Esth",
    "Job": "Job", "Ps": "Ps", "Prov": "Prov", "Eccl": "Eccl",
    "Cant": "Song", "Song": "Song", "Isa": "Isa", "Jer": "Jer",
    "Lam": "Lam", "Ezek": "Ezek", "Dan": "Dan", "Hos": "Hos",
    "Joel": "Joel", "Amos": "Amos", "Obad": "Obad", "Jonah": "Jonah",
    "Mic": "Mic", "Nah": "Nah", "Hab": "Hab", "Zeph": "Zeph",
    "Hag": "Hag", "Zech": "Zech", "Mal": "Mal",
}

SOURCE_URL = "https://ccat.sas.upenn.edu/gopher/text/religion/biblical/lxxmorph/"


def _find_lxx_file() -> Path | None:
    for name in _CANDIDATES:
        p = RAW / name
        if p.exists():
            return p
    return None


def iter_verse_texts() -> Generator[dict, None, None]:
    lxx_file = _find_lxx_file()
    if lxx_file is None:
        raise FileNotFoundError(
            f"LXX source file not found in {RAW}. "
            f"Expected one of: {_CANDIDATES}. "
            "Download from CATSS (requires registration) and place in data/raw/."
        )

    if lxx_file.suffix == ".xml":
        yield from _parse_xml(lxx_file)
    else:
        yield from _parse_txt(lxx_file)


def _parse_txt(path: Path) -> Generator[dict, None, None]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
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

            osis_book = _LXX_TO_OSIS.get(book_str, book_str)
            yield {
                "osis_ref": f"{osis_book}.{chapter}.{verse}",
                "language_code": "grc",
                "script_direction": "ltr",
                "text": text.strip(),
                "translation_name": "LXX",
                "is_virtual": False,
                "source_url": SOURCE_URL,
            }


def _parse_xml(path: Path) -> Generator[dict, None, None]:
    from lxml import etree

    with path.open("rb") as fh:
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
            "language_code": "grc",
            "script_direction": "ltr",
            "text": text,
            "translation_name": "LXX",
            "is_virtual": False,
            "source_url": SOURCE_URL,
        }
