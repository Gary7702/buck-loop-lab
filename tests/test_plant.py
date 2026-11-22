"""Plant stability, duty clamping and reset."""

import math

from buckloop.plant import BuckPlant


def test_bounded_output_for_full_duty() -> None:
    plant = BuckPlant()
    values = [plant.step(1.0, 2e-6) for _ in range(10000)]
    assert all(0.0 <= v <= 2.5 * plant.vin for v in values)
    assert math.isfinite(values[-1])
    assert abs(values[-1] - plant.vin) < 0.01  # settles at Vin*D


def test_zero_duty_decays_to_zero() -> None:
    plant = BuckPlant()
    for _ in range(5000):
        plant.step(1.0, 2e-6)
    values = [plant.step(0.0, 2e-6) for _ in range(10000)]
    assert values[-1] < 0.01


def test_duty_is_clamped() -> None:
    high = BuckPlant()
    clamped = BuckPlant()
    for _ in range(3000):
        high.step(1.0, 2e-6)
        clamped.step(7.3, 2e-6)
    assert math.isclose(high.output_voltage, clamped.output_voltage, rel_tol=1e-12)

    low = BuckPlant()
    below = BuckPlant()
    for _ in range(3000):
        low.step(0.0, 2e-6)
        below.step(-4.0, 2e-6)
    assert math.isclose(low.output_voltage, below.output_voltage, rel_tol=1e-12)


def test_reset_clears_states() -> None:
    plant = BuckPlant()
    plant.step(1.0, 2e-6)
    plant.reset()
    assert plant.i_l == 0.0
    assert plant.v_c == 0.0
    assert plant.output_voltage == 0.0


def test_esr_and_bad_arguments() -> None:
    plant = BuckPlant(esr=0.02)
    assert plant.step(0.5, 1e-6) > 0.0
    for kwargs in ({"vin": 0}, {"l": -1}, {"c": 0}, {"r": -5}, {"esr": -1}):
        try:
            BuckPlant(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")
    try:
        plant.step(0.5, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for dt=0")
