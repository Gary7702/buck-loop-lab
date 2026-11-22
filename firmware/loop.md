# Control-loop sketch (pseudocode, not compiled)

**Status: TEMPLATE. Unverified on hardware.** See `README.md` in this directory.

The loop mirrors the Python simulation: on every fixed-period tick the MCU
reads the sensed output voltage, computes a bounded PID duty, and writes it
to the PWM compare register.

```text
ADC read (sensed Vout)
    -> convert counts to volts using calibration (NOT provided)
    -> PID compute(setpoint, measurement)
    -> write PWM duty = clamp(pid_output, duty_min, duty_max)
    -> wait for next timer tick (fixed Ts)
```

## main.c-style pseudocode (illustrative only)

```c
/* NOT real firmware: no includes, no HAL init, no clock/PWM/ADC setup.
   Names are placeholders. Do not copy verbatim into a project. */
#include "pid.h"

#define TS      2e-6f      /* example: 2 us tick; MUST match pid.ts */
#define VREF    3.3f
#define ADC_MAX 4095.0f
#define SENSE_SCALE  (VREF / ADC_MAX)  /* placeholder: divide by sense ratio! */

static PID pid;
static float setpoint_v = 9.0f;

void timer_tick_isr(void) {          /* called every Ts seconds */
    uint32_t raw = ADC_Read_Channel_placeholder();
    float vout = (float)raw * SENSE_SCALE;

    float duty = PID_Compute(&pid, setpoint_v, vout);

    /* TODO: map duty in [0,1] to the timer's counter range, and honour
       the actual polarity of your gate driver. Not implemented here. */
    PWM_Set_Duty_placeholder(duty);
}

int main(void) {
    /* TODO: clock, GPIO, ADC + calibration, PWM timer, ISR registration. */
    PID_Init(&pid,
             /* kp */ 0.15f,
             /* ki */ 150.0f,
             /* kd */ 5e-6f,
             /* ts */ TS,
             /* out_min */ 0.0f,
             /* out_max */ 1.0f,
             /* deriv_alpha */ 0.2f);

    /* TODO: soft-start ramp, then enable the ISR and PWM output. */
    for (;;) { /* idle / fault monitoring placeholder */ }
}
```

## Why the loop looks like this

- **ADC read first** — the controller needs the latest measurement. The
  Python `compute(setpoint, measurement)` has the same argument order.
- **PID compute** — deterministic, fixed `ts`, bounded output. See `pid.c`.
- **PWM duty update** — the Python controller's output is a duty in [0, 1];
  firmware must map that to timer compare counts with correct polarity.
- **Timer tick** — a fixed sample period is required for the discrete
  integrator (`ki * error * ts`) and derivative (`delta / ts`) to mean
  anything. A variable delay changes the effective gains.

## Known gaps (deliberately not filled in)

- No ADC calibration, sense-divider ratio, or filtering.
- No PWM polarity/resolution handling or dead-time insertion.
- No protection, soft-start, or fault states.
- No proof of timing closure or interrupt priority.
- No hardware test results.

These are not oversights to be glossed over: they are exactly the pieces
that make a real converter different from the simulation in this repository.
