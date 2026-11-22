"""SVG files are created, non-empty, and contain real chart markup."""

from pathlib import Path

import pytest

from buckloop.controller import PIDController
from buckloop.frequency import bode, resonance_frequency
from buckloop.plant import BuckPlant
from buckloop.sim import Result, StepMetrics, step_response
from buckloop.svg import bode_svg, step_response_svg


def test_step_response_svg(tmp_path: Path) -> None:
    result = step_response(BuckPlant(), PIDController(kp=0.15, ki=150, ts=2e-6), 9.0, 0.002, 2e-6)
    target = tmp_path / "step_response.svg"
    assert step_response_svg(result, target) == target
    content = target.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    assert "<polyline" in content
    assert "setpoint" in content
    assert "</svg>" in content
    assert target.stat().st_size > 1000


def test_bode_svg(tmp_path: Path) -> None:
    points = bode(BuckPlant(), n=30)
    target = tmp_path / "bode.svg"
    assert bode_svg(points, target, resonance_hz=resonance_frequency(BuckPlant())) == target
    content = target.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    assert content.count("<polyline") == 2
    assert "magnitude" in content and "phase" in content
    assert target.stat().st_size > 1000


def test_empty_input_rejected(tmp_path: Path) -> None:
    empty = Result(9.0, [], [], [], StepMetrics(None, 0.0, None, 0.0, 0.0))
    with pytest.raises(ValueError):
        step_response_svg(empty, tmp_path / "x.svg")
    with pytest.raises(ValueError):
        bode_svg([], tmp_path / "y.svg")
