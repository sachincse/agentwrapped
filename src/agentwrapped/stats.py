"""Aggregate a pile of agent sessions into the handful of stats that make a
shareable "Wrapped" card. Reuses trace-lens's parser so there is exactly one
JSONL reader to maintain.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

from trace_lens import Session, analyze, parse_session
from trace_lens.discover import discover_sessions


# (label, emoji-ish tag, predicate over tool-share) — first match wins.
_PERSONALITIES = [
    ("The Refactorer", "edit", {"Edit", "MultiEdit"}),
    ("The Builder", "build", {"Write", "NotebookEdit"}),
    ("The Operator", "shell", {"Bash"}),
    ("The Explorer", "search", {"Read", "Grep", "Glob", "NotebookRead"}),
    ("The Researcher", "web", {"WebSearch", "WebFetch"}),
    ("The Planner", "plan", {"TodoWrite", "Task", "Agent"}),
]


@dataclass
class Wrapped:
    n_sessions: int = 0
    n_tool_calls: int = 0
    total_output_tokens: int = 0
    total_input_tokens: int = 0
    total_cost_usd: float = 0.0
    tool_counts: Counter = field(default_factory=Counter)
    model_counts: Counter = field(default_factory=Counter)
    by_day_calls: dict[str, int] = field(default_factory=dict)
    busiest_day: Optional[str] = None
    busiest_day_calls: int = 0
    longest_session_calls: int = 0
    longest_session_title: str = ""
    personality: str = "The Generalist"
    personality_tag: str = "balanced"
    personality_pct: int = 0
    year: Optional[int] = None

    @property
    def top_tools(self) -> list[tuple[str, int]]:
        return self.tool_counts.most_common(5)

    @property
    def top_model(self) -> Optional[str]:
        return self.model_counts.most_common(1)[0][0] if self.model_counts else None

    def tool_share(self, names: set[str]) -> float:
        total = sum(self.tool_counts.values())
        if not total:
            return 0.0
        return sum(self.tool_counts.get(n, 0) for n in names) / total


def _classify(w: Wrapped) -> None:
    best_label, best_tag, best_pct = "The Generalist", "balanced", 0
    for label, tag, names in _PERSONALITIES:
        pct = int(round(w.tool_share(names) * 100))
        if pct > best_pct:
            best_label, best_tag, best_pct = label, tag, pct
    # only override the generalist if one cluster is clearly dominant
    if best_pct >= 25:
        w.personality, w.personality_tag, w.personality_pct = best_label, best_tag, best_pct
    else:
        w.personality, w.personality_tag, w.personality_pct = "The Generalist", "balanced", best_pct


def _accumulate(w: Wrapped, session: Session) -> None:
    report = analyze(session)
    w.n_sessions += 1
    w.n_tool_calls += session.n_tool_calls
    w.total_output_tokens += session.output_tokens
    w.total_input_tokens += session.total_input_tokens
    w.total_cost_usd += report.cost_usd
    w.model_counts.update(session.models)
    for tc in session.tool_calls:
        w.tool_counts[tc.name] += 1
        if tc.ts is not None:
            day = tc.ts.date().isoformat()
            w.by_day_calls[day] = w.by_day_calls.get(day, 0) + 1
    if session.n_tool_calls > w.longest_session_calls:
        w.longest_session_calls = session.n_tool_calls
        w.longest_session_title = session.title or session.session_id[:8]


def build_wrapped(
    paths: Optional[list[str]] = None,
    cwd: Optional[str] = None,
    root: Optional[str] = None,
    all_projects: bool = True,
    year: Optional[int] = None,
) -> Wrapped:
    """Build a :class:`Wrapped` from session paths (or auto-discovered ones)."""
    if paths is None:
        paths = discover_sessions(cwd=cwd, root=root, all_projects=all_projects)

    w = Wrapped(year=year)
    for path in paths:
        try:
            session = parse_session(path)
        except (OSError, ValueError):
            continue
        if year is not None and session.started_at and session.started_at.year != year:
            continue
        _accumulate(w, session)

    if w.by_day_calls:
        day, calls = max(w.by_day_calls.items(), key=lambda kv: kv[1])
        w.busiest_day, w.busiest_day_calls = day, calls
    _classify(w)
    return w
