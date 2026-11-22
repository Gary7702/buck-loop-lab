# buck-loop-lab

A small, honest, runnable GitHub portfolio project about **digital closed-loop control of a buck converter**: a deterministic pure-Python plant + digital PID simulation that produces step-response and Bode-plot data as CSV and hand-written SVG, plus a clearly-marked STM32 skeleton.

[中文说明](README.zh-CN.md)

## What it IS

- A **simulation-only** teaching/demo project: averaged buck state-space model (RK4), discrete PID with anti-windup, closed-loop step response with transient metrics, and an analytic open-loop Bode plot.
- 100% standard library (`math`, `cmath`, `dataclasses`, `argparse`, `csv`, `pathlib`). **No numpy, scipy, or matplotlib.**
- Offline, deterministic, testable. All data is synthetic, produced by the model.

## What it is NOT

- **Not hardware.** No board was available; nothing was flashed or measured.
- **Not production firmware.** `firmware/` is an unverified template: no pinout, ADC calibration, or PWM setup guaranteed.
- **Not real measurement data.** No oscilloscope or network-analyzer capture is included or claimed.
- **Not a SPICE-grade power-stage model.** Ideal switches, CCM only, no losses; see [docs/notes.md](docs/notes.md).

## Install and run (offline)

```bash
python -m pip install -e "E:/doc_workbuddy/buck-loop-lab[dev]"
python -m buckloop all --out "E:/doc_workbuddy/buck-loop-lab/examples/output"
```

Other real commands:

```bash
python -m buckloop bode
python -m buckloop step --setpoint 9 --duration 0.02
python -m buckloop step --help
```

`--out` is a **directory**; it is created if missing. Paths with spaces work.

## Real sample output (copied from an actual run)

`python -m buckloop all --out "E:/doc_workbuddy/buck-loop-lab/examples/output"`:

```text
[all] output directory: E:\doc_workbuddy\buck-loop-lab\examples\output
[step] setpoint=9 V, dt=2e-06 s, samples=10001
  final value   : 9.0000 V
  rise (10-90%) : 0.000158 s
  overshoot     : 7.68 %
  settling (2%) : 0.004598 s
  steady error  : 0.0000 V
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\step_response.csv
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\step_response.svg

[bode] 60 points, 10 .. 100000 Hz
  resonance estimate : 1068.1 Hz
  peak magnitude     : 38.87 dB @ 1081.2 Hz
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\bode.csv
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\bode.svg
```

`python -m buckloop bode`:

```text
[bode] 60 points, 10 .. 100000 Hz
  resonance estimate : 1068.1 Hz
  peak magnitude     : 38.87 dB @ 1081.2 Hz
  wrote examples\output\bode.csv
  wrote examples\output\bode.svg
```

`python -m buckloop step --setpoint 9 --duration 0.02`:

```text
[step] setpoint=9 V, dt=2e-06 s, samples=10001
  final value   : 9.0000 V
  rise (10-90%) : 0.000158 s
  overshoot     : 7.68 %
  settling (2%) : 0.004598 s
  steady error  : 0.0000 V
  wrote examples\output\step_response.csv
  wrote examples\output\step_response.svg
```

Outputs: `step_response.csv` (`time_s,voltage_v,duty`), `step_response.svg`
(time vs voltage with setpoint line), `bode.csv` (`freq_hz,magnitude_db,phase_deg`),
and `bode.svg` (magnitude/phase vs log frequency). SVGs are written by hand
and start with `<svg`.

## Project layout

```text
buck-loop-lab/
├── src/buckloop/
│   ├── __init__.py       public API + version
│   ├── plant.py          averaged buck, RK4, optional ESR, duty clamp
│   ├── controller.py     discrete PID, filtered D-on-measurement, anti-windup
│   ├── sim.py            closed-loop step response + transient metrics
│   ├── frequency.py      analytic control-to-output Bode + resonance estimate
│   ├── svg.py            dependency-free SVG writer (two charts)
│   ├── cli.py            argparse subcommands: step / bode / all
│   └── __main__.py       python -m buckloop
├── firmware/             STM32 TEMPLATE, UNVERIFIED on hardware
│   ├── README.md         honesty / adaptation notes
│   ├── loop.md           ADC -> PID -> PWM -> tick pseudocode
│   ├── pid.h             PID state + API skeleton
│   └── pid.c             mirrors the Python controller math
├── docs/notes.md         small-signal derivation and simplifications
├── tests/                pytest tests
├── examples/output/      generated CSV + SVG (regenerate with `all`)
├── .github/workflows/ci.yml
├── pyproject.toml
└── LICENSE               MIT, 2026 Gary7702
```

## Development commands

```bash
python -m pytest tests --cov=buckloop --cov-report=term-missing
python -m coverage run -m pytest tests && python -m coverage report -m
python -m ruff check .
python -m ruff format --check .
python -m ruff format .
python -m build --no-isolation . --outdir dist
```

`pytest --cov` needs `pytest-cov`; if it is not installed, use the
`coverage run` line above, which needs only the `coverage` package.

## Honesty note

This is a simulation-only portfolio project built with AI assistance in
**November 2026**. The model is synthetic and ideal; the firmware skeleton is
**unverified on real hardware**; no production use, measured data, or
hardware performance is claimed. Adapt and validate everything before using
any of it in a real converter.
