# STM32 firmware skeleton — TEMPLATE, NOT TESTED ON HARDWARE

> **Read this first.** Everything in this directory is an illustrative
> **template** for an STM32-like MCU. It has **not** been compiled, flashed,
> or verified on any real board. No pinout, ADC calibration, clock tree,
> PWM timer configuration, or hardware scaling is guaranteed to be correct.
> You must adapt all of it to your own MCU, board, and power stage before
> use. There is **no guarantee** that it will work, and no claim is made
> that it is production-ready.

## What this is

- A plain-text sketch of the control loop mirrored from `src/buckloop/controller.py`:
  `ADC read → PID compute → PWM duty update → timer tick`.
- A `pid.h` / `pid.c` skeleton that mirrors the Python controller's math
  (derivative-on-measurement, filtered derivative, conditional-integration
  anti-windup, output clamp).
- A place to document the mapping from the simulation to an implementation.

## What this is NOT

- Not compiled firmware. There is no toolchain, no startup code, no HAL/LL
  setup, no linker script, no ADC or PWM driver.
- Not a validated power-supply design. The simulation uses an averaged,
  ideal-switch, CCM-only model; real converters have switching delays,
  dead time, current ripple, sensing noise, and layout parasitics.
- Not a source of measured Bode or step-response data. All data in this
  repository is synthetic, produced by the Python simulation.

## Files

| File | Purpose |
| --- | --- |
| `loop.md` | Human-readable control-loop description + `main.c`-style pseudocode. |
| `pid.h` | PID state struct and function declarations. |
| `pid.c` | Skeleton implementation mirroring the Python controller. |

## Before adapting to real hardware

1. Choose and configure an ADC channel, reference voltage, and scaling so
   the sensed output voltage maps to volts correctly; calibrate the offset
   and gain. The Python model assumes a perfect, noise-free measurement.
2. Configure a PWM timer and verify the duty-to-voltage polarity and
   resolution. Clamp the duty to the duty range your driver actually allows.
3. Run the PID at a fixed sample period matching `pid.ts`. Use a timer
   interrupt or a deterministic scheduler, not a variable-delay loop.
4. Add output limits, soft-start, and over-voltage/over-current protection.
   The skeleton has none of these.
5. Re-tune the gains on the real plant. The default simulation gains
   (`kp=0.15`, `ki=150`, `kd=5e-6`, `ts=2e-6`) are for the simulated plant
   only and are not validated for any hardware.

No part of this directory has been verified on hardware.
