"""Command-line interface for buckloop.

All outputs (CSV + hand-written SVG) go into ``--out``, treated as a
directory so paths with spaces work without shell quoting tricks.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .controller import PIDController
from .frequency import BodePoint, bode, resonance_frequency
from .plant import BuckPlant
from .sim import Result, step_response
from .svg import bode_svg, step_response_svg

DEFAULT_OUT = "examples/output"


def _controller(dt: float) -> PIDController:
    """A deliberately simple, stable PI tuning for the default plant."""
    return PIDController(
        kp=0.15,
        ki=150.0,
        kd=5e-6,
        ts=dt,
        out_min=0.0,
        out_max=1.0,
        deriv_alpha=0.2,
    )


def _write_step_csv(result: Result, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_s", "voltage_v", "duty"])
        for t, v, d in zip(result.times, result.voltages, result.duties):
            writer.writerow([f"{t:.9g}", f"{v:.9g}", f"{d:.9g}"])


def _write_bode_csv(points: list[BodePoint], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["freq_hz", "magnitude_db", "phase_deg"])
        for point in points:
            writer.writerow(
                [f"{point.freq_hz:.9g}", f"{point.magnitude_db:.9g}", f"{point.phase_deg:.9g}"]
            )


def _print_step(result: Result, dt: float) -> None:
    m = result.metrics
    rise = "n/a" if m.rise_time_s is None else f"{m.rise_time_s:.6f} s"
    settle = "n/a" if m.settling_time_s is None else f"{m.settling_time_s:.6f} s"
    print(f"[step] setpoint={result.setpoint:g} V, dt={dt:g} s, samples={len(result.times)}")
    print(f"  final value   : {m.final_value:.4f} V")
    print(f"  rise (10-90%) : {rise}")
    print(f"  overshoot     : {m.overshoot_pct:.2f} %")
    print(f"  settling (2%) : {settle}")
    print(f"  steady error  : {m.steady_state_error:.4f} V")


def run_step(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = step_response(BuckPlant(), _controller(args.dt), args.setpoint, args.duration, args.dt)
    _print_step(result, args.dt)
    csv_path = out_dir / "step_response.csv"
    svg_path = out_dir / "step_response.svg"
    _write_step_csv(result, csv_path)
    step_response_svg(result, svg_path)
    print(f"  wrote {csv_path}")
    print(f"  wrote {svg_path}")
    return 0


def run_bode(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    plant = BuckPlant()
    points = bode(plant, args.f_min, args.f_max, args.n)
    resonance = resonance_frequency(plant)
    peak = max(points, key=lambda p: p.magnitude_db)
    print(f"[bode] {len(points)} points, {args.f_min:g} .. {args.f_max:g} Hz")
    print(f"  resonance estimate : {resonance:.1f} Hz")
    print(f"  peak magnitude     : {peak.magnitude_db:.2f} dB @ {peak.freq_hz:.1f} Hz")
    csv_path = out_dir / "bode.csv"
    svg_path = out_dir / "bode.svg"
    _write_bode_csv(points, csv_path)
    bode_svg(points, svg_path, resonance_hz=resonance)
    print(f"  wrote {csv_path}")
    print(f"  wrote {svg_path}")
    return 0


def run_all(args: argparse.Namespace) -> int:
    print(f"[all] output directory: {Path(args.out).resolve()}")
    run_step(args)
    print()
    run_bode(args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="buckloop",
        description="Deterministic buck closed-loop step response and Bode plot (simulation only).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    step_parser = subparsers.add_parser("step", help="run a closed-loop step response")
    step_parser.add_argument(
        "--setpoint", type=float, default=9.0, help="target output voltage (V)"
    )
    step_parser.add_argument("--duration", type=float, default=0.02, help="simulation length (s)")
    step_parser.add_argument("--dt", type=float, default=2e-6, help="sample / integration step (s)")
    step_parser.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    step_parser.set_defaults(func=run_step)

    bode_parser = subparsers.add_parser("bode", help="compute the open-loop Bode plot")
    bode_parser.add_argument("--f-min", type=float, default=10.0, help="lowest frequency (Hz)")
    bode_parser.add_argument(
        "--f-max", type=float, default=100_000.0, help="highest frequency (Hz)"
    )
    bode_parser.add_argument("--n", type=int, default=60, help="number of log-spaced points")
    bode_parser.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    bode_parser.set_defaults(func=run_bode)

    all_parser = subparsers.add_parser("all", help="run both step and bode")
    all_parser.add_argument("--setpoint", type=float, default=9.0)
    all_parser.add_argument("--duration", type=float, default=0.02)
    all_parser.add_argument("--dt", type=float, default=2e-6)
    all_parser.add_argument("--f-min", type=float, default=10.0)
    all_parser.add_argument("--f-max", type=float, default=100_000.0)
    all_parser.add_argument("--n", type=int, default=60)
    all_parser.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    all_parser.set_defaults(func=run_all)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
