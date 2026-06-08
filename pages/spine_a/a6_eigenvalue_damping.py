import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from components.nav import make_nav
from components.equation_panel import make_equation_panel
from components.notice_box import make_notice_box
from components.assumptions_box import make_assumptions_box
from solvers.stability import compute_eigenvalues
from figures.stability_figures import make_eigenvalue_figure

dash.register_page(__name__, path="/stability/eigenvalue-damping", name="Eigenvalue Damping")

_ROUTE = "/stability/eigenvalue-damping"


def layout():
    return html.Div([
        make_nav(_ROUTE),

        html.Div([
            html.H3("Explainer Video"),
            html.Video(src="/assets/videos/a6_eigenvalue.mp4", controls=True,
                       style={"width": "100%", "border-radius": "6px", "background": "#000"}),
        ], className="section-card"),

        make_equation_panel("eigenvalue_eq"),

        html.Div([
            html.H3("Explore"),
            html.Div([
                html.Div([
                    html.Div("Inertia H (MWs/MVA)", className="slider-label"),
                    dcc.Slider(id="a6-H", min=1, max=10, step=0.5, value=5,
                               marks={1: "1", 5: "5", 10: "10"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Damping D (pu)", className="slider-label"),
                    dcc.Slider(id="a6-D", min=0, max=5, step=0.1, value=0.5,
                               marks={0: "0", 2.5: "2.5", 5: "5"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Mechanical power Pm (pu)", className="slider-label"),
                    dcc.Slider(id="a6-Pm", min=0, max=0.95, step=0.05, value=0.5,
                               marks={0: "0", 0.5: "0.5", 0.95: "0.95"},
                               tooltip={"placement": "bottom"}),
                    html.Div("Transfer capacity Pe_max (pu)", className="slider-label"),
                    dcc.Slider(id="a6-Pe_max", min=0.5, max=2.0, step=0.1, value=1.0,
                               marks={0.5: "0.5", 1: "1", 2: "2"},
                               tooltip={"placement": "bottom"}),
                    html.Div(id="a6-warning", className="warning-banner", style={"display": "none"}),
                    html.P(
                        "This analysis applies only to small perturbations around the operating "
                        "point. For large disturbances, return to pages A3–A5.",
                        style={"color": "#888", "font-size": "0.82rem", "margin-top": "16px"},
                    ),
                ], className="slider-panel"),

                html.Div([
                    dcc.Graph(id="a6-graph", config={"displayModeBar": False}),
                    dcc.Store(id="a6-last-valid"),
                ], className="graph-panel"),
            ], className="explore-layout"),
        ], className="section-card"),

        make_notice_box([
            "Increase D. Where do the eigenvalues move?",
            "Set D = 0. Where are the eigenvalues? What does this mean for oscillations?",
            "Increase Pm toward Pe_max. Ks decreases. What happens to eigenvalue positions?",
            "At what value of Pm does Ks = 0? What are the eigenvalues then?",
        ]),

        make_assumptions_box(
            "Single machine, infinite bus. Classical machine model — no exciter, no governor, "
            "no power system stabilizer. Linearization valid only near the operating point. "
            "Results do not generalize to multi-machine systems without further analysis."
        ),
    ])


@callback(
    Output("a6-graph", "figure"),
    Output("a6-last-valid", "data"),
    Output("a6-warning", "children"),
    Output("a6-warning", "style"),
    Input("a6-H", "value"),
    Input("a6-D", "value"),
    Input("a6-Pm", "value"),
    Input("a6-Pe_max", "value"),
    State("a6-last-valid", "data"),
)
def update_a6(H, D, Pm, Pe_max, last_valid):
    result = compute_eigenvalues(H, D, Pm, Pe_max)

    if result["warning"]:
        fig = go.Figure(last_valid) if last_valid else go.Figure()
        return fig, last_valid, result["warning"], {"display": "block"}

    fig = make_eigenvalue_figure(result)
    return fig, fig.to_dict(), "", {"display": "none"}
