import dash
from pages.spine_a import (
    a1_swing_equation,
    a2_smib_equilibrium,
    a3_phase_portrait,
    a4_equal_area,
    a5_critical_clearing_time,
    a6_eigenvalue_damping,
)

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server  # WSGI entry point for Render.com

app.layout = dash.html.Div(
    [dash.page_container],
    style={"background": "#1a1a2e", "min-height": "100vh"},
)

if __name__ == "__main__":
    app.run(debug=True)
