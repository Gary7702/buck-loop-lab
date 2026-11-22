/*
 * pid.h - PID controller state and API skeleton.
 *
 * TEMPLATE ONLY. Not compiled, not tested on hardware.
 * Mirrors src/buckloop/controller.py (PIDController).
 */
#ifndef BUCKLOOP_PID_H
#define BUCKLOOP_PID_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float kp;
    float ki;
    float kd;
    float ts;           /* sample period, seconds */
    float out_min;      /* lower output limit (duty lower bound) */
    float out_max;      /* upper output limit (duty upper bound) */
    float deriv_alpha;  /* derivative low-pass coefficient, [0, 1] */

    /* internal state */
    float integral;
    float prev_measurement;
    float filtered_deriv;
    int   initialized;
} PID;

/* Initialise gains/limits and clear state. */
void PID_Init(PID *pid, float kp, float ki, float kd, float ts,
              float out_min, float out_max, float deriv_alpha);

/* Clear only the runtime state (integrator and derivative history). */
void PID_Reset(PID *pid);

/* Compute a bounded control value (duty cycle) for one sample. */
float PID_Compute(PID *pid, float setpoint, float measurement);

#ifdef __cplusplus
}
#endif

#endif /* BUCKLOOP_PID_H */
