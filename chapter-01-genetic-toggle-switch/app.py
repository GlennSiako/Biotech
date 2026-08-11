import streamlit as st
import numpy as np

from models.single_gene import simulate as simulate_single
from models.toggle_switch import simulate as simulate_toggle, make_pulse
from plotting.plotly_figures import (
    plot_single_gene,
    plot_toggle_time,
    plot_phase_portrait,
)

st.set_page_config(page_title="Genetic Toggle Switch Playground", layout="wide")

st.title("Chapter 1: Genetic Toggle Switch Playground")

tab_single, tab_toggle = st.tabs(["Single Gene", "Toggle Switch"])

with tab_single:
    st.header("Single Gene: Production vs. Degradation")
    st.markdown(r"The simplest model: $dx/dt = \alpha - \beta x$, with steady state $\alpha/\beta$.")

    col_inputs, col_plot = st.columns([1, 3])
    with col_inputs:
        alpha = st.slider("Production rate α", 0.1, 5.0, 2.0, 0.1)
        beta = st.slider("Degradation rate β", 0.1, 2.0, 0.5, 0.05)
        x0 = st.slider("Initial concentration", 0.0, 10.0, 0.0, 0.1)
        t_max = st.slider("Simulation time", 10.0, 100.0, 50.0, 5.0)

    with col_plot:
        t_eval = np.linspace(0, t_max, 500)
        t, x = simulate_single(alpha, beta, x0, (0, t_max), t_eval)
        fig = plot_single_gene(t, x)
        st.plotly_chart(fig, use_container_width=True)

        col_metric1, col_metric2 = st.columns(2)
        col_metric1.metric("Predicted steady state", f"{alpha / beta:.2f}")
        col_metric2.metric("Final simulated concentration", f"{x[-1]:.2f}")

with tab_toggle:
    st.header("Two-Gene Toggle Switch")
    st.markdown(
        r"""
        Two mutually repressing genes:

        $$
        \frac{dA}{dt} = \frac{\alpha_A}{1 + (B/K_B)^{n_B}} - \beta_A A + \text{pulse}_A(t)
        $$

        $$
        \frac{dB}{dt} = \frac{\alpha_B}{1 + (A/K_A)^{n_A}} - \beta_B B + \text{pulse}_B(t)
        $$

        Use the buttons to apply a temporary inducer pulse and watch the system switch states.
        """
    )

    col_inputs, col_plot = st.columns([1, 3])
    with col_inputs:
        st.subheader("Production & degradation")
        alpha_a = st.slider("α_A", 0.1, 5.0, 2.0, 0.1, key="alpha_a")
        alpha_b = st.slider("α_B", 0.1, 5.0, 2.0, 0.1, key="alpha_b")
        beta_a = st.slider("β_A", 0.1, 2.0, 1.0, 0.05, key="beta_a")
        beta_b = st.slider("β_B", 0.1, 2.0, 1.0, 0.05, key="beta_b")

        st.subheader("Repression")
        k_a = st.slider("K_A (repression threshold)", 0.1, 3.0, 1.0, 0.1, key="k_a")
        k_b = st.slider("K_B (repression threshold)", 0.1, 3.0, 1.0, 0.1, key="k_b")
        n_a = st.slider("n_A (Hill coefficient)", 1.0, 6.0, 2.0, 0.5, key="n_a")
        n_b = st.slider("n_B (Hill coefficient)", 1.0, 6.0, 2.0, 0.5, key="n_b")

        st.subheader("Initial conditions")
        a0 = st.slider("Initial A", 0.0, 5.0, 0.1, 0.05, key="a0")
        b0 = st.slider("Initial B", 0.0, 5.0, 2.0, 0.05, key="b0")

        st.subheader("Inducer pulse")
        inducer_start = st.slider("Start time", 0.0, 50.0, 10.0, 1.0)
        inducer_duration = st.slider("Duration", 1.0, 20.0, 5.0, 1.0)
        inducer_strength = st.slider("Strength", 0.0, 5.0, 2.0, 0.1)

        apply_a = st.button("Apply Inducer A", key="inducer_a")
        apply_b = st.button("Apply Inducer B", key="inducer_b")

        t_max_toggle = st.slider("Simulation time", 10.0, 100.0, 50.0, 5.0, key="t_max_toggle")

    with col_plot:
        params = (alpha_a, alpha_b, beta_a, beta_b, k_a, k_b, n_a, n_b)
        pulse_a = make_pulse(inducer_start, inducer_duration, inducer_strength) if apply_a else None
        pulse_b = make_pulse(inducer_start, inducer_duration, inducer_strength) if apply_b else None

        t_eval = np.linspace(0, t_max_toggle, 500)
        t, a, b = simulate_toggle(params, [a0, b0], (0, t_max_toggle), t_eval, pulse_a, pulse_b)

        st.plotly_chart(plot_toggle_time(t, a, b), use_container_width=True)
        st.plotly_chart(plot_phase_portrait(a, b), use_container_width=True)

        col_metric1, col_metric2 = st.columns(2)
        col_metric1.metric("Final A", f"{a[-1]:.2f}")
        col_metric2.metric("Final B", f"{b[-1]:.2f}")
