"""buckloop - a small, honest buck-converter digital-control simulator.

Simulation only.  The STM32 code under ``firmware/`` is an untested template.
"""

__version__ = "0.1.0"

from .controller import PIDController
from .frequency import BodePoint, bode, resonance_frequency
from .plant import BuckPlant
from .sim import Result, StepMetrics, step_response

__all__ = [
    "BodePoint",
    "BuckPlant",
    "PIDController",
    "Result",
    "StepMetrics",
    "__version__",
    "bode",
    "resonance_frequency",
    "step_response",
]
