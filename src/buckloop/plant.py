"""Averaged state-space buck converter model (CCM, ideal switches).

Two states are integrated with fixed-step RK4:

    di_l/dt = (d * Vin - v_o) / L
    dv_c/dt = (i_l - v_o / R) / C
    v_o     = (v_c + ESR * i_l) / (1 + ESR / R)

where ``d`` is the duty cycle in [0, 1].  With ``esr = 0`` the output is
exactly the capacitor voltage and the model reduces to the textbook
averaged buck.  The ESR term above is the standard quasi-static
approximation: the capacitor current is ``i_c = i_l - v_o/R`` and
``v_o = v_c + ESR * i_c`` solved algebraically for ``v_o``.

SIMPLIFICATIONS (honest note): ideal switches, continuous conduction mode
only, no losses other than the optional ESR, fixed input voltage.
This is a teaching model, not a SPICE-grade power-stage model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BuckPlant:
    """Deterministic averaged buck plant.

    Defaults: Vin=12 V, L=100 uH, C=220 uF, R=5 Ohm, ESR=0 Ohm.
    RK4 with dt <= ~2 us is stable for these values (f_LC ~ 1.07 kHz).
    """

    vin: float = 12.0
    l: float = 100e-6  # noqa: E741 - L (inductance) is the conventional symbol
    c: float = 220e-6
    r: float = 5.0
    esr: float = 0.0
    i_l: float = 0.0
    v_c: float = 0.0

    def __post_init__(self) -> None:
        if self.vin <= 0 or self.l <= 0 or self.c <= 0 or self.r <= 0:
            raise ValueError("vin, l, c and r must be positive")
        if self.esr < 0:
            raise ValueError("esr must be non-negative")

    def reset(self) -> None:
        """Return the plant to its zero-energy initial state."""
        self.i_l = 0.0
        self.v_c = 0.0

    @property
    def output_voltage(self) -> float:
        """Output voltage implied by the current states (no time step)."""
        return self._output(self.i_l, self.v_c)

    def _output(self, i_l: float, v_c: float) -> float:
        return (v_c + self.esr * i_l) / (1.0 + self.esr / self.r)

    def _derivatives(self, i_l: float, v_c: float, duty: float) -> tuple[float, float]:
        v_o = self._output(i_l, v_c)
        di_l = (duty * self.vin - v_o) / self.l
        dv_c = (i_l - v_o / self.r) / self.c
        return di_l, dv_c

    def step(self, duty: float, dt: float) -> float:
        """Advance the plant by ``dt`` seconds with constant ``duty``.

        The duty cycle is clamped to [0, 1].  Returns the new output voltage.
        """
        if dt <= 0:
            raise ValueError("dt must be positive")
        d = min(1.0, max(0.0, duty))

        i, v = self.i_l, self.v_c
        k1i, k1v = self._derivatives(i, v, d)
        k2i, k2v = self._derivatives(i + 0.5 * dt * k1i, v + 0.5 * dt * k1v, d)
        k3i, k3v = self._derivatives(i + 0.5 * dt * k2i, v + 0.5 * dt * k2v, d)
        k4i, k4v = self._derivatives(i + dt * k3i, v + dt * k3v, d)

        self.i_l = i + (dt / 6.0) * (k1i + 2.0 * k2i + 2.0 * k3i + k4i)
        self.v_c = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
        return self.output_voltage
