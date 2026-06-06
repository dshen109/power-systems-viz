import yaml
from dash import html
import dash_katex

_EQUATIONS = None

def _load_equations():
    global _EQUATIONS
    if _EQUATIONS is None:
        with open("content/equations.yaml") as f:
            _EQUATIONS = yaml.safe_load(f)
    return _EQUATIONS

def make_equation_panel(equation_key: str) -> html.Div:
    eqs = _load_equations()
    entry = eqs.get(equation_key, {})
    latex = entry.get("latex", "")
    gloss = entry.get("gloss", "")

    return html.Div(
        [
            html.H3("Key Equation", style={"margin-bottom": "12px"}),
            html.Div(
                dash_katex.DashKatex(
                    expression=latex,
                    displayMode=True,
                ),
                style={
                    "background": "#0d0d1a",
                    "border": "1px solid #16213e",
                    "border-radius": "6px",
                    "padding": "16px 20px",
                    "overflow-x": "auto",
                    "margin-bottom": "12px",
                    "color": "#ffffff",
                    "font-size": "1.1rem",
                },
            ),
            html.P(gloss, style={"color": "#cccccc", "line-height": "1.6", "margin": 0}),
        ],
        className="section-card",
    )
