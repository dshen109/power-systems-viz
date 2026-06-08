"""
Dash integration tests using dash[testing] + Selenium ChromeDriver.
Run: pytest tests/test_callbacks.py -v
Requires: Google Chrome + matching chromedriver on PATH.
"""
import pytest
from dash.testing.application_runners import import_app


@pytest.fixture
def dash_app(dash_duo):
    """Load the app via dash_duo test runner."""
    app = import_app("app")
    dash_duo.start_server(app)
    return dash_duo


class TestPageA1:
    def test_page_loads(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/swing-equation")
        dash_app.wait_for_element("#a1-graph", timeout=10)

    def test_graph_has_data_on_load(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/swing-equation")
        dash_app.wait_for_element("#a1-graph .js-plotly-plot", timeout=10)
        graph = dash_app.find_element("#a1-graph")
        assert graph is not None

    def test_warning_hidden_on_valid_input(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/swing-equation")
        dash_app.wait_for_element("#a1-warning", timeout=10)
        warning = dash_app.find_element("#a1-warning")
        assert warning.get_attribute("style") and "none" in warning.get_attribute("style")

    def test_next_link_navigates(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/swing-equation")
        dash_app.wait_for_element("a[href='/stability/smib-equilibrium']", timeout=10)
        dash_app.find_element("a[href='/stability/smib-equilibrium']").click()
        dash_app.wait_for_element("#a2-graph", timeout=10)


class TestPageA2:
    def test_page_loads(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/smib-equilibrium")
        dash_app.wait_for_element("#a2-graph", timeout=10)

    def test_prev_link_present(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/smib-equilibrium")
        dash_app.wait_for_element("a[href='/stability/swing-equation']", timeout=10)


class TestPageA3:
    def test_page_loads(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/phase-portrait")
        dash_app.wait_for_element("#a3-graph", timeout=15)


class TestPageA4:
    def test_page_loads(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/equal-area")
        dash_app.wait_for_element("#a4-graph", timeout=10)


class TestPageA5:
    def test_page_loads(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/critical-clearing-time")
        dash_app.wait_for_element("#a5-graph", timeout=10)


class TestPageA6:
    def test_page_loads(self, dash_app):
        dash_app.driver.get(dash_app.server_url + "/stability/eigenvalue-damping")
        dash_app.wait_for_element("#a6-graph", timeout=10)

    def test_no_next_link_on_last_page(self, dash_app):
        """A6 is last page — no next link."""
        dash_app.driver.get(dash_app.server_url + "/stability/eigenvalue-damping")
        dash_app.wait_for_element("#a6-graph", timeout=10)
        links = dash_app.driver.find_elements("css selector", "a[href*='stability']")
        hrefs = [l.get_attribute("href") for l in links]
        assert not any("/stability/eigenvalue-damping" in h and "→" in (l.text or "") for l, h in zip(links, hrefs))
