import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_DARK = dict(plot_bgcolor="#16213e", paper_bgcolor="#1a1a2e", font=dict(color="#ffffff"))
_ACCENT = "#4fc3f7"
_ORANGE = "#ff9800"
_GREEN = "#66bb6a"
_RED = "#ff4444"


def make_swing_figure(result: dict) -> go.Figure:
    """
    Two-subplot figure: δ(t) top, Δω(t) bottom.
    result keys: t, delta, omega, delta_eq, delta_u.
    """
    t = result["t"]
    delta_deg = np.degrees(result["delta"])
    omega = result["omega"]
    delta_eq_deg = np.degrees(result["delta_eq"])
    delta_u_deg = np.degrees(result["delta_u"])

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=["Rotor angle δ(t)", "Speed deviation Δω(t)"],
        vertical_spacing=0.12,
    )

    fig.add_trace(
        go.Scatter(x=t, y=delta_deg, name="δ(t)", line=dict(color=_ACCENT, width=2)),
        row=1, col=1,
    )
    fig.add_hline(
        y=delta_eq_deg, line_dash="dash", line_color=_GREEN,
        annotation_text=f"δ_eq = {delta_eq_deg:.1f}°",
        annotation_font_color=_GREEN, row=1, col=1,
    )
    fig.add_hline(
        y=delta_u_deg, line_dash="dot", line_color=_RED,
        annotation_text=f"δ_u = {delta_u_deg:.1f}°",
        annotation_font_color=_RED, row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(x=t, y=omega, name="Δω(t)", line=dict(color=_ORANGE, width=2)),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#555555", row=2, col=1)

    fig.update_xaxes(title_text="Time (s)", row=2, col=1, gridcolor="#1e2a40")
    fig.update_yaxes(title_text="Angle (degrees)", row=1, col=1, gridcolor="#1e2a40")
    fig.update_yaxes(title_text="Δω (rad/s)", row=2, col=1, gridcolor="#1e2a40")
    fig.update_layout(**_DARK, height=480, showlegend=False, margin=dict(t=40, b=20))
    return fig


def make_pdelta_figure(Pm: float, Pe_max: float, delta_s: float | None, delta_u: float | None) -> go.Figure:
    """
    P-δ curve with equilibrium markers. Used for A2.
    """
    delta = np.linspace(0.0, np.pi, 300)
    Pe = Pe_max * np.sin(delta)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.degrees(delta), y=Pe,
        name=f"Pe_max sin(δ)  [Pe_max = {Pe_max:.2f}]",
        line=dict(color=_ACCENT, width=2),
    ))
    fig.add_hline(
        y=Pm, line_dash="dash", line_color=_ORANGE,
        annotation_text=f"Pm = {Pm:.3f} pu",
        annotation_font_color=_ORANGE,
    )

    if delta_s is not None:
        fig.add_trace(go.Scatter(
            x=[np.degrees(delta_s)], y=[Pm],
            mode="markers+text",
            name="Stable (δ_s)",
            marker=dict(color=_GREEN, size=14, symbol="circle"),
            text=[f"δ_s = {np.degrees(delta_s):.1f}°\n({delta_s:.3f} rad)"],
            textposition="top center",
            textfont=dict(color=_GREEN, size=11),
        ))
    if delta_u is not None:
        fig.add_trace(go.Scatter(
            x=[np.degrees(delta_u)], y=[Pm],
            mode="markers+text",
            name="Unstable (δ_u)",
            marker=dict(color=_RED, size=14, symbol="circle-open", line=dict(width=3, color=_RED)),
            text=[f"δ_u = {np.degrees(delta_u):.1f}°\n({delta_u:.3f} rad)"],
            textposition="top center",
            textfont=dict(color=_RED, size=11),
        ))

    fig.update_layout(
        **_DARK,
        xaxis_title="Rotor angle δ (degrees)",
        yaxis_title="Electrical power Pe (pu)",
        xaxis=dict(range=[0, 180], gridcolor="#1e2a40"),
        yaxis=dict(gridcolor="#1e2a40"),
        height=400,
        legend=dict(bgcolor="#16213e", bordercolor="#4fc3f7", borderwidth=1),
        margin=dict(t=20, b=40),
    )
    return fig


def make_rotor_figure(delta: float) -> go.Figure:
    """
    Small rotor clipart: unit circle with arrow at angle delta from vertical.
    delta = 0 means arrow points up (12 o'clock).
    """
    theta = np.linspace(0.0, 2.0 * np.pi, 120)
    fig = go.Figure()

    # Rotor circle
    fig.add_trace(go.Scatter(
        x=np.cos(theta), y=np.sin(theta),
        mode="lines", line=dict(color=_ACCENT, width=2),
        showlegend=False,
    ))
    # Rotor arm (arrow from center to rim)
    arm_x = np.sin(delta)
    arm_y = np.cos(delta)
    fig.add_trace(go.Scatter(
        x=[0, arm_x], y=[0, arm_y],
        mode="lines",
        line=dict(color=_ORANGE, width=4),
        showlegend=False,
    ))
    # Arrowhead marker at tip
    fig.add_trace(go.Scatter(
        x=[arm_x], y=[arm_y],
        mode="markers",
        marker=dict(color=_ORANGE, size=10, symbol="circle"),
        showlegend=False,
    ))

    fig.add_annotation(
        x=0, y=-1.45,
        text=f"δ = {np.degrees(delta):.1f}°",
        showarrow=False, font=dict(color="#ffffff", size=12),
        xref="x", yref="y",
    )

    fig.update_layout(
        **_DARK,
        xaxis=dict(range=[-1.5, 1.5], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[-1.7, 1.5], showgrid=False, zeroline=False,
                   showticklabels=False, scaleanchor="x", scaleratio=1),
        height=220,
        margin=dict(l=5, r=5, t=5, b=5),
    )
    return fig
