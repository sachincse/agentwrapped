"""Tests for stats aggregation, personality, and card rendering."""
from __future__ import annotations

import glob
import os

import pytest
from rich.console import Console

from agentwrapped.card import human_int, render_png
from agentwrapped.stats import build_wrapped
from agentwrapped.terminal import render_terminal

FIXDIR = os.path.join(os.path.dirname(__file__), "fixtures")
PATHS = sorted(glob.glob(os.path.join(FIXDIR, "*.jsonl")))


@pytest.fixture()
def wrapped():
    return build_wrapped(paths=PATHS)


def test_aggregation(wrapped):
    assert wrapped.n_sessions == 2
    assert wrapped.n_tool_calls == 6           # 4 in a + 2 in b
    assert wrapped.tool_counts["Edit"] == 3
    assert wrapped.tool_counts["Bash"] == 2
    assert wrapped.tool_counts["Read"] == 1
    assert wrapped.total_output_tokens == 4 * 50 + 2 * 20


def test_personality_is_refactorer(wrapped):
    # 3 of 6 calls are Edit -> 50% edit cluster -> The Refactorer
    assert wrapped.personality == "The Refactorer"
    assert wrapped.personality_tag == "edit"
    assert wrapped.personality_pct == 50


def test_busiest_and_longest(wrapped):
    assert wrapped.busiest_day == "2026-03-01"   # session a has 4 calls that day
    assert wrapped.busiest_day_calls == 4
    assert wrapped.longest_session_calls == 4
    assert wrapped.longest_session_title == "Refactor the widget module"


def test_year_filter():
    w2026 = build_wrapped(paths=PATHS, year=2026)
    assert w2026.n_sessions == 2
    w2025 = build_wrapped(paths=PATHS, year=2025)
    assert w2025.n_sessions == 0


def test_cost_positive(wrapped):
    assert wrapped.total_cost_usd > 0


def test_human_int():
    assert human_int(950) == "950"
    assert human_int(1500) == "1.5k"
    assert human_int(2_300_000) == "2.3M"


def test_render_png_writes_valid_png(wrapped, tmp_path):
    out = tmp_path / "card.png"
    render_png(wrapped, str(out))
    assert out.exists()
    with open(out, "rb") as fh:
        assert fh.read(8) == b"\x89PNG\r\n\x1a\n"   # PNG signature


def test_render_terminal_runs(wrapped):
    console = Console(record=True, width=80, file=open(os.devnull, "w", encoding="utf-8"))
    render_terminal(wrapped, console)
    text = console.export_text()
    assert "WRAPPED" in text
    assert "Refactorer" in text


def test_empty_wrapped(tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    w = build_wrapped(paths=[str(empty)])
    assert w.n_sessions == 1
    assert w.n_tool_calls == 0
    assert w.personality == "The Generalist"
