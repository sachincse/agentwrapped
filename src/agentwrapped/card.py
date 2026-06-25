"""Render a :class:`Wrapped` to a shareable PNG card (1200x630, the social-share
size). Pure Pillow, no network. Fonts are resolved from common system paths
with a graceful fallback to Pillow's bundled default.
"""
from __future__ import annotations

import os
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from .stats import Wrapped

W, H = 1200, 630
PAD = 64

# vibrant 3-stop gradient (deep indigo -> violet)
_GRAD = [(15, 12, 41), (48, 43, 99), (36, 36, 62)]
_ACCENT = (0, 229, 160)      # mint — big numbers
_ACCENT2 = (255, 209, 102)   # amber — personality
_FG = (240, 244, 248)
_DIM = (160, 170, 190)

_FONT_CANDIDATES = {
    False: [
        "C:/Windows/Fonts/segoeui.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
    True: [
        "C:/Windows/Fonts/segoeuib.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
}


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES[bold]:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:  # Pillow >= 10.1 ships a scalable default
        return ImageFont.load_default(size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def human_int(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient(draw: ImageDraw.ImageDraw) -> None:
    half = H // 2
    for y in range(H):
        if y < half:
            color = _lerp(_GRAD[0], _GRAD[1], y / half)
        else:
            color = _lerp(_GRAD[1], _GRAD[2], (y - half) / (H - half))
        draw.line([(0, y), (W, y)], fill=color)


def _text_w(draw, text, font) -> int:
    return int(draw.textlength(text, font=font))


def render_png(w: Wrapped, out_path: str) -> str:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw)

    f_label = _load_font(22, bold=True)
    f_huge = _load_font(58, bold=True)
    f_stat = _load_font(40, bold=True)
    f_statlbl = _load_font(19)
    f_small = _load_font(20)
    f_foot = _load_font(18)

    year = str(w.year) if w.year else "all-time"

    # header
    draw.text((PAD, 44), "AGENT · WRAPPED", font=f_label, fill=_ACCENT)
    yr_w = _text_w(draw, year.upper(), f_label)
    draw.text((W - PAD - yr_w, 44), year.upper(), font=f_label, fill=_DIM)

    # personality headline
    draw.text((PAD, 92), f"You are {w.personality}", font=f_huge, fill=_FG)
    sub = (
        f"{w.personality_pct}% of your tool calls were {w.personality_tag}"
        if w.personality != "The Generalist"
        else "a balanced mix of build, search and shell"
    )
    draw.text((PAD, 162), sub, font=f_small, fill=_ACCENT2)

    # stat grid (3 columns x 2 rows)
    stats = [
        (human_int(w.n_sessions), "sessions"),
        (human_int(w.n_tool_calls), "tool calls"),
        (human_int(w.total_output_tokens), "tokens written"),
        (f"${w.total_cost_usd:,.0f}", "est. spend"),
        (f"{w.busiest_day_calls}", "busiest day"),
        (human_int(w.longest_session_calls), "longest run"),
    ]
    col_w = (W - 2 * PAD) // 3
    top = 230
    row_h = 118
    for i, (val, lbl) in enumerate(stats):
        cx = PAD + (i % 3) * col_w
        cy = top + (i // 3) * row_h
        draw.text((cx, cy), val, font=f_stat, fill=_ACCENT if i % 2 == 0 else _FG)
        draw.text((cx, cy + 52), lbl.upper(), font=f_statlbl, fill=_DIM)

    # top tools row
    ty = top + 2 * row_h + 6
    draw.text((PAD, ty), "TOP TOOLS", font=f_statlbl, fill=_DIM)
    x = PAD
    total_calls = max(1, w.n_tool_calls)
    for name, count in w.top_tools:
        chip = f"{name} {count * 100 // total_calls}%"
        cw = _text_w(draw, chip, f_small) + 28
        draw.rounded_rectangle([x, ty + 26, x + cw, ty + 64], radius=18,
                               fill=(46, 44, 82), outline=_ACCENT, width=1)
        draw.text((x + 14, ty + 34), chip, font=f_small, fill=_FG)
        x += cw + 14
        if x > W - PAD - 120:
            break

    # footer
    foot = "made with agentwrapped · 100% local, nothing uploaded · github.com/sachincse/agentwrapped"
    draw.text((PAD, H - 44), foot, font=f_foot, fill=_DIM)

    img.save(out_path, "PNG")
    return out_path
