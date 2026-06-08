import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from components.nav import make_nav
from components.equation_panel import make_equation_panel
from components.notice_box import make_notice_box
from components.assumptions_box import make_assumptions_box
from solvers.swing import SwingParams, solve_swing
from figures.swing_figures import make_swing_figure, make_rotor_figure

dash.register_page(__name__, path="/stability/swing-equation", name="Swing Equation")

_ROUTE = "/stability/swing-equation"


def layout():
    return html.Div([
        make_nav(_ROUTE),

        html.Div([
            html.H3("Explainer Video", style={"margin-bottom": "10px"}),
            html.Video(
                src="/assets/videos/a1_swing_equation.mp4",
                controls=True,
                style={"width": "100%", "border-radius": "6px", "background": "#000"},
            ),
            html.P(
                "Video not yet available — Manim scene to be rendered and committed.",
                style={"color": "#666", "font-size": "0.8rem", "margin-top": "6px"},
                id="a1-video-placeholder",
            ),
        ], className="section-card"),

        make_equation_panel("swing_eq"),

        html.Div([
            html.H3("Explore", style={"margin-bottom": "16px"}),
            html.Div([
                html.Div([
                    html.Div("Inertia H (MWs/MVA)", className="slider-label"),
                    dcc.Slider(id="a1-H", min=1, max=10, step=0.5, value=5,
                               marks={1: "1", 5: "5", 10: "10"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Damping D (pu)", className="slider-label"),
                    dcc.Slider(id="a1-D", min=0, max=5, step=0.1, value=0.5,
                               marks={0: "0", 2.5: "2.5", 5: "5"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Mechanical power Pm (pu)", className="slider-label"),
                    dcc.Slider(id="a1-Pm", min=0, max=0.95, step=0.05, value=0.5,
                               marks={0: "0", 0.5: "0.5", 0.95: "0.95"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Initial perturbation δ₀ (rad)", className="slider-label"),
                    dcc.Slider(id="a1-delta0", min=0.01, max=0.5, step=0.01, value=0.1,
                               marks={0.01: "0.01", 0.25: "0.25", 0.5: "0.5"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Simulation time (s)", className="slider-label"),
                    dcc.Slider(id="a1-tend", min=5, max=30, step=1, value=10,
                               marks={5: "5", 15: "15", 30: "30"},
                               tooltip={"placement": "bottom"}),
                    html.Div(id="a1-warning", className="warning-banner",
                             style={"display": "none"}),
                ], className="slider-panel"),

                html.Div([
                    html.Div([
                        dcc.Graph(id="a1-graph", config={"displayModeBar": False}),
                        dcc.Graph(id="a1-rotor", config={"displayModeBar": False},
                                  style={"margin-top": "8px"}),
                    ]),
                    dcc.Store(id="a1-last-valid"),
                ], className="graph-panel"),
            ], className="explore-layout"),
        ], className="section-card"),

        make_notice_box([
            "Increase H. Does the oscillation frequency increase or decrease? Why?",
            "Set D = 0. Does the system return to equilibrium?",
            "Increase Pm closer to 1.0. Does the equilibrium shift? Does the system still settle?",
        ]),

        make_assumptions_box(
            "Single machine, infinite bus. Pe_max = 1 pu fixed. "
            "Classical machine model (no AVR, no governor). "
            "Angles in radians, frequency in rad/s."
        ),
    ])


@callback(
    Output("a1-graph", "figure"),
    Output("a1-rotor", "figure"),
    Output("a1-last-valid", "data"),
    Output("a1-warning", "children"),
    Output("a1-warning", "style"),
    Input("a1-H", "value"),
    Input("a1-D", "value"),
    Input("a1-Pm", "value"),
    Input("a1-delta0", "value"),
    Input("a1-tend", "value"),
    State("a1-last-valid", "data"),
)
def update_a1(H, D, Pm, delta_0, t_end, last_valid):
    params = SwingParams(
        H=H, D=D, Pm=Pm, Pe_max=1.0, t_end=t_end, delta_0=delta_0
    )
    result = solve_swing(params)

    if result["warning"]:
        fig = go.Figure(last_valid) if last_valid else go.Figure()
        rotor = make_rotor_figure(0.0)
        return (
            fig, rotor, last_valid,
            result["warning"],
            {"display": "block"},
        )

    fig = make_swing_figure(result)
    current_delta = float(result["delta"][-1]) if result["delta"] is not None else 0.0
    rotor = make_rotor_figure(current_delta)
    fig_dict = fig.to_dict()
    return fig, rotor, fig_dict, "", {"display": "none"}
