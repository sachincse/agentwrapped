"""agentwrapped — Spotify Wrapped for your AI coding agent.

    agentwrapped                 # render card.png from all local sessions
    agentwrapped --year 2026     # only this year
    agentwrapped --project       # just the current project, not machine-wide
    agentwrapped --terminal      # print to the terminal instead of a PNG
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .card import render_png
from .stats import build_wrapped
from .terminal import render_terminal

console = Console()
err = Console(stderr=True)


def main(
    out: str = typer.Option("agent-wrapped.png", "--out", "-o", help="Output PNG path."),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Limit to a calendar year."),
    project: bool = typer.Option(False, "--project", help="Only this project (default: all)."),
    terminal: bool = typer.Option(False, "--terminal", "-t", help="Print to terminal instead of PNG."),
    root: Optional[str] = typer.Option(None, "--root", help="Override the session-logs root."),
    show_version: bool = typer.Option(False, "--version", help="Print version and exit."),
) -> None:
    """Turn your local agent session logs into one shareable card."""
    if show_version:
        console.print(f"agentwrapped {__version__}")
        raise typer.Exit()

    w = build_wrapped(root=root, all_projects=not project, year=year)
    if w.n_sessions == 0:
        err.print("[red]No session logs found.[/red] Run a coding agent first, or pass --root.")
        raise typer.Exit(2)

    if terminal:
        render_terminal(w, console)
        return

    render_png(w, out)
    console.print(f"[green]✓[/green] Wrote [bold]{out}[/bold]  "
                  f"— {w.personality}, {w.n_sessions} sessions, "
                  f"{w.n_tool_calls:,} tool calls, ~${w.total_cost_usd:,.0f}")
    console.print("[dim]Share it. The card never left your machine.[/dim]")


def entrypoint() -> None:  # console-script entry point
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    typer.run(main)


if __name__ == "__main__":
    entrypoint()
