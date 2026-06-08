import numpy as np
import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from components.nav import make_nav
from components.equation_panel import make_equation_panel
from components.notice_box import make_notice_box
from components.assumptions_box import make_assumptions_box
from solvers.swing import find_smib_equilibria
from figures.swing_figures import make_pdelta_figure

dash.register_page(__name__, path="/stability/smib-equilibrium", name="SMIB Equilibrium")

_ROUTE = "/stability/smib-equilibrium"


def layout():
    return html.Div([
        make_nav(_ROUTE),

        html.Div([
            html.H3("Explainer Video"),
            html.Video(src="/assets/videos/a2_smib_equilibrium.mp4", controls=True,
                       style={"width": "100%", "border-radius": "6px", "background": "#000"}),
        ], className="section-card"),

        make_equation_panel("smib_eq"),

        html.Div([
            html.H3("Explore"),
            html.Div([
                html.Div([
                    html.Div("Mechanical power Pm (pu)", className="slider-label"),
                    dcc.Slider(id="a2-Pm", min=0, max=2.0, step=0.05, value=0.5,
                               marks={0: "0", 1: "1", 2: "2"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Transfer capacity Pe_max (pu)", className="slider-label"),
                    dcc.Slider(id="a2-Pe_max", min=0.5, max=2.0, step=0.05, value=1.0,
                               marks={0.5: "0.5", 1: "1", 2: "2"},
                               tooltip={"placement": "bottom"}),
                    html.Div(id="a2-info", style={"margin-top": "16px", "color": "#aaaaaa", "font-size": "0.9rem"}),
                    html.Div(id="a2-warning", className="warning-banner", style={"display": "none"}),
                ], className="slider-panel"),

                html.Div([
                    dcc.Graph(id="a2-graph", config={"displayModeBar": False}),
                    dcc.Store(id="a2-last-valid"),
                ], className="graph-panel"),
            ], className="explore-layout"),
        ], className="section-card"),

        make_notice_box([
            "Increase Pm toward Pe_max. What happens to the two equilibria?",
            "At Pm = Pe_max, how many equilibria exist?",
            "Increase Pe_max (stronger line). Does the stable operating angle increase or decrease for the same Pm?",
        ]),

        make_assumptions_box(
            "Single machine, infinite bus. Lossless network. "
            "No saliency (round-rotor model). Pe = Pe_max sin(δ) only."
        ),
    ])


@callback(
    Output("a2-graph", "figure"),
    Output("a2-last-valid", "data"),
    Output("a2-info", "children"),
    Output("a2-warning", "children"),
    Output("a2-warning", "style"),
    Input("a2-Pm", "value"),
    Input("a2-Pe_max", "value"),
    State("a2-last-valid", "data"),
)
def update_a2(Pm, Pe_max, last_valid):
    result = find_smib_equilibria(Pm, Pe_max)

    if result["warning"]:
        fig = go.Figure(last_valid) if last_valid else make_pdelta_figure(Pm, Pe_max, None, None)
        return fig, last_valid, "", result["warning"], {"display": "block"}

    delta_s = result["delta_s"]
    delta_u = result["delta_u"]
    info = (
        f"δ_s = {np.degrees(delta_s):.1f}° ({delta_s:.3f} rad)  |  "
        f"δ_u = {np.degrees(delta_u):.1f}° ({delta_u:.3f} rad)"
    )
    fig = make_pdelta_figure(Pm, Pe_max, delta_s, delta_u)
    return fig, fig.to_dict(), info, "", {"display": "none"}
