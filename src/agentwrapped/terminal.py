"""Render a :class:`Wrapped` to the terminal with Rich (no image needed)."""
from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .card import human_int
from .stats import Wrapped


def render_terminal(w: Wrapped, console: Console) -> None:
    year = str(w.year) if w.year else "all-time"

    title = Text(f"You are {w.personality}", style="bold white", justify="center")
    sub = (
        f"{w.personality_pct}% of your tool calls were {w.personality_tag}"
        if w.personality != "The Generalist"
        else "a balanced mix of build, search and shell"
    )
    subtitle = Text(sub, style="yellow", justify="center")

    grid = Table.grid(expand=True, padding=(0, 3))
    for _ in range(3):
        grid.add_column(justify="center", ratio=1)

    def cell(val: str, lbl: str) -> Text:
        t = Text(justify="center")
        t.append(f"{val}\n", style="bold green")
        t.append(lbl.upper(), style="dim")
        return t

    grid.add_row(
        cell(human_int(w.n_sessions), "sessions"),
        cell(human_int(w.n_tool_calls), "tool calls"),
        cell(human_int(w.total_output_tokens), "tokens written"),
    )
    grid.add_row("", "", "")
    grid.add_row(
        cell(f"${w.total_cost_usd:,.0f}", "est. spend"),
        cell(str(w.busiest_day_calls), f"busiest day ({w.busiest_day or '—'})"),
        cell(human_int(w.longest_session_calls), "longest run"),
    )

    tools = Text("  ", justify="center")
    total = max(1, w.n_tool_calls)
    for name, count in w.top_tools:
        tools.append(f" {name} {count * 100 // total}% ", style="black on green")
        tools.append("  ")

    body = Group(
        title,
        subtitle,
        Text(""),
        grid,
        Text(""),
        Align.center(tools),
    )
    console.print(
        Panel(
            body,
            title=f"[bold green]AGENT · WRAPPED[/bold green]  [dim]{year}[/dim]",
            subtitle="[dim]100% local · github.com/sachincse/agentwrapped[/dim]",
            border_style="green",
            padding=(1, 3),
        )
    )
