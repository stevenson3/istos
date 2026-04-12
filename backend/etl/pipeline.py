"""
Orchestrate the full Istos ETL pipeline.

Usage:
    cd backend
    python -m etl.pipeline                    # full run
    python -m etl.pipeline download           # step 1 only
    python -m etl.pipeline canon              # seed book/chapter/verse scaffold
    python -m etl.pipeline texts              # load verse texts (BSB + Delitzsch)
    python -m etl.pipeline tokens             # load morphological tokens (OSHB + MorphGNT)
    python -m etl.pipeline edges              # build all edge types
    python -m etl.pipeline edges:citational   # one edge type
    python -m etl.pipeline edges:linguistic
    python -m etl.pipeline edges:authorial
"""

import sys
import time

from app.database import SessionLocal, ensure_extensions
from etl import download as dl
from etl import load


def step_download():
    print("=== Step 1: Download raw sources ===")
    dl.download()


def step_canon(db):
    print("=== Step 2: Seed canon scaffold ===")
    return load.seed_canon(db)


def step_texts(db, osis_map):
    print("=== Step 3: Load verse texts ===")

    from etl.sources import bsb, delitzsch

    print("  BSB (English)...")
    bsb_rows = list(bsb.iter_verse_texts())
    n = load.load_verse_texts(db, bsb_rows, osis_map)
    print(f"  {n} BSB verses loaded")

    print("  Delitzsch (virtual Hebrew NT)...")
    try:
        del_rows = list(delitzsch.iter_verse_texts())
        n = load.load_verse_texts(db, del_rows, osis_map)
        print(f"  {n} Delitzsch verses loaded")
    except FileNotFoundError as e:
        print(f"  [skip] {e}")

    print("  LXX (Greek OT)...")
    try:
        from etl.sources import lxx
        lxx_rows = list(lxx.iter_verse_texts())
        n = load.load_verse_texts(db, lxx_rows, osis_map)
        print(f"  {n} LXX verses loaded")
    except FileNotFoundError as e:
        print(f"  [skip] {e}")


def step_tokens(db, osis_map):
    print("=== Step 4: Load morphological tokens ===")

    print("  OSHB (Hebrew OT)...")
    try:
        from etl.sources.oshb import iter_all_tokens
        oshb_rows = list(iter_all_tokens())
        n = load.load_verse_tokens(db, oshb_rows, osis_map)
        print(f"  {n} OSHB tokens loaded")
    except FileNotFoundError as e:
        print(f"  [skip] {e}")

    print("  MorphGNT (Greek NT)...")
    try:
        from etl.sources.morphgnt import iter_tokens
        gnt_rows = list(iter_tokens())
        n = load.load_verse_tokens(db, gnt_rows, osis_map)
        print(f"  {n} MorphGNT tokens loaded")
    except FileNotFoundError as e:
        print(f"  [skip] {e}")


def step_edges(db, which: str = "all"):
    print(f"=== Step 5: Build edges ({which}) ===")

    if which in ("all", "citational"):
        try:
            from etl.edges.citational import load_citational_edges
            load_citational_edges(db)
        except FileNotFoundError as e:
            print(f"  [skip citational] {e}")

    if which in ("all", "linguistic"):
        from etl.edges.linguistic import load_linguistic_edges
        load_linguistic_edges(db)

    if which in ("all", "authorial"):
        from etl.edges.authorial import load_authorial_edges
        load_authorial_edges(db)


def run(steps: list[str]):
    t0 = time.time()
    ensure_extensions()

    with SessionLocal() as db:
        if "download" in steps:
            step_download()

        osis_map: dict[str, int] = {}

        if "canon" in steps:
            osis_map = step_canon(db)
        elif any(s in steps for s in ("texts", "tokens", "edges", "all")):
            # Load existing map from DB
            from sqlalchemy import select
            from app.models.verse import Verse
            osis_map = {r.osis_ref: r.id for r in db.execute(select(Verse.osis_ref, Verse.id)).all()}
            print(f"Loaded {len(osis_map)} existing osis_refs from DB")

        if "texts" in steps:
            step_texts(db, osis_map)

        if "tokens" in steps:
            step_tokens(db, osis_map)

        for step in steps:
            if step.startswith("edges"):
                which = step.split(":")[1] if ":" in step else "all"
                step_edges(db, which)
                break

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


def main():
    args = sys.argv[1:]
    if not args:
        steps = ["download", "canon", "texts", "tokens", "edges"]
    else:
        steps = args

    # Expand "all" shorthand
    if steps == ["all"]:
        steps = ["download", "canon", "texts", "tokens", "edges"]

    run(steps)


if __name__ == "__main__":
    main()
