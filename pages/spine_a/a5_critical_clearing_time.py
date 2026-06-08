import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from components.nav import make_nav
from components.equation_panel import make_equation_panel
from components.notice_box import make_notice_box
from components.assumptions_box import make_assumptions_box
from solvers.stability import solve_fault_sequence, find_cct
from figures.swing_figures import make_rotor_figure
from figures.stability_figures import make_cct_figure

dash.register_page(__name__, path="/stability/critical-clearing-time", name="Critical Clearing Time")

_ROUTE = "/stability/critical-clearing-time"


def layout():
    return html.Div([
        make_nav(_ROUTE),

        html.Div([
            html.H3("Explainer Video"),
            html.Video(src="/assets/videos/a5_cct.mp4", controls=True,
                       style={"width": "100%", "border-radius": "6px", "background": "#000"}),
        ], className="section-card"),

        make_equation_panel("cct_eq"),

        html.Div([
            html.H3("Explore"),
            html.P("Slider changes debounced 300 ms.",
                   style={"color": "#888", "font-size": "0.85rem", "margin-bottom": "12px"}),
            html.Div([
                html.Div([
                    html.Div("Inertia H (MWs/MVA)", className="slider-label"),
                    dcc.Slider(id="a5-H", min=1, max=10, step=0.5, value=5,
                               marks={1: "1", 5: "5", 10: "10"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Damping D (pu)", className="slider-label"),
                    dcc.Slider(id="a5-D", min=0, max=5, step=0.1, value=0.5,
                               marks={0: "0", 2.5: "2.5", 5: "5"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Mechanical power Pm (pu)", className="slider-label"),
                    dcc.Slider(id="a5-Pm", min=0.1, max=0.9, step=0.05, value=0.5,
                               marks={0.1: "0.1", 0.5: "0.5", 0.9: "0.9"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Pre-fault Pe_max_pre (pu)", className="slider-label"),
                    dcc.Slider(id="a5-pre", min=0.5, max=2.0, step=0.1, value=1.0,
                               marks={0.5: "0.5", 1: "1", 2: "2"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Fault-on Pe_max_fault (pu)", className="slider-label"),
                    dcc.Slider(id="a5-fault", min=0, max=1.0, step=0.05, value=0.0,
                               marks={0: "0", 0.5: "0.5", 1: "1"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Post-fault Pe_max_post (pu)", className="slider-label"),
                    dcc.Slider(id="a5-post", min=0.3, max=2.0, step=0.1, value=1.0,
                               marks={0.3: "0.3", 1: "1", 2: "2"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div("Fault clearing time tc (s)", className="slider-label"),
                    dcc.Slider(id="a5-tc", min=0, max=2.0, step=0.05, value=0.2,
                               marks={0: "0", 0.5: "0.5", 1: "1", 2: "2"},
                               debounce=True, tooltip={"placement": "bottom"}),
                    html.Div(id="a5-warning", className="warning-banner", style={"display": "none"}),
                ], className="slider-panel"),

                html.Div([
                    dcc.Graph(id="a5-graph", config={"displayModeBar": False}),
                    dcc.Graph(id="a5-rotor", config={"displayModeBar": False},
                              style={"margin-top": "8px"}),
                    dcc.Store(id="a5-last-valid"),
                ], className="graph-panel"),
            ], className="explore-layout"),
        ], className="section-card"),

        make_notice_box([
            "Decrease H. Does CCT increase or decrease? Why?",
            "Increase Pm (heavier loading). How does CCT change?",
            "Set Pe_max_fault = 0 (bolted fault, maximum severity). How short must tc be?",
            "Compare the critical clearing angle from page A4 to where δ is at the CCT here.",
        ]),

        make_assumptions_box(
            "Single machine, infinite bus. Classical machine model. Fault applied at t = 0. "
            "When D > 0, CCT here exceeds the undamped EAC prediction from page A4 — "
            "damping absorbs energy and extends the stable clearing window."
        ),
    ])


@callback(
    Output("a5-graph", "figure"),
    Output("a5-rotor", "figure"),
    Output("a5-last-valid", "data"),
    Output("a5-warning", "children"),
    Output("a5-warning", "style"),
    Input("a5-H", "value"),
    Input("a5-D", "value"),
    Input("a5-Pm", "value"),
    Input("a5-pre", "value"),
    Input("a5-fault", "value"),
    Input("a5-post", "value"),
    Input("a5-tc", "value"),
    State("a5-last-valid", "data"),
)
def update_a5(H, D, Pm, Pe_max_pre, Pe_max_fault, Pe_max_post, t_clear, last_valid):
    result = solve_fault_sequence(H, D, Pm, Pe_max_pre, Pe_max_fault, Pe_max_post, t_clear)
    cct_result = find_cct(H, D, Pm, Pe_max_pre, Pe_max_fault, Pe_max_post)

    if result["warning"] and result["t"] is None:
        fig = go.Figure(last_valid) if last_valid else go.Figure()
        rotor = make_rotor_figure(0.0)
        return fig, rotor, last_valid, result["warning"], {"display": "block"}

    fig = make_cct_figure(result, t_clear, cct_result)
    current_delta = float(result["delta"][-1]) if result["delta"] is not None else 0.0
    rotor = make_rotor_figure(current_delta)
    warning = result["warning"] or ""
    warn_style = {"display": "block"} if result["warning"] else {"display": "none"}
    return fig, rotor, fig.to_dict(), warning, warn_style
