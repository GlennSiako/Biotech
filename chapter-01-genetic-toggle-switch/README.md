# Chapter 1: Genetic Toggle Switch Playground

A small, interactive Python project that follows the progression of a systems-biology introduction:

1. **Single gene** – the simplest circuit: production vs. degradation.
2. **Two-gene toggle switch** – two mutually repressing genes that settle into one of two stable states.

The app is built with **Streamlit**, **Plotly**, and **SciPy** (`solve_ivp`).

## Run the app

```bash
cd chapter-01-genetic-toggle-switch
pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Run the tests

```bash
pytest
```

## Model equations

### Single gene

```
dx/dt = α - βx
```

Steady state: `x_ss = α / β`.

### Toggle switch

```
dA/dt = α_A / (1 + (B/K_B)^n_B) - β_A A + pulse_A(t)
dB/dt = α_B / (1 + (A/K_A)^n_A) - β_B B + pulse_B(t)
```

A temporary inducer pulse biases production of one gene, pushing the system from one stable state to the other.
