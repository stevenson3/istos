"""
Parse the Berean Standard Bible (BSB) XLSX / CSV file.

The BSB file from bereanbible.com is a spreadsheet with columns including:
  Verse, BSB, Footnotes, ...

We emit VerseText dicts with language_code="eng", translation_name="BSB".

Input:  data/raw/bsb.xlsx
"""

from pathlib import Path
from typing import Generator

RAW = Path(__file__).parent.parent.parent.parent / "data" / "raw"
BSB_FILE = RAW / "bsb.xlsx"

# OSIS book ID lookup by BSB book name (abbreviated)
_BSB_TO_OSIS: dict[str, str] = {
    "Genesis": "Gen", "Exodus": "Exod", "Leviticus": "Lev", "Numbers": "Num",
    "Deuteronomy": "Deut", "Joshua": "Josh", "Judges": "Judg", "Ruth": "Ruth",
    "1 Samuel": "1Sam", "2 Samuel": "2Sam", "1 Kings": "1Kgs", "2 Kings": "2Kgs",
    "1 Chronicles": "1Chr", "2 Chronicles": "2Chr", "Ezra": "Ezra", "Nehemiah": "Neh",
    "Esther": "Esth", "Job": "Job", "Psalms": "Ps", "Proverbs": "Prov",
    "Ecclesiastes": "Eccl", "Song of Songs": "Song", "Isaiah": "Isa",
    "Jeremiah": "Jer", "Lamentations": "Lam", "Ezekiel": "Ezek", "Daniel": "Dan",
    "Hosea": "Hos", "Joel": "Joel", "Amos": "Amos", "Obadiah": "Obad",
    "Jonah": "Jonah", "Micah": "Mic", "Nahum": "Nah", "Habakkuk": "Hab",
    "Zephaniah": "Zeph", "Haggai": "Hag", "Zechariah": "Zech", "Malachi": "Mal",
    "Matthew": "Matt", "Mark": "Mark", "Luke": "Luke", "John": "John",
    "Acts": "Acts", "Romans": "Rom", "1 Corinthians": "1Cor",
    "2 Corinthians": "2Cor", "Galatians": "Gal", "Ephesians": "Eph",
    "Philippians": "Phil", "Colossians": "Col", "1 Thessalonians": "1Thess",
    "2 Thessalonians": "2Thess", "1 Timothy": "1Tim", "2 Timothy": "2Tim",
    "Titus": "Titus", "Philemon": "Phlm", "Hebrews": "Heb", "James": "Jas",
    "1 Peter": "1Pet", "2 Peter": "2Pet", "1 John": "1John",
    "2 John": "2John", "3 John": "3John", "Jude": "Jude", "Revelation": "Rev",
}

SOURCE_URL = "https://bereanbible.com/bsb.xlsx"


def iter_verse_texts() -> Generator[dict, None, None]:
    """
    Yield verse-text dicts from BSB XLSX.

    The BSB xlsx has varying column layouts across editions.  We attempt to
    handle the most common format; column indices may need adjustment if the
    upstream file changes.
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("Install openpyxl: pip install openpyxl")

    if not BSB_FILE.exists():
        raise FileNotFoundError(f"BSB file not found: {BSB_FILE}. Run etl.download first.")

    wb = openpyxl.load_workbook(BSB_FILE, read_only=True, data_only=True)
    ws = wb.active

    rows = ws.iter_rows(values_only=True)
    header = next(rows, None)  # skip header row if present

    for row in rows:
        if not row or not row[0]:
            continue

        # Typical BSB column layout: [Verse, BSB, Footnotes, ...]
        # "Verse" looks like "Genesis 1:1" or "Gen 1:1"
        verse_ref = str(row[0]).strip()
        text = str(row[1]).strip() if row[1] else ""

        if not verse_ref or not text:
            continue

        osis_ref = _bsb_ref_to_osis(verse_ref)
        if not osis_ref:
            continue

        yield {
            "osis_ref": osis_ref,
            "language_code": "eng",
            "script_direction": "ltr",
            "text": text,
            "translation_name": "BSB",
            "is_virtual": False,
            "source_url": SOURCE_URL,
        }


def _bsb_ref_to_osis(ref: str) -> str | None:
    """Convert 'Genesis 1:1' or 'Gen 1:1' to 'Gen.1.1'."""
    try:
        parts = ref.rsplit(" ", 1)
        book_name = parts[0].strip()
        ch_v = parts[1].split(":")
        chapter = int(ch_v[0])
        verse = int(ch_v[1])
    except (IndexError, ValueError):
        return None

    osis_book = _BSB_TO_OSIS.get(book_name)
    if not osis_book:
        # Try short name
        for long, short in _BSB_TO_OSIS.items():
            if book_name == short:
                osis_book = short
                break
    if not osis_book:
        return None
    return f"{osis_book}.{chapter}.{verse}"
