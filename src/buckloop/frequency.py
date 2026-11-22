"""Analytic open-loop Bode plot of the buck control-to-output transfer function.

No SciPy, no FFT: just ``cmath`` evaluated at ``s = j*omega``.

The averaged buck linearizes to

    Vout(s) / D(s) = Vin / (L*C*s^2 + (L/R)*s + 1)

derived in ``docs/notes.md``.  ESR is intentionally neglected here so the
plot matches the documented ideal model; the time-domain plant may include
ESR.  This describes the *open loop* plant, not the closed PID loop.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass

from .plant import BuckPlant


@dataclass(frozen=True)
class BodePoint:
    """One frequency sample of the control-to-output transfer function."""

    freq_hz: float
    magnitude_db: float
    phase_deg: float


def control_to_output(plant: BuckPlant, omega: float) -> complex:
    """Complex value of Vout/D at angular frequency ``omega`` (rad/s)."""
    s = 1j * omega
    denominator = plant.l * plant.c * s * s + (plant.l / plant.r) * s + 1.0
    return plant.vin / denominator


def bode(
    plant: BuckPlant, f_min: float = 10.0, f_max: float = 100_000.0, n: int = 60
) -> list[BodePoint]:
    """Return ``n`` log-spaced Bode points between ``f_min`` and ``f_max`` Hz."""
    if n < 2:
        raise ValueError("n must be at least 2")
    if f_min <= 0 or f_max <= f_min:
        raise ValueError("require 0 < f_min < f_max")

    log_min, log_max = math.log10(f_min), math.log10(f_max)
    points: list[BodePoint] = []
    for index in range(n):
        freq = 10.0 ** (log_min + (log_max - log_min) * index / (n - 1))
        value = control_to_output(plant, 2.0 * math.pi * freq)
        points.append(
            BodePoint(
                freq_hz=freq,
                magnitude_db=20.0 * math.log10(abs(value)),
                phase_deg=math.degrees(cmath.phase(value)),
            )
        )
    return points


def resonance_frequency(plant: BuckPlant) -> float:
    """Estimate the magnitude-peak frequency in Hz (0 if there is no peak).

    For the standard second-order denominator: omega_0 = 1/sqrt(LC) and
    zeta = sqrt(L/C)/(2R).  A peak exists only when zeta < 1/sqrt(2), at
    omega_r = omega_0 * sqrt(1 - 2*zeta^2).
    """
    omega_0 = 1.0 / math.sqrt(plant.l * plant.c)
    zeta = math.sqrt(plant.l / plant.c) / (2.0 * plant.r)
    if zeta >= 1.0 / math.sqrt(2.0):
        return 0.0
    omega_r = omega_0 * math.sqrt(1.0 - 2.0 * zeta * zeta)
    return omega_r / (2.0 * math.pi)
