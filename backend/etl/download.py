"""
Download all raw source files from GitHub releases and eBible.org.

Usage:
    python -m etl.download          # download everything
    python -m etl.download oshb     # download one source
"""

import hashlib
import sys
from pathlib import Path

import httpx
from tqdm import tqdm

RAW = Path(__file__).parent.parent.parent / "data" / "raw"

# (name, url, dest_filename)
SOURCES: list[tuple[str, str, str]] = [
    (
        "oshb",
        "https://github.com/openscriptures/morphhb/archive/refs/heads/master.zip",
        "morphhb-master.zip",
    ),
    (
        "morphgnt",
        "https://github.com/morphgnt/sblgnt/archive/refs/heads/master.zip",
        "sblgnt-master.zip",
    ),
    (
        "bsb",
        "https://bereanbible.com/bsb.xlsx",
        "bsb.xlsx",
    ),
    (
        "openbible",
        "https://a.openbible.info/bulk/cross-references.zip",
        "cross-references.zip",
    ),
    (
        "delitzsch",
        "https://github.com/openscriptures/HebrewNT/archive/refs/heads/master.zip",
        "HebrewNT-master.zip",
    ),
]


def _download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"  [skip] {dest.name} already present")
        return

    print(f"  -> {url}")
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest.name, leave=False
        ) as bar:
            for chunk in r.iter_bytes(chunk_size=65536):
                fh.write(chunk)
                bar.update(len(chunk))


def download(names: list[str] | None = None) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url, filename in SOURCES:
        if names and name not in names:
            continue
        print(f"[{name}]")
        _download(url, RAW / filename)


if __name__ == "__main__":
    targets = sys.argv[1:] or None
    download(targets)
