"""
Normalize and deduplicate data from all sources before DB load.

Responsibilities:
  - Assign stable OSIS refs (Gen.1.1 format)
  - Build the canonical Book / Chapter / Verse hierarchy from known verse counts
  - Deduplicate token and verse-text rows
"""

from __future__ import annotations

from dataclasses import dataclass, field

# fmt: off
# Canonical Bible book metadata (OSIS ID, full name, abbrev, testament, genre,
# original language, order, author hint)
CANON: list[dict] = [
    {"osis_id": "Gen",    "name": "Genesis",        "abbrev": "Gen",    "testament": "OT", "genre": "Law",      "lang": "Hebrew",       "order": 1,  "author": "Moses"},
    {"osis_id": "Exod",   "name": "Exodus",         "abbrev": "Exod",   "testament": "OT", "genre": "Law",      "lang": "Hebrew",       "order": 2,  "author": "Moses"},
    {"osis_id": "Lev",    "name": "Leviticus",      "abbrev": "Lev",    "testament": "OT", "genre": "Law",      "lang": "Hebrew",       "order": 3,  "author": "Moses"},
    {"osis_id": "Num",    "name": "Numbers",        "abbrev": "Num",    "testament": "OT", "genre": "Law",      "lang": "Hebrew",       "order": 4,  "author": "Moses"},
    {"osis_id": "Deut",   "name": "Deuteronomy",    "abbrev": "Deut",   "testament": "OT", "genre": "Law",      "lang": "Hebrew",       "order": 5,  "author": "Moses"},
    {"osis_id": "Josh",   "name": "Joshua",         "abbrev": "Josh",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 6,  "author": "Joshua"},
    {"osis_id": "Judg",   "name": "Judges",         "abbrev": "Judg",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 7,  "author": "Unknown"},
    {"osis_id": "Ruth",   "name": "Ruth",           "abbrev": "Ruth",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 8,  "author": "Unknown"},
    {"osis_id": "1Sam",   "name": "1 Samuel",       "abbrev": "1Sam",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 9,  "author": "Samuel"},
    {"osis_id": "2Sam",   "name": "2 Samuel",       "abbrev": "2Sam",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 10, "author": "Samuel"},
    {"osis_id": "1Kgs",   "name": "1 Kings",        "abbrev": "1Kgs",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 11, "author": "Unknown"},
    {"osis_id": "2Kgs",   "name": "2 Kings",        "abbrev": "2Kgs",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 12, "author": "Unknown"},
    {"osis_id": "1Chr",   "name": "1 Chronicles",   "abbrev": "1Chr",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 13, "author": "Ezra"},
    {"osis_id": "2Chr",   "name": "2 Chronicles",   "abbrev": "2Chr",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 14, "author": "Ezra"},
    {"osis_id": "Ezra",   "name": "Ezra",           "abbrev": "Ezra",   "testament": "OT", "genre": "History",  "lang": "HebrewAramaic","order": 15, "author": "Ezra"},
    {"osis_id": "Neh",    "name": "Nehemiah",       "abbrev": "Neh",    "testament": "OT", "genre": "History",  "lang": "HebrewAramaic","order": 16, "author": "Nehemiah"},
    {"osis_id": "Esth",   "name": "Esther",         "abbrev": "Esth",   "testament": "OT", "genre": "History",  "lang": "Hebrew",       "order": 17, "author": "Unknown"},
    {"osis_id": "Job",    "name": "Job",            "abbrev": "Job",    "testament": "OT", "genre": "Wisdom",   "lang": "Hebrew",       "order": 18, "author": "Unknown"},
    {"osis_id": "Ps",     "name": "Psalms",         "abbrev": "Ps",     "testament": "OT", "genre": "Poetry",   "lang": "Hebrew",       "order": 19, "author": "David"},
    {"osis_id": "Prov",   "name": "Proverbs",       "abbrev": "Prov",   "testament": "OT", "genre": "Wisdom",   "lang": "Hebrew",       "order": 20, "author": "Solomon"},
    {"osis_id": "Eccl",   "name": "Ecclesiastes",   "abbrev": "Eccl",   "testament": "OT", "genre": "Wisdom",   "lang": "Hebrew",       "order": 21, "author": "Solomon"},
    {"osis_id": "Song",   "name": "Song of Songs",  "abbrev": "Song",   "testament": "OT", "genre": "Poetry",   "lang": "Hebrew",       "order": 22, "author": "Solomon"},
    {"osis_id": "Isa",    "name": "Isaiah",         "abbrev": "Isa",    "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 23, "author": "Isaiah"},
    {"osis_id": "Jer",    "name": "Jeremiah",       "abbrev": "Jer",    "testament": "OT", "genre": "Prophecy", "lang": "HebrewAramaic","order": 24, "author": "Jeremiah"},
    {"osis_id": "Lam",    "name": "Lamentations",   "abbrev": "Lam",    "testament": "OT", "genre": "Poetry",   "lang": "Hebrew",       "order": 25, "author": "Jeremiah"},
    {"osis_id": "Ezek",   "name": "Ezekiel",        "abbrev": "Ezek",   "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 26, "author": "Ezekiel"},
    {"osis_id": "Dan",    "name": "Daniel",         "abbrev": "Dan",    "testament": "OT", "genre": "Apocalyptic","lang": "HebrewAramaic","order":27, "author": "Daniel"},
    {"osis_id": "Hos",    "name": "Hosea",          "abbrev": "Hos",    "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 28, "author": "Hosea"},
    {"osis_id": "Joel",   "name": "Joel",           "abbrev": "Joel",   "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 29, "author": "Joel"},
    {"osis_id": "Amos",   "name": "Amos",           "abbrev": "Amos",   "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 30, "author": "Amos"},
    {"osis_id": "Obad",   "name": "Obadiah",        "abbrev": "Obad",   "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 31, "author": "Obadiah"},
    {"osis_id": "Jonah",  "name": "Jonah",          "abbrev": "Jonah",  "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 32, "author": "Jonah"},
    {"osis_id": "Mic",    "name": "Micah",          "abbrev": "Mic",    "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 33, "author": "Micah"},
    {"osis_id": "Nah",    "name": "Nahum",          "abbrev": "Nah",    "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 34, "author": "Nahum"},
    {"osis_id": "Hab",    "name": "Habakkuk",       "abbrev": "Hab",    "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 35, "author": "Habakkuk"},
    {"osis_id": "Zeph",   "name": "Zephaniah",      "abbrev": "Zeph",   "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 36, "author": "Zephaniah"},
    {"osis_id": "Hag",    "name": "Haggai",         "abbrev": "Hag",    "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 37, "author": "Haggai"},
    {"osis_id": "Zech",   "name": "Zechariah",      "abbrev": "Zech",   "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 38, "author": "Zechariah"},
    {"osis_id": "Mal",    "name": "Malachi",        "abbrev": "Mal",    "testament": "OT", "genre": "Prophecy", "lang": "Hebrew",       "order": 39, "author": "Malachi"},
    {"osis_id": "Matt",   "name": "Matthew",        "abbrev": "Matt",   "testament": "NT", "genre": "Gospel",   "lang": "Greek",        "order": 40, "author": "Matthew"},
    {"osis_id": "Mark",   "name": "Mark",           "abbrev": "Mark",   "testament": "NT", "genre": "Gospel",   "lang": "Greek",        "order": 41, "author": "Mark"},
    {"osis_id": "Luke",   "name": "Luke",           "abbrev": "Luke",   "testament": "NT", "genre": "Gospel",   "lang": "Greek",        "order": 42, "author": "Luke"},
    {"osis_id": "John",   "name": "John",           "abbrev": "John",   "testament": "NT", "genre": "Gospel",   "lang": "Greek",        "order": 43, "author": "John"},
    {"osis_id": "Acts",   "name": "Acts",           "abbrev": "Acts",   "testament": "NT", "genre": "Acts",     "lang": "Greek",        "order": 44, "author": "Luke"},
    {"osis_id": "Rom",    "name": "Romans",         "abbrev": "Rom",    "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 45, "author": "Paul"},
    {"osis_id": "1Cor",   "name": "1 Corinthians",  "abbrev": "1Cor",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 46, "author": "Paul"},
    {"osis_id": "2Cor",   "name": "2 Corinthians",  "abbrev": "2Cor",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 47, "author": "Paul"},
    {"osis_id": "Gal",    "name": "Galatians",      "abbrev": "Gal",    "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 48, "author": "Paul"},
    {"osis_id": "Eph",    "name": "Ephesians",      "abbrev": "Eph",    "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 49, "author": "Paul"},
    {"osis_id": "Phil",   "name": "Philippians",    "abbrev": "Phil",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 50, "author": "Paul"},
    {"osis_id": "Col",    "name": "Colossians",     "abbrev": "Col",    "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 51, "author": "Paul"},
    {"osis_id": "1Thess", "name": "1 Thessalonians","abbrev": "1Thess", "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 52, "author": "Paul"},
    {"osis_id": "2Thess", "name": "2 Thessalonians","abbrev": "2Thess", "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 53, "author": "Paul"},
    {"osis_id": "1Tim",   "name": "1 Timothy",      "abbrev": "1Tim",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 54, "author": "Paul"},
    {"osis_id": "2Tim",   "name": "2 Timothy",      "abbrev": "2Tim",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 55, "author": "Paul"},
    {"osis_id": "Titus",  "name": "Titus",          "abbrev": "Titus",  "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 56, "author": "Paul"},
    {"osis_id": "Phlm",   "name": "Philemon",       "abbrev": "Phlm",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 57, "author": "Paul"},
    {"osis_id": "Heb",    "name": "Hebrews",        "abbrev": "Heb",    "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 58, "author": "Unknown"},
    {"osis_id": "Jas",    "name": "James",          "abbrev": "Jas",    "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 59, "author": "James"},
    {"osis_id": "1Pet",   "name": "1 Peter",        "abbrev": "1Pet",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 60, "author": "Peter"},
    {"osis_id": "2Pet",   "name": "2 Peter",        "abbrev": "2Pet",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 61, "author": "Peter"},
    {"osis_id": "1John",  "name": "1 John",         "abbrev": "1John",  "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 62, "author": "John"},
    {"osis_id": "2John",  "name": "2 John",         "abbrev": "2John",  "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 63, "author": "John"},
    {"osis_id": "3John",  "name": "3 John",         "abbrev": "3John",  "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 64, "author": "John"},
    {"osis_id": "Jude",   "name": "Jude",           "abbrev": "Jude",   "testament": "NT", "genre": "Epistle",  "lang": "Greek",        "order": 65, "author": "Jude"},
    {"osis_id": "Rev",    "name": "Revelation",     "abbrev": "Rev",    "testament": "NT", "genre": "Apocalyptic","lang": "Greek",      "order": 66, "author": "John"},
]
# fmt: on
