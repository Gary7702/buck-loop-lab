"""PID saturation, anti-windup and derivative handling."""

import pytest

from buckloop.controller import PIDController


def test_output_is_saturated_and_integrator_does_not_wind_up() -> None:
    pid = PIDController(kp=0.1, ki=100.0, ts=1e-3, out_min=0.0, out_max=1.0)
    outputs = [pid.compute(100.0, 0.0) for _ in range(1000)]
    assert all(value == 1.0 for value in outputs)
    assert pid.integral == 0.0  # frozen by conditional integration

    # Once the error is zero, the controller recovers immediately.
    assert pid.compute(0.0, 0.0) == 0.0


def test_lower_saturation() -> None:
    pid = PIDController(kp=0.1, ki=10.0, ts=1e-3, out_min=0.0, out_max=1.0)
    assert pid.compute(-100.0, 0.0) == 0.0
    assert pid.integral == 0.0


def test_derivative_on_measurement_avoids_setpoint_kick() -> None:
    pid = PIDController(kp=0.01, ki=0.0, kd=100.0, ts=1e-3, deriv_alpha=0.0)
    assert pid.compute(0.0, 5.0) == 0.0
    # Measurement unchanged: derivative must stay zero despite the setpoint jump.
    assert pid.compute(100.0, 5.0) == pytest.approx(0.95)  # kp * (100 - 5), no D kick


def test_filtered_derivative_is_recursive() -> None:
    pid = PIDController(kp=0.0, ki=0.0, kd=0.0, ts=1e-3, deriv_alpha=0.5)
    pid.compute(0.0, 0.0)
    pid.compute(0.0, 1.0)  # raw derivative = 1000
    assert pid._filtered_deriv == pytest.approx(500.0)
    pid.compute(0.0, 1.0)  # raw derivative = 0
    assert pid._filtered_deriv == pytest.approx(250.0)


def test_reset_and_validation() -> None:
    pid = PIDController(kp=1.0, ki=1.0, ts=1e-3)
    pid.compute(1.0, 0.0)
    pid.reset()
    assert pid.integral == 0.0
    assert pid._initialized is False
    with pytest.raises(ValueError):
        PIDController(kp=1.0, ki=0.0, ts=0)
    with pytest.raises(ValueError):
        PIDController(kp=1.0, ki=0.0, ts=1, deriv_alpha=2.0)
    with pytest.raises(ValueError):
        PIDController(kp=1.0, ki=0.0, ts=1, out_min=2.0, out_max=1.0)
