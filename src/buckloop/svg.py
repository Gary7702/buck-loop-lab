"""Minimal dependency-free SVG chart writer.

Everything is emitted as plain text elements, polylines and axes.  The
output deliberately starts with ``<svg`` (no XML declaration) so it is
trivial to check and to embed.  Trajectories are downsampled for plotting
only; the CSV files keep every sample.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path

from .frequency import BodePoint
from .sim import Result


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _open_svg(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">'
    )


def _text(
    x: float,
    y: float,
    content: str,
    *,
    size: int = 12,
    anchor: str = "start",
    fill: str = "#222222",
) -> str:
    return (
        f'  <text x="{x:.2f}" y="{y:.2f}" font-family="monospace" '
        f'font-size="{size}" text-anchor="{anchor}" fill="{fill}">'
        f"{_escape(content)}</text>"
    )


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = "#888888",
    width: float = 1.0,
    dash: str = "",
) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{width}"{extra}/>'
    )


def _downsample(length: int, limit: int = 2000) -> list[int]:
    if length <= limit:
        return list(range(length))
    stride = math.ceil(length / limit)
    indices = list(range(0, length, stride))
    if indices[-1] != length - 1:
        indices.append(length - 1)
    return indices


def _fmt(value: float) -> str:
    return f"{value:.4g}"


def step_response_svg(
    result: Result, path: str | Path, *, width: int = 900, height: int = 520
) -> Path:
    """Write a time-vs-voltage chart with a dashed setpoint line."""
    if not result.times:
        raise ValueError("cannot plot an empty step response")

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    left, right, top, bottom = 80.0, 30.0, 56.0, 62.0
    plot_w = width - left - right
    plot_h = height - top - bottom

    times, voltages = result.times, result.voltages
    t0, t1 = times[0], times[-1]
    values = [*voltages, result.setpoint, 0.0]
    vlo, vhi = min(values), max(values)
    pad = 0.1 * (vhi - vlo) or 0.1
    vlo, vhi = vlo - pad, vhi + pad

    def x_of(t: float) -> float:
        return left if t1 == t0 else left + (t - t0) / (t1 - t0) * plot_w

    def y_of(v: float) -> float:
        return top + (vhi - v) / (vhi - vlo) * plot_h

    parts = [
        _open_svg(width, height),
        f'  <rect width="{width}" height="{height}" fill="#ffffff"/>',
        _text(width / 2, 30, "Buck closed-loop step response", size=16, anchor="middle"),
    ]

    for i in range(6):
        value = vlo + (vhi - vlo) * i / 5
        y = y_of(value)
        parts.append(_line(left, y, left + plot_w, y, stroke="#dddddd"))
        parts.append(_text(left - 8, y + 4, _fmt(value), anchor="end"))
    for i in range(6):
        value = t0 + (t1 - t0) * i / 5
        x = x_of(value)
        parts.append(_line(x, top, x, top + plot_h, stroke="#eeeeee"))
        parts.append(_text(x, top + plot_h + 20, _fmt(value), anchor="middle"))

    parts.append(_line(left, top, left, top + plot_h, stroke="#333333"))
    parts.append(_line(left, top + plot_h, left + plot_w, top + plot_h, stroke="#333333"))
    parts.append(_text(left + plot_w / 2, height - 20, "time (s)", anchor="middle"))
    parts.append(_text(16, top + plot_h / 2, "voltage (V)", anchor="middle"))

    parts.append(
        _line(
            left,
            y_of(result.setpoint),
            left + plot_w,
            y_of(result.setpoint),
            stroke="#e08a1e",
            width=1.5,
            dash="6,4",
        )
    )
    parts.append(
        _text(
            left + plot_w - 4,
            y_of(result.setpoint) - 6,
            f"setpoint = {result.setpoint:g} V",
            anchor="end",
            fill="#e08a1e",
        )
    )

    indices = _downsample(len(times))
    coords = " ".join(f"{x_of(times[i]):.2f},{y_of(voltages[i]):.2f}" for i in indices)
    parts.append(f'  <polyline fill="none" stroke="#1f77b4" stroke-width="2" points="{coords}"/>')
    parts.append(_text(left + 6, top + 16, "v_out", fill="#1f77b4"))

    parts.append("</svg>")
    out.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    return out


def bode_svg(
    points: Sequence[BodePoint],
    path: str | Path,
    *,
    resonance_hz: float | None = None,
    width: int = 900,
    height: int = 620,
) -> Path:
    """Write stacked magnitude (dB) and phase (deg) panels vs log frequency."""
    if len(points) < 2:
        raise ValueError("need at least two Bode points")

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    left, right, top, bottom, gap = 80.0, 30.0, 56.0, 62.0, 46.0
    plot_w = width - left - right
    panel_h = (height - top - bottom - gap) / 2.0
    mag_top = top
    phase_top = top + panel_h + gap

    freqs = [p.freq_hz for p in points]
    log_lo, log_hi = math.log10(min(freqs)), math.log10(max(freqs))

    def x_of(freq: float) -> float:
        return left + (math.log10(freq) - log_lo) / (log_hi - log_lo) * plot_w

    def axis(panel_top: float, low: float, high: float) -> tuple[float, float]:
        for i in range(5):
            value = low + (high - low) * i / 4
            y = panel_top + panel_h - (value - low) / (high - low) * panel_h
            parts.append(_line(left, y, left + plot_w, y, stroke="#dddddd"))
            parts.append(_text(left - 8, y + 4, _fmt(value), anchor="end"))
        parts.append(_line(left, panel_top, left, panel_top + panel_h, stroke="#333333"))
        parts.append(
            _line(left, panel_top + panel_h, left + plot_w, panel_top + panel_h, stroke="#333333")
        )
        return low, high

    def y_of(value: float, low: float, high: float, panel_top: float) -> float:
        return panel_top + panel_h - (value - low) / (high - low) * panel_h

    mags = [p.magnitude_db for p in points]
    phases = [p.phase_deg for p in points]

    def span(values: list[float]) -> tuple[float, float]:
        lo, hi = min(values), max(values)
        pad = 0.08 * (hi - lo) or 1.0
        return lo - pad, hi + pad

    mag_lo, mag_hi = span(mags)
    phase_lo, phase_hi = span(phases)

    parts = [
        _open_svg(width, height),
        f'  <rect width="{width}" height="{height}" fill="#ffffff"/>',
        _text(
            width / 2, 30, "Buck control-to-output Bode plot (open loop)", size=16, anchor="middle"
        ),
    ]

    axis(mag_top, mag_lo, mag_hi)
    axis(phase_top, phase_lo, phase_hi)

    decade_start = math.ceil(log_lo)
    decade_end = math.floor(log_hi)
    for decade in range(decade_start, decade_end + 1):
        x = x_of(10.0**decade)
        parts.append(_line(x, top, x, phase_top + panel_h, stroke="#bbbbbb", dash="3,3"))
        parts.append(_text(x, phase_top + panel_h + 20, f"1e{decade}", anchor="middle"))

    parts.append(_text(left + 6, mag_top + 16, "magnitude (dB)", fill="#1a9850"))
    parts.append(_text(left + 6, phase_top + 16, "phase (deg)", fill="#876bf1"))

    if resonance_hz and min(freqs) <= resonance_hz <= max(freqs):
        x = x_of(resonance_hz)
        parts.append(_line(x, top, x, phase_top + panel_h, stroke="#d73027", dash="5,4"))
        parts.append(_text(x + 4, top + 14, f"f_res ~ {resonance_hz:.0f} Hz", fill="#d73027"))

    mag_coords = " ".join(
        f"{x_of(p.freq_hz):.2f},{y_of(p.magnitude_db, mag_lo, mag_hi, mag_top):.2f}" for p in points
    )
    phase_coords = " ".join(
        f"{x_of(p.freq_hz):.2f},{y_of(p.phase_deg, phase_lo, phase_hi, phase_top):.2f}"
        for p in points
    )
    parts.append(
        f'  <polyline fill="none" stroke="#1a9850" stroke-width="2" points="{mag_coords}"/>'
    )
    parts.append(
        f'  <polyline fill="none" stroke="#876bf1" stroke-width="2" points="{phase_coords}"/>'
    )
    parts.append(
        _text(left + plot_w / 2, height - 18, "frequency (Hz, log scale)", anchor="middle")
    )

    parts.append("</svg>")
    out.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    return out
