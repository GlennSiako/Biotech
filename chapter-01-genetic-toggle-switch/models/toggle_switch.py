from scipy.integrate import solve_ivp


def make_pulse(start, duration, strength):
    """Return a function that applies a rectangular pulse during [start, start+duration]."""
    def pulse(t):
        return strength if start <= t <= start + duration else 0.0
    return pulse


def toggle_switch_ode(
    t,
    y,
    alpha_a,
    alpha_b,
    beta_a,
    beta_b,
    k_a,
    k_b,
    n_a,
    n_b,
    pulse_a,
    pulse_b,
):
    """Two-gene mutual repression toggle switch.

    dA/dt = alpha_A / (1 + (B/K_B)^n_B) - beta_A * A + pulse_A(t)
    dB/dt = alpha_B / (1 + (A/K_A)^n_A) - beta_B * B + pulse_B(t)
    """
    a, b = y
    da_dt = alpha_a / (1 + (b / k_b) ** n_b) - beta_a * a + pulse_a(t)
    db_dt = alpha_b / (1 + (a / k_a) ** n_a) - beta_b * b + pulse_b(t)
    return [da_dt, db_dt]


def simulate(params, y0, t_span, t_eval, pulse_a=None, pulse_b=None):
    """Simulate the toggle switch and return time points plus A and B concentrations."""
    pulse_a = pulse_a or (lambda t: 0.0)
    pulse_b = pulse_b or (lambda t: 0.0)
    args = (*params, pulse_a, pulse_b)
    sol = solve_ivp(
        toggle_switch_ode,
        t_span,
        y0,
        args=args,
        t_eval=t_eval,
        method="RK45",
    )
    return sol.t, sol.y[0], sol.y[1]
