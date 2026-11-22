"""Deterministic discrete PID controller with anti-windup.

The derivative acts on the *measurement* (not the error), which avoids a
derivative kick when the setpoint changes, and is first-order filtered.
Anti-windup uses conditional integration: the integrator is frozen whenever
the unclamped output would push further into the configured limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PIDController:
    """Discrete PID.

    ``ts`` is the sample period in seconds, ``deriv_alpha`` is the derivative
    low-pass coefficient in [0, 1] (larger = smoother/slower).  Output is
    clamped to ``[out_min, out_max]``; for a buck duty cycle use [0, 1].
    """

    kp: float
    ki: float
    kd: float = 0.0
    ts: float = 1e-4
    out_min: float = 0.0
    out_max: float = 1.0
    deriv_alpha: float = 0.2
    integral: float = field(default=0.0, init=False)
    _prev_measurement: float = field(default=0.0, init=False)
    _filtered_deriv: float = field(default=0.0, init=False)
    _initialized: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.ts <= 0:
            raise ValueError("ts must be positive")
        if not 0.0 <= self.deriv_alpha <= 1.0:
            raise ValueError("deriv_alpha must be in [0, 1]")
        if self.out_min > self.out_max:
            raise ValueError("out_min must not exceed out_max")

    def reset(self) -> None:
        """Clear integrator and derivative history."""
        self.integral = 0.0
        self._prev_measurement = 0.0
        self._filtered_deriv = 0.0
        self._initialized = False

    def compute(self, setpoint: float, measurement: float) -> float:
        """Return the bounded control signal for this sample."""
        error = setpoint - measurement

        if not self._initialized:
            self._prev_measurement = measurement
            self._filtered_deriv = 0.0
            self._initialized = True
        else:
            raw_deriv = (measurement - self._prev_measurement) / self.ts
            self._filtered_deriv = (
                self.deriv_alpha * self._filtered_deriv + (1.0 - self.deriv_alpha) * raw_deriv
            )
            self._prev_measurement = measurement

        proportional = self.kp * error
        derivative = -self.kd * self._filtered_deriv
        integral_candidate = self.integral + self.ki * error * self.ts

        tentative = proportional + integral_candidate + derivative
        driving_into_limit = (tentative > self.out_max and error > 0) or (
            tentative < self.out_min and error < 0
        )
        if driving_into_limit:
            integral = self.integral  # freeze: conditional-integration anti-windup
        else:
            integral = integral_candidate
        self.integral = integral

        output = proportional + integral + derivative
        return min(self.out_max, max(self.out_min, output))
