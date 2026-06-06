from dash import html

def make_notice_box(notices: list[str]) -> html.Div:
    return html.Div(
        [
            html.H3("What to Notice", style={"margin-bottom": "12px"}),
            html.Ul(
                [html.Li(n, style={"margin-bottom": "8px", "color": "#cccccc"}) for n in notices],
                style={"margin": 0, "padding-left": "20px"},
            ),
        ],
        className="section-card",
    )
