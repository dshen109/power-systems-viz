import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_DARK = dict(plot_bgcolor="#16213e", paper_bgcolor="#1a1a2e", font=dict(color="#ffffff"))
_ACCENT = "#4fc3f7"
_ORANGE = "#ff9800"
_GREEN = "#66bb6a"
_RED = "#ff4444"
_PURPLE = "#ce93d8"


def make_phase_portrait_figure(result: dict) -> go.Figure:
    fig = go.Figure()

    first_stable = True
    first_unstable = True
    for traj in result["trajectories"]:
        color = _ACCENT if traj["stable"] else _RED
        showlegend = (first_stable and traj["stable"]) or (first_unstable and not traj["stable"])
        name = ("Stable" if traj["stable"] else "Unstable") if showlegend else None
        if traj["stable"]:
            first_stable = False
        else:
            first_unstable = False

        fig.add_trace(go.Scatter(
            x=np.degrees(traj["delta"]),
            y=traj["omega"],
            mode="lines",
            line=dict(color=color, width=0.7),
            opacity=0.7,
            name=name,
            showlegend=showlegend,
        ))

    if result["delta_s"] is not None:
        fig.add_trace(go.Scatter(
            x=[np.degrees(result["delta_s"])], y=[0.0],
            mode="markers", name="Stable eq.",
            marker=dict(color=_GREEN, size=12, symbol="circle"),
        ))
    if result["delta_u"] is not None:
        fig.add_trace(go.Scatter(
            x=[np.degrees(result["delta_u"])], y=[0.0],
            mode="markers", name="Unstable eq.",
            marker=dict(color=_RED, size=12, symbol="x", line=dict(width=3, color=_RED)),
        ))

    fig.add_annotation(
        x=0.01, y=-0.1, xref="paper", yref="paper",
        text="Boundary is approximate — based on trajectory outcomes, not exact separatrix computation.",
        showarrow=False, font=dict(size=10, color="#888888"), align="left",
    )

    fig.update_layout(
        **_DARK,
        xaxis_title="Rotor angle δ (degrees)",
        yaxis_title="Speed deviation Δω (rad/s)",
        xaxis=dict(gridcolor="#1e2a40"),
        yaxis=dict(gridcolor="#1e2a40"),
        height=520,
        legend=dict(bgcolor="#16213e", bordercolor="#4fc3f7", borderwidth=1),
        margin=dict(t=20, b=40),
    )
    return fig


def make_equal_area_figure(
    Pm: float, Pe_max_pre: float, Pe_max_fault: float,
    Pe_max_post: float, delta_c: float, result: dict,
) -> go.Figure:
    delta = np.linspace(0.0, np.pi, 300)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=np.degrees(delta), y=Pe_max_pre * np.sin(delta),
        name=f"Pre-fault (Pe_max = {Pe_max_pre:.2f})",
        line=dict(color=_ACCENT, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=np.degrees(delta), y=Pe_max_fault * np.sin(delta),
        name=f"Fault-on (Pe_max = {Pe_max_fault:.2f})",
        line=dict(color=_ORANGE, width=2, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=np.degrees(delta), y=Pe_max_post * np.sin(delta),
        name=f"Post-fault (Pe_max = {Pe_max_post:.2f})",
        line=dict(color=_GREEN, width=2),
    ))

    fig.add_hline(y=Pm, line_dash="dot", line_color="white",
                  annotation_text=f"Pm = {Pm:.2f}", annotation_font_color="white")

    delta_0 = result["delta_0"]
    delta_max = result["delta_max"]

    d_acc = np.linspace(delta_0, delta_c, 80)
    fig.add_trace(go.Scatter(
        x=np.concatenate([np.degrees(d_acc), np.degrees(d_acc[::-1])]),
        y=np.concatenate([np.full_like(d_acc, Pm), Pe_max_fault * np.sin(d_acc[::-1])]),
        fill="toself", fillcolor="rgba(255,68,68,0.25)", line=dict(width=0),
        name=f"A_accel = {result['A_accel']:.4f}",
    ))

    d_dec = np.linspace(delta_c, delta_max, 80)
    fig.add_trace(go.Scatter(
        x=np.concatenate([np.degrees(d_dec), np.degrees(d_dec[::-1])]),
        y=np.concatenate([Pe_max_post * np.sin(d_dec), np.full_like(d_dec, Pm)[::-1]]),
        fill="toself", fillcolor="rgba(102,187,106,0.25)", line=dict(width=0),
        name=f"A_decel = {result['A_decel']:.4f}",
    ))

    label = "STABLE" if result["stable"] else "UNSTABLE"
    label_color = _GREEN if result["stable"] else _RED
    fig.add_annotation(
        x=0.85, y=0.88, xref="paper", yref="paper",
        text=f"<b>{label}</b>", font=dict(size=22, color=label_color),
        showarrow=False, bgcolor="#16213e", bordercolor=label_color, borderwidth=2, borderpad=6,
    )

    fig.update_layout(
        **_DARK,
        xaxis_title="Rotor angle δ (degrees)", yaxis_title="Power (pu)",
        xaxis=dict(range=[0, 180], gridcolor="#1e2a40"),
        yaxis=dict(gridcolor="#1e2a40"),
        height=460,
        legend=dict(bgcolor="#16213e", bordercolor="#4fc3f7", borderwidth=1, font=dict(size=11)),
        margin=dict(t=20, b=40),
    )
    return fig


def make_cct_figure(result: dict, t_clear: float, cct_result: dict) -> go.Figure:
    t = result["t"]
    delta_deg = np.degrees(result["delta"])
    t_clear_end = result["fault_period"][1]
    delta_u_deg = np.degrees(result["delta_u_post"])

    fig = go.Figure()

    fig.add_vrect(
        x0=0.0, x1=t_clear_end, fillcolor="rgba(255,255,255,0.05)",
        layer="below", line_width=0,
        annotation_text="Fault on", annotation_position="top left",
        annotation_font_color="#aaaaaa",
    )

    fig.add_trace(go.Scatter(x=t, y=delta_deg, name="δ(t)", line=dict(color=_ACCENT, width=2)))

    fig.add_hline(y=delta_u_deg, line_dash="dot", line_color=_RED,
                  annotation_text=f"δ_u_post = {delta_u_deg:.1f}°", annotation_font_color=_RED)

    fig.add_vline(x=t_clear_end, line_dash="dash", line_color=_ORANGE,
                  annotation_text=f"tc = {t_clear_end:.3f} s", annotation_font_color=_ORANGE)

    status = "STABLE" if result["stable"] else "UNSTABLE"
    status_color = _GREEN if result["stable"] else _RED
    fig.add_annotation(
        x=0.75, y=0.92, xref="paper", yref="paper",
        text=f"<b>{status}</b>", font=dict(size=18, color=status_color),
        showarrow=False, bgcolor="#16213e", bordercolor=status_color, borderwidth=2, borderpad=5,
    )

    if cct_result.get("cct") is not None:
        cct_val = cct_result["cct"]
        cct_label = f"Est. CCT ≈ {cct_val:.3f} s"
        if not cct_result.get("converged", True):
            cct_label += " (not converged)"
        fig.add_annotation(
            x=0.01, y=0.07, xref="paper", yref="paper",
            text=cct_label, showarrow=False, font=dict(color="#aaaaaa", size=11), align="left",
        )

    fig.update_layout(
        **_DARK,
        xaxis_title="Time (s)", yaxis_title="Rotor angle δ (degrees)",
        xaxis=dict(gridcolor="#1e2a40"), yaxis=dict(gridcolor="#1e2a40"),
        height=420, showlegend=False, margin=dict(t=20, b=40),
    )
    return fig


def make_eigenvalue_figure(result: dict) -> go.Figure:
    fig = make_subplots(
        rows=1, cols=2, column_widths=[0.7, 0.3],
        subplot_titles=["Eigenvalue locations (complex plane)", "Damping ratio ζ"],
    )

    eigenvalues = result["eigenvalues"]
    zeta = result["zeta"]
    omega_n = result["omega_n"]

    max_imag = max(abs(lam.imag) for lam in eigenvalues) * 1.4 + 0.5
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[-max_imag, max_imag],
        mode="lines", line=dict(color="#444444", width=1, dash="dash"),
        showlegend=False,
    ), row=1, col=1)

    for lam in eigenvalues:
        fig.add_trace(go.Scatter(
            x=[lam.real], y=[lam.imag],
            mode="markers+text",
            marker=dict(color=_ACCENT, size=14, symbol="circle"),
            text=[f"σ={lam.real:.3f}<br>ωd={abs(lam.imag):.3f}"],
            textposition="top right",
            textfont=dict(color="#cccccc", size=10),
            showlegend=False,
        ), row=1, col=1)

    fig.add_annotation(
        x=0.02, y=0.05, xref="paper", yref="paper",
        text=f"ζ = {zeta:.3f} | ωn = {omega_n:.3f} rad/s | Ks = {result['Ks']:.4f}",
        showarrow=False, font=dict(size=11, color="#aaaaaa"), align="left",
    )

    bar_color = _RED if zeta < 0.05 else (_ORANGE if zeta < 0.1 else _GREEN)

    fig.add_trace(go.Bar(
        x=["ζ"], y=[min(zeta, 1.0)],
        marker_color=bar_color,
        text=[f"{zeta:.3f}"], textposition="outside",
        textfont=dict(color="white"), showlegend=False,
    ), row=1, col=2)

    fig.add_hline(y=0.05, line_dash="dot", line_color="#888888",
                  annotation_text="0.05", annotation_font_color="#888888", row=1, col=2)
    fig.add_hline(y=0.1, line_dash="dot", line_color="#888888",
                  annotation_text="0.10", annotation_font_color="#888888", row=1, col=2)

    fig.update_xaxes(title_text="Real part (σ)", gridcolor="#1e2a40", row=1, col=1)
    fig.update_yaxes(title_text="Imaginary part (ωd)", gridcolor="#1e2a40", row=1, col=1)
    fig.update_yaxes(title_text="Damping ratio", range=[0, max(zeta * 1.3, 0.3)],
                     gridcolor="#1e2a40", row=1, col=2)

    fig.update_layout(**_DARK, height=440, margin=dict(t=40, b=40))
    return fig
