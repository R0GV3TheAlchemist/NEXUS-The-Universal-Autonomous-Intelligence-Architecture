"""
GAIA Alignment Visualizer — Schumann + HRV State → Sparkline PNG

Converts the current AlignmentState into a compact 64×32px sparkline image
that can be injected into the LLM's vision context window.

Forbes (May 22, 2026) validation: multimodal LLMs grounded via IoT sensor
images reduce FLOP usage by 40–75% vs. text-only token serialization.

Instead of serializing ~200 tokens of JSON biometric state, we render a
~64x32 sparkline PNG (≤10 token-equivalent) that Qwen3.5-9B reads natively.

Usage:
    from sidecar.alignment_visualizer import render_alignment_sparkline
    b64_png = render_alignment_sparkline(state)
    # Pass to llm_router.generate(..., images=[b64_png], task_type=TaskType.VISION)
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field

log = logging.getLogger("gaia.alignment_visualizer")

# Canvas dimensions — small enough to be cheap, large enough to be readable
IMG_W = 64
IMG_H = 32

# Color palette (RGB tuples)
COLOR_BG          = (10,  10,  18)    # near-black
COLOR_HRV         = (0,   200, 150)   # teal-green
COLOR_SCHUMANN    = (100, 120, 255)   # indigo-blue
COLOR_KP          = (255, 180, 40)    # amber
COLOR_ALIGNMENT   = (220, 60,  200)   # magenta (composite score)
COLOR_GRID        = (30,  30,  50)    # dark grid lines
COLOR_LABEL_TEXT  = (180, 180, 200)   # soft white


@dataclass
class AlignmentState:
    """
    Snapshot of the Schumann + HRV biometric alignment state.
    All scores are normalised to [0.0, 1.0] unless noted.
    """
    hrv_score:          float = 0.5     # HRV coherence (0–1)
    schumann_score:     float = 0.5     # Schumann amplitude alignment (0–1)
    kp_index:           float = 0.3     # Kp geomagnetic index (0–1, normalised from 0–9)
    alignment_score:    float = 0.5     # Composite alignment (0–1)

    # Rolling history for sparklines (last N samples, newest last)
    hrv_history:        list[float] = field(default_factory=list)
    schumann_history:   list[float] = field(default_factory=list)
    alignment_history:  list[float] = field(default_factory=list)

    # Human-readable state label (injected as alt-text into vision prompt)
    label:              str = "nominal"


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _draw_sparkline(
    pixels: list[list[list[int]]],
    history: list[float],
    color: tuple[int, int, int],
    x_start: int,
    x_end: int,
    y_top: int,
    y_bot: int,
    thickness: int = 1,
) -> None:
    """
    Draw a sparkline into the pixel buffer.
    pixels[y][x] = [R, G, B]
    """
    if not history:
        return
    w = x_end - x_start
    h = y_bot - y_top

    # Resample history to w points
    n = len(history)
    for xi in range(w):
        # map xi → history index (interpolate)
        t = xi / max(w - 1, 1) * (n - 1)
        lo_i = int(t)
        hi_i = min(lo_i + 1, n - 1)
        frac = t - lo_i
        val = history[lo_i] * (1 - frac) + history[hi_i] * frac
        val = _clamp(val)

        # y coordinate (top = high value)
        yi = y_top + int((1.0 - val) * (h - 1))
        for dy in range(thickness):
            py = min(yi + dy, y_bot - 1)
            px = x_start + xi
            if 0 <= py < IMG_H and 0 <= px < IMG_W:
                pixels[py][px] = list(color)


def _draw_bar(
    pixels: list[list[list[int]]],
    value: float,
    color: tuple[int, int, int],
    x: int,
    y_top: int,
    y_bot: int,
    bar_w: int = 3,
) -> None:
    """Draw a vertical bar gauge at position x."""
    filled_h = int(_clamp(value) * (y_bot - y_top))
    for dy in range(filled_h):
        py = y_bot - 1 - dy
        for dx in range(bar_w):
            px = x + dx
            if 0 <= py < IMG_H and 0 <= px < IMG_W:
                pixels[py][px] = list(color)


def render_alignment_sparkline(state: AlignmentState) -> str:
    """
    Render the AlignmentState as a 64×32 RGB PNG sparkline.
    Returns a base64-encoded PNG string suitable for injection
    into the LLM vision context window.

    Layout (64×32):
      Left 48px  — three-channel sparkline (HRV / Schumann / Alignment history)
      Right 16px — four vertical bar gauges (HRV, Schumann, Kp, Alignment)
    """
    # Initialise pixel buffer
    pixels: list[list[list[int]]] = [
        [list(COLOR_BG) for _ in range(IMG_W)]
        for _ in range(IMG_H)
    ]

    # Draw subtle grid lines
    for y in [8, 16, 24]:
        for x in range(IMG_W):
            pixels[y][x] = list(COLOR_GRID)

    # ── Sparklines (left 48px) ─────────────────────────────────
    spark_x_end = 48

    # Pad histories to at least 2 points so sparklines always render
    def _pad(h: list[float], v: float) -> list[float]:
        return h if len(h) >= 2 else ([v] * 2)

    _draw_sparkline(pixels, _pad(state.hrv_history, state.hrv_score),
                    COLOR_HRV, 0, spark_x_end, 1, IMG_H - 1)
    _draw_sparkline(pixels, _pad(state.schumann_history, state.schumann_score),
                    COLOR_SCHUMANN, 0, spark_x_end, 1, IMG_H - 1)
    _draw_sparkline(pixels, _pad(state.alignment_history, state.alignment_score),
                    COLOR_ALIGNMENT, 0, spark_x_end, 1, IMG_H - 1, thickness=2)

    # ── Bar gauges (right 16px) ─────────────────────────────────
    gauges = [
        (state.hrv_score,       COLOR_HRV,       48),
        (state.schumann_score,  COLOR_SCHUMANN,  51),
        (state.kp_index,        COLOR_KP,        54),
        (state.alignment_score, COLOR_ALIGNMENT, 57),
    ]
    for val, color, x in gauges:
        _draw_bar(pixels, val, color, x, 2, IMG_H - 2)

    # ── Encode as PNG ───────────────────────────────────────────────
    # We write a minimal PNG without Pillow dependency for portability.
    # Uses stdlib only: zlib + struct.
    import zlib
    import struct

    def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    # PNG signature
    png = b"\x89PNG\r\n\x1a\n"

    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", IMG_W, IMG_H, 8, 2, 0, 0, 0)  # 8-bit RGB
    png += _png_chunk(b"IHDR", ihdr_data)

    # IDAT (raw pixel data, filter byte 0 per row)
    raw_rows = b""
    for row in pixels:
        raw_rows += b"\x00"  # filter type: None
        for pixel in row:
            raw_rows += bytes(pixel)
    compressed = zlib.compress(raw_rows, level=6)
    png += _png_chunk(b"IDAT", compressed)

    # IEND
    png += _png_chunk(b"IEND", b"")

    b64 = base64.b64encode(png).decode("ascii")
    log.debug(
        f"[alignment_visualizer] rendered sparkline | "
        f"hrv={state.hrv_score:.2f} schumann={state.schumann_score:.2f} "
        f"kp={state.kp_index:.2f} align={state.alignment_score:.2f} "
        f"png_bytes={len(png)} b64_chars={len(b64)}"
    )
    return b64


def alignment_vision_prompt(state: AlignmentState) -> str:
    """
    Returns the text description injected alongside the sparkline image.
    Keeps token count minimal while giving the model full semantic context.
    """
    kp_label = (
        "quiet" if state.kp_index < 0.22
        else "unsettled" if state.kp_index < 0.56
        else "stormy"
    )
    return (
        f"[GAIA Biometric Context] "
        f"HRV coherence {state.hrv_score:.0%} | "
        f"Schumann alignment {state.schumann_score:.0%} | "
        f"Geomagnetic field {kp_label} (Kp={state.kp_index * 9:.1f}) | "
        f"Composite alignment {state.alignment_score:.0%} | "
        f"State: {state.label}. "
        f"The sparkline image shows rolling history (teal=HRV, indigo=Schumann, magenta=composite). "
        f"Adapt your response tone and depth to this biometric context."
    )
