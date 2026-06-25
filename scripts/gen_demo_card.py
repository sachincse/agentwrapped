"""Regenerate docs/card.png from the test fixtures (never real session logs),
so the public repo's hero image leaks nothing.

    python scripts/gen_demo_card.py
"""
from __future__ import annotations

import glob
import os

from agentwrapped.card import render_png
from agentwrapped.stats import build_wrapped

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXDIR = os.path.join(ROOT, "tests", "fixtures")
DOCS = os.path.join(ROOT, "docs")


def main() -> None:
    os.makedirs(DOCS, exist_ok=True)
    paths = sorted(glob.glob(os.path.join(FIXDIR, "*.jsonl")))
    w = build_wrapped(paths=paths, year=2026)
    out = render_png(w, os.path.join(DOCS, "card.png"))
    print("wrote", out)


if __name__ == "__main__":
    main()
