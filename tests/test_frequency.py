"""Bode point count, monotonic frequency and resonance sanity."""

import math

import pytest

from buckloop.frequency import bode, control_to_output, resonance_frequency
from buckloop.plant import BuckPlant


def test_bode_points_and_frequency_order() -> None:
    points = bode(BuckPlant(), n=60)
    assert len(points) == 60
    assert all(b.freq_hz > a.freq_hz for a, b in zip(points, points[1:]))
    assert points[0].freq_hz == pytest.approx(10.0)
    assert points[-1].freq_hz == pytest.approx(100_000.0)
    assert all(math.isfinite(p.magnitude_db) and math.isfinite(p.phase_deg) for p in points)


def test_low_frequency_gain_and_phase_trend() -> None:
    points = bode(BuckPlant(), n=120)
    dc_db = 20 * math.log10(BuckPlant().vin)
    assert abs(points[0].magnitude_db - dc_db) < 0.5
    assert points[-1].magnitude_db < points[0].magnitude_db - 20
    assert points[0].phase_deg > -5
    assert points[-1].phase_deg < -170


def test_resonance_sanity() -> None:
    plant = BuckPlant()
    resonance = resonance_frequency(plant)
    f0 = 1 / (2 * math.pi * math.sqrt(plant.l * plant.c))
    assert 0 < resonance < f0
    points = bode(plant, n=400)
    peak = max(points, key=lambda p: p.magnitude_db)
    assert abs(peak.freq_hz - resonance) / resonance < 0.1
    assert peak.magnitude_db > points[0].magnitude_db + 10


def test_no_peak_when_heavily_damped() -> None:
    assert resonance_frequency(BuckPlant(r=0.1)) == 0.0


def test_transfer_helper_and_validation() -> None:
    plant = BuckPlant()
    assert abs(control_to_output(plant, 0.0) - plant.vin) < 1e-9
    with pytest.raises(ValueError):
        bode(plant, n=1)
    with pytest.raises(ValueError):
        bode(plant, f_min=0, f_max=100)
    with pytest.raises(ValueError):
        bode(plant, f_min=200, f_max=100)
