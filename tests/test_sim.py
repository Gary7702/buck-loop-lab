"""Closed-loop step response and metrics on a known case."""

import math

import pytest

from buckloop.controller import PIDController
from buckloop.plant import BuckPlant
from buckloop.sim import step_response


def test_known_step_case() -> None:
    result = step_response(
        BuckPlant(),
        PIDController(kp=0.15, ki=150.0, kd=5e-6, ts=2e-6),
        setpoint=9.0,
        duration=0.01,
        dt=2e-6,
    )
    metrics = result.metrics
    assert len(result.times) == 5001
    assert result.times[0] == 0.0
    assert result.times[-1] == pytest.approx(0.01)
    assert all(b - a > 0 for a, b in zip(result.times, result.times[1:]))
    assert all(0.0 <= d <= 1.0 for d in result.duties)
    assert metrics.rise_time_s is not None and 0 < metrics.rise_time_s < 0.005
    assert 0.0 <= metrics.overshoot_pct < 20.0
    assert metrics.settling_time_s is not None
    assert abs(metrics.final_value - 9.0) < 0.05
    assert abs(metrics.steady_state_error) < 0.05


def test_short_duration_returns_metrics() -> None:
    result = step_response(BuckPlant(), PIDController(kp=0.1, ki=10.0, ts=2e-6), 9.0, 1e-4, 2e-6)
    assert math.isfinite(result.metrics.final_value)
    assert result.metrics.final_value < 9.0  # not settled in 0.1 ms


def test_invalid_arguments() -> None:
    with pytest.raises(ValueError):
        step_response(BuckPlant(), PIDController(kp=1, ki=0, ts=1), 9, 0, 1e-6)
    with pytest.raises(ValueError):
        step_response(BuckPlant(), PIDController(kp=1, ki=0, ts=1), 9, 0.01, 0)
