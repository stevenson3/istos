"""
Parse the OpenBible.info cross-reference CSV.

File format (tab-separated):
    from_verse  to_verse  votes

Example:
    Gen.1.1  John.1.1  42
    Gen.1.26  Ps.8.5   17

We emit Edge dicts with edge_type=CITATIONAL (all openbible refs treated as
citational; finer classification — actual quotation vs. allusion — requires
additional NLP and is deferred).

Input:  data/raw/cross-references.zip  (single CSV inside)
"""

import csv
import io
import zipfile
from pathlib import Path
from typing import Generator

RAW = Path(__file__).parent.parent.parent.parent / "data" / "raw"
XREF_ZIP = RAW / "cross-references.zip"


def iter_edges() -> Generator[dict, None, None]:
    if not XREF_ZIP.exists():
        raise FileNotFoundError(f"OpenBible zip not found: {XREF_ZIP}. Run etl.download first.")

    with zipfile.ZipFile(XREF_ZIP) as zf:
        csv_names = [n for n in zf.namelist() if n.endswith(".csv") or n.endswith(".txt")]
        if not csv_names:
            raise ValueError(f"No CSV found inside {XREF_ZIP}")
        csv_name = csv_names[0]

        with zf.open(csv_name) as fh:
            reader = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter="\t")
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                if len(row) < 2:
                    continue

                from_ref, to_ref = row[0].strip(), row[1].strip()
                votes = int(row[2]) if len(row) > 2 and row[2].strip().lstrip("-").isdigit() else 0
                # Normalize confidence: votes can be negative (downvoted)
                weight = max(0.0, min(1.0, (votes + 5) / 55.0))

                yield {
                    "source_osis_ref": from_ref,
                    "target_osis_ref": to_ref,
                    "edge_type": "CITATIONAL",
                    "weight": weight,
                    "is_directed": True,
                    "metadata": {"source": "openbible", "votes": votes},
                }
