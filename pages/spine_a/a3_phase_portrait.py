import time
import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from components.nav import make_nav
from components.equation_panel import make_equation_panel
from components.notice_box import make_notice_box
from components.assumptions_box import make_assumptions_box
from solvers.stability import compute_phase_portrait
from figures.stability_figures import make_phase_portrait_figure

dash.register_page(__name__, path="/stability/phase-portrait", name="Phase Portrait")

_ROUTE = "/stability/phase-portrait"


def layout():
    return html.Div([
        make_nav(_ROUTE),

        html.Div([
            html.H3("Explainer Video"),
            html.Video(src="/assets/videos/a3_phase_portrait.mp4", controls=True,
                       style={"width": "100%", "border-radius": "6px", "background": "#000"}),
        ], className="section-card"),

        make_equation_panel("phase_eq"),

        html.Div([
            html.H3("Explore"),
            html.P("Note: slider changes debounced 500 ms. Fine grid may take up to 5 s.",
                   style={"color": "#888", "font-size": "0.85rem", "margin-bottom": "12px"}),
            html.Div([
                html.Div([
                    html.Div("Inertia H (MWs/MVA)", className="slider-label"),
                    dcc.Slider(id="a3-H", min=1, max=10, step=0.5, value=5,
                               marks={1: "1", 5: "5", 10: "10"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Damping D (pu)", className="slider-label"),
                    dcc.Slider(id="a3-D", min=0, max=5, step=0.1, value=0.5,
                               marks={0: "0", 2.5: "2.5", 5: "5"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Mechanical power Pm (pu)", className="slider-label"),
                    dcc.Slider(id="a3-Pm", min=0, max=0.95, step=0.05, value=0.5,
                               marks={0: "0", 0.5: "0.5", 0.95: "0.95"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Transfer capacity Pe_max (pu)", className="slider-label"),
                    dcc.Slider(id="a3-Pe_max", min=0.5, max=2.0, step=0.1, value=1.0,
                               marks={0.5: "0.5", 1: "1", 2: "2"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Grid density", className="slider-label"),
                    dcc.RadioItems(
                        id="a3-density",
                        options=[
                            {"label": " Coarse (fast)", "value": "coarse"},
                            {"label": " Medium", "value": "medium"},
                            {"label": " Fine (slow)", "value": "fine"},
                        ],
                        value="coarse",
                        style={"color": "#ccc", "margin-top": "6px"},
                        labelStyle={"display": "block", "margin-bottom": "4px"},
                    ),
                    html.Div(id="a3-warning", className="warning-banner", style={"display": "none"}),
                ], className="slider-panel"),

                html.Div([
                    dcc.Graph(id="a3-graph", config={"displayModeBar": False}),
                    dcc.Store(id="a3-last-valid"),
                ], className="graph-panel"),
            ], className="explore-layout"),
        ], className="section-card"),

        make_notice_box([
            "Set D = 0. Are trajectories closed loops or spirals?",
            "Increase D. What changes near the stable equilibrium?",
            "Move Pm closer to Pe_max. What happens to the stable region size?",
        ]),

        make_assumptions_box(
            "Single machine, infinite bus. Classical machine model. "
            "Stability boundary shown is approximate — based on trajectory outcomes, "
            "not exact separatrix computation."
        ),
    ])


@callback(
    Output("a3-graph", "figure"),
    Output("a3-last-valid", "data"),
    Output("a3-warning", "children"),
    Output("a3-warning", "style"),
    Input("a3-H", "value"),
    Input("a3-D", "value"),
    Input("a3-Pm", "value"),
    Input("a3-Pe_max", "value"),
    Input("a3-density", "value"),
    State("a3-last-valid", "data"),
)
def update_a3(H, D, Pm, Pe_max, density, last_valid):
    t0 = time.time()
    result = compute_phase_portrait(H, D, Pm, Pe_max, density)

    if result["warning"]:
        fig = go.Figure(last_valid) if last_valid else go.Figure()
        return fig, last_valid, result["warning"], {"display": "block"}

    elapsed = time.time() - t0
    warning_msg = ""
    warn_style = {"display": "none"}

    if elapsed > 5.0 and density == "fine":
        result = compute_phase_portrait(H, D, Pm, Pe_max, "coarse")
        warning_msg = "Grid reduced to coarse for performance (fine exceeded 5 s)."
        warn_style = {"display": "block"}

    fig = make_phase_portrait_figure(result)
    return fig, fig.to_dict(), warning_msg, warn_style
