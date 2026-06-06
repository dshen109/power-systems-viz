from dash import html

def make_assumptions_box(text: str) -> html.Div:
    return html.Div(
        [
            html.H3("Assumptions", style={"margin-bottom": "8px"}),
            html.P(text, style={"color": "#aaaaaa", "margin": 0, "line-height": "1.6"}),
        ],
        className="section-card",
        style={"margin-bottom": "40px"},
    )
