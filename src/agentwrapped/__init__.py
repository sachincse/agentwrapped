"""agentwrapped — Spotify Wrapped for your AI coding agent.

Reads the local session logs your coding agent already writes and renders one
shareable card. Reuses trace-lens for parsing.
"""
from __future__ import annotations

from .stats import Wrapped, build_wrapped

__all__ = ["build_wrapped", "Wrapped"]
__version__ = "0.1.0"
