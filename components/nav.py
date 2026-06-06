import yaml
from dash import html, dcc

_CONCEPTS = None

def _load_concepts():
    global _CONCEPTS
    if _CONCEPTS is None:
        with open("content/concepts.yaml") as f:
            _CONCEPTS = yaml.safe_load(f)
    return _CONCEPTS

def _get_nav_context(current_route: str) -> dict:
    data = _load_concepts()
    for spine in data["spines"]:
        pages = spine["pages"]
        for i, page in enumerate(pages):
            if page["route"] == current_route:
                return {
                    "spine_id": spine["id"],
                    "spine_name": spine["name"],
                    "current_idx": i,
                    "total": len(pages),
                    "title": page["title"],
                    "prev": pages[i - 1] if i > 0 else None,
                    "next": pages[i + 1] if i < len(pages) - 1 else None,
                }
    return {}

def make_nav(current_route: str) -> html.Div:
    ctx = _get_nav_context(current_route)
    if not ctx:
        return html.Div()

    progress_pct = (ctx["current_idx"] + 1) / ctx["total"] * 100

    prev_link = (
        dcc.Link(
            f"← {ctx['prev']['title']}",
            href=ctx["prev"]["route"],
            style={"color": "#4fc3f7"},
        )
        if ctx["prev"]
        else html.Span("")
    )
    next_link = (
        dcc.Link(
            f"{ctx['next']['title']} →",
            href=ctx["next"]["route"],
            style={"color": "#4fc3f7"},
        )
        if ctx["next"]
        else html.Span("")
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        f"Spine {ctx['spine_id']}: {ctx['spine_name']}",
                        style={"font-weight": "600", "color": "#4fc3f7"},
                    ),
                    html.Span(
                        f"{ctx['current_idx'] + 1} of {ctx['total']}",
                        style={"color": "#aaaaaa"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "space-between",
                    "padding": "12px 24px 8px",
                },
            ),
            html.Div(
                html.Div(
                    style={"width": f"{progress_pct}%", "height": "4px", "background": "#4fc3f7"}
                ),
                className="progress-bar-track",
                style={"margin": "0 24px"},
            ),
            html.Div(
                [prev_link, next_link],
                style={
                    "display": "flex",
                    "justify-content": "space-between",
                    "padding": "8px 24px 12px",
                },
            ),
            html.Hr(style={"margin": "0", "border-color": "#16213e"}),
        ],
        style={"background": "#0d0d1a"},
    )
