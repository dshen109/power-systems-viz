import dash
from dash import html, dcc

dash.register_page(__name__, path="/", name="Home")

def layout():
    return html.Div([
        html.Div([
            html.H1("Power Systems Viz", style={"color": "#4fc3f7", "margin-bottom": "8px"}),
            html.P(
                "Interactive learning site for undergraduate power systems students.",
                style={"color": "#aaaaaa"},
            ),
            html.Hr(style={"border-color": "#16213e", "margin": "24px 0"}),
            html.H3("Choose a module:"),
            html.Div([
                dcc.Link(
                    html.Div([
                        html.H3("Spine A — Stability", style={"color": "#4fc3f7", "margin": 0}),
                        html.P(
                            "Swing equation · SMIB equilibrium · Phase portrait · "
                            "Equal area · Critical clearing time · Eigenvalue damping",
                            style={"color": "#aaaaaa", "margin": "8px 0 0"},
                        ),
                    ], className="section-card", style={"cursor": "pointer"}),
                    href="/stability/swing-equation",
                ),
            ]),
        ], style={"max-width": "720px", "margin": "60px auto", "padding": "0 24px"}),
    ])
