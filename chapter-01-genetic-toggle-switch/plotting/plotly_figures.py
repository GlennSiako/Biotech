import plotly.graph_objects as go


def plot_single_gene(t, x):
    """Return a Plotly line chart for a single-gene simulation."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=t,
            y=x,
            mode="lines",
            name="Protein concentration",
            line=dict(width=3),
        )
    )
    fig.update_layout(
        title="Single Gene: Production vs. Degradation",
        xaxis_title="Time",
        yaxis_title="Concentration",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_toggle_time(t, a, b):
    """Return a Plotly line chart of A and B concentrations over time."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=t,
            y=a,
            mode="lines",
            name="Gene A",
            line=dict(width=3, color="#1f77b4"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=b,
            mode="lines",
            name="Gene B",
            line=dict(width=3, color="#ff7f0e"),
        )
    )
    fig.update_layout(
        title="Toggle Switch Dynamics",
        xaxis_title="Time",
        yaxis_title="Concentration",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(x=0.02, y=0.98),
    )
    return fig


def plot_phase_portrait(a, b):
    """Return a Plotly phase-portrait figure (A vs. B)."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=a,
            y=b,
            mode="lines",
            name="Trajectory",
            line=dict(width=3, color="#2ca02c"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[a[0]],
            y=[b[0]],
            mode="markers",
            name="Start",
            marker=dict(size=12, color="#d62728"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[a[-1]],
            y=[b[-1]],
            mode="markers",
            name="End",
            marker=dict(size=12, color="#9467bd"),
        )
    )
    fig.update_layout(
        title="Phase Portrait: A vs. B",
        xaxis_title="Gene A concentration",
        yaxis_title="Gene B concentration",
        template="plotly_white",
        hovermode="closest",
        legend=dict(x=0.02, y=0.98),
    )
    return fig
