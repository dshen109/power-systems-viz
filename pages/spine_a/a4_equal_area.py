import numpy as np
import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from components.nav import make_nav
from components.equation_panel import make_equation_panel
from components.notice_box import make_notice_box
from components.assumptions_box import make_assumptions_box
from solvers.stability import compute_equal_area
from figures.stability_figures import make_equal_area_figure

dash.register_page(__name__, path="/stability/equal-area", name="Equal Area Criterion")

_ROUTE = "/stability/equal-area"

_DEFAULT_PM = 0.5
_DEFAULT_PRE = 1.0
_DEFAULT_FAULT = 0.0
_DEFAULT_POST = 1.0


def layout():
    delta_0_default = float(np.degrees(np.arcsin(_DEFAULT_PM / _DEFAULT_PRE)))
    delta_max_default = float(np.degrees(np.pi - np.arcsin(_DEFAULT_PM / _DEFAULT_POST)))

    return html.Div([
        make_nav(_ROUTE),

        html.Div([
            html.H3("Explainer Video"),
            html.Video(src="/assets/videos/a4_equal_area.mp4", controls=True,
                       style={"width": "100%", "border-radius": "6px", "background": "#000"}),
        ], className="section-card"),

        make_equation_panel("equal_area_eq"),

        html.Div([
            html.H3("Explore"),
            html.Div([
                html.Div([
                    html.Div("Mechanical power Pm (pu)", className="slider-label"),
                    dcc.Slider(id="a4-Pm", min=0.1, max=0.9, step=0.05, value=_DEFAULT_PM,
                               marks={0.1: "0.1", 0.5: "0.5", 0.9: "0.9"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Pre-fault Pe_max_pre (pu)", className="slider-label"),
                    dcc.Slider(id="a4-pre", min=0.5, max=2.0, step=0.1, value=_DEFAULT_PRE,
                               marks={0.5: "0.5", 1: "1", 2: "2"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Fault-on Pe_max_fault (pu, 0 = bolted)", className="slider-label"),
                    dcc.Slider(id="a4-fault", min=0, max=1.0, step=0.05, value=_DEFAULT_FAULT,
                               marks={0: "0", 0.5: "0.5", 1: "1"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Post-fault Pe_max_post (pu)", className="slider-label"),
                    dcc.Slider(id="a4-post", min=0.3, max=2.0, step=0.1, value=_DEFAULT_POST,
                               marks={0.3: "0.3", 1: "1", 2: "2"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Clearing angle δc (degrees)", className="slider-label"),
                    dcc.Slider(id="a4-delta_c", min=delta_0_default + 1, max=delta_max_default - 1,
                               step=1, value=60,
                               marks={int(delta_0_default + 1): "δ₀+1°",
                                      int(delta_max_default - 1): "δ_max-1°"},
                               tooltip={"placement": "bottom"}),
                    html.Div(id="a4-warning", className="warning-banner", style={"display": "none"}),
                ], className="slider-panel"),

                html.Div([
                    dcc.Graph(id="a4-graph", config={"displayModeBar": False}),
                    dcc.Store(id="a4-last-valid"),
                ], className="graph-panel"),
            ], className="explore-layout"),
        ], className="section-card"),

        make_notice_box([
            "Increase clearing angle. At what point does the machine go unstable?",
            "Reduce Pe_max_post (more line damage). How does the decelerating area shrink?",
            "Set Pe_max_fault = 0 (bolted fault). Does this maximize the accelerating area?",
            "This page gives clearing angle. Go to page A5 to find the clearing time.",
        ]),

        make_assumptions_box(
            "Single machine, infinite bus. Equal area criterion is exact for undamped (D = 0), "
            "lossless SMIB model. With damping, it is a useful approximation — see A5 for "
            "time-domain comparison. Clearing angle set directly; clearing time on next page."
        ),
    ])


@callback(
    Output("a4-graph", "figure"),
    Output("a4-last-valid", "data"),
    Output("a4-warning", "children"),
    Output("a4-warning", "style"),
    Input("a4-Pm", "value"),
    Input("a4-pre", "value"),
    Input("a4-fault", "value"),
    Input("a4-post", "value"),
    Input("a4-delta_c", "value"),
    State("a4-last-valid", "data"),
)
def update_a4(Pm, Pe_max_pre, Pe_max_fault, Pe_max_post, delta_c_deg, last_valid):
    delta_c = np.radians(delta_c_deg)
    result = compute_equal_area(Pm, Pe_max_pre, Pe_max_fault, Pe_max_post, delta_c)

    if result["warning"]:
        fig = go.Figure(last_valid) if last_valid else go.Figure()
        return fig, last_valid, result["warning"], {"display": "block"}

    fig = make_equal_area_figure(Pm, Pe_max_pre, Pe_max_fault, Pe_max_post, delta_c, result)
    return fig, fig.to_dict(), "", {"display": "none"}
