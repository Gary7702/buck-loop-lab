/*
 * pid.c - PID controller skeleton mirroring src/buckloop/controller.py.
 *
 * TEMPLATE ONLY. Not compiled, not tested on hardware.
 * Derivative-on-measurement + first-order filtered derivative +
 * conditional-integration anti-windup + output clamp.
 */
#include "pid.h"

static float clampf(float value, float low, float high)
{
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }
    return value;
}

void PID_Init(PID *pid, float kp, float ki, float kd, float ts,
              float out_min, float out_max, float deriv_alpha)
{
    pid->kp = kp;
    pid->ki = ki;
    pid->kd = kd;
    pid->ts = ts;
    pid->out_min = out_min;
    pid->out_max = out_max;
    pid->deriv_alpha = deriv_alpha;
    PID_Reset(pid);
}

void PID_Reset(PID *pid)
{
    pid->integral = 0.0f;
    pid->prev_measurement = 0.0f;
    pid->filtered_deriv = 0.0f;
    pid->initialized = 0;
}

float PID_Compute(PID *pid, float setpoint, float measurement)
{
    float error = setpoint - measurement;
    float proportional, derivative, integral_candidate, tentative;
    float integral, output;

    if (!pid->initialized) {
        pid->prev_measurement = measurement;
        pid->filtered_deriv = 0.0f;
        pid->initialized = 1;
    } else {
        float raw_deriv = (measurement - pid->prev_measurement) / pid->ts;
        pid->filtered_deriv = pid->deriv_alpha * pid->filtered_deriv
                            + (1.0f - pid->deriv_alpha) * raw_deriv;
        pid->prev_measurement = measurement;
    }

    proportional = pid->kp * error;
    derivative = -pid->kd * pid->filtered_deriv;   /* derivative on measurement */
    integral_candidate = pid->integral + pid->ki * error * pid->ts;

    tentative = proportional + integral_candidate + derivative;
    if (((tentative > pid->out_max) && (error > 0.0f)) ||
        ((tentative < pid->out_min) && (error < 0.0f))) {
        integral = pid->integral;                   /* freeze: anti-windup */
    } else {
        integral = integral_candidate;
    }
    pid->integral = integral;

    output = proportional + integral + derivative;
    return clampf(output, pid->out_min, pid->out_max);
}
