from scipy.integrate import solve_ivp


def single_gene_ode(t, x, alpha, beta):
    """Single-gene production and degradation.

    dx/dt = alpha - beta * x
    """
    return alpha - beta * x


def simulate(alpha, beta, x0, t_span, t_eval):
    """Simulate the single-gene ODE and return time points and concentrations."""
    sol = solve_ivp(
        single_gene_ode,
        t_span,
        [x0],
        args=(alpha, beta),
        t_eval=t_eval,
        method="RK45",
    )
    return sol.t, sol.y[0]
