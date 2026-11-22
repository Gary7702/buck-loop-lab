"""Closed-loop step response and elementary transient metrics."""

from __future__ import annotations

from dataclasses import dataclass

from .controller import PIDController
from .plant import BuckPlant


@dataclass
class StepMetrics:
    """Summary numbers for a step response.

    ``None`` means the event was not observed inside the simulated window
    (e.g. the response never entered the settling band).
    """

    rise_time_s: float | None
    overshoot_pct: float
    settling_time_s: float | None
    steady_state_error: float
    final_value: float


@dataclass
class Result:
    """Recorded step-response trajectory plus its metrics."""

    setpoint: float
    times: list[float]
    voltages: list[float]
    duties: list[float]
    metrics: StepMetrics


def _final_value(voltages: list[float]) -> float:
    """Average the last 5% of samples to estimate the steady state."""
    if not voltages:
        return 0.0
    count = max(1, len(voltages) // 20)
    window = voltages[-count:]
    return sum(window) / len(window)


def _rise_time(times: list[float], voltages: list[float], setpoint: float) -> float | None:
    if setpoint <= 0:
        return None
    low, high = 0.1 * setpoint, 0.9 * setpoint
    t_low: float | None = None
    for t, v in zip(times, voltages):
        if t_low is None and v >= low:
            t_low = t
        if t_low is not None and v >= high:
            return t - t_low
    return None


def _settling_time(
    times: list[float], voltages: list[float], final: float, tol: float = 0.02
) -> float | None:
    band = tol * abs(final)
    last_outside = -1
    for index, value in enumerate(voltages):
        if abs(value - final) > band:
            last_outside = index
    if last_outside >= len(voltages) - 1:
        return None
    return times[last_outside + 1]


def step_response(
    plant: BuckPlant,
    controller: PIDController,
    setpoint: float,
    duration: float,
    dt: float,
) -> Result:
    """Simulate ``duration`` seconds of closed-loop step response.

    Both plant and controller are reset first.  The controller samples every
    ``dt`` seconds, the same as the plant integration step.  Metrics use the
    recorded trajectory only.
    """
    if duration <= 0 or dt <= 0:
        raise ValueError("duration and dt must be positive")
    steps = max(1, int(round(duration / dt)))

    plant.reset()
    controller.reset()

    times: list[float] = []
    voltages: list[float] = []
    duties: list[float] = []

    for index in range(steps + 1):
        t = index * dt
        v = plant.output_voltage
        duty = controller.compute(setpoint, v)
        times.append(t)
        voltages.append(v)
        duties.append(duty)
        plant.step(duty, dt)

    final = _final_value(voltages)
    peak = max(voltages, default=0.0)
    overshoot = max(0.0, (peak - final) / final * 100.0) if final > 0 else 0.0
    metrics = StepMetrics(
        rise_time_s=_rise_time(times, voltages, setpoint),
        overshoot_pct=overshoot,
        settling_time_s=_settling_time(times, voltages, final),
        steady_state_error=setpoint - final,
        final_value=final,
    )
    return Result(setpoint, times, voltages, duties, metrics)
