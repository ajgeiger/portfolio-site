"""The shared frame around every page: brand, navigation and footer."""

import dash
from dash import dcc, html


class AppShell:
    """Build the portfolio header, page navigation and footer.

    Navigation links are generated from the registered pages, so adding a
    page to the app adds it to the menu with no other changes.
    """

    BRAND = "Alex Geiger"
    BRAND_DETAIL = "Analytics Portfolio"
    NAV_ID = "shell-navigation"
    LOCATION_ID = "shell-location"
    FOOTER = "Built by Alex Geiger with Python and Plotly Dash. Data and topic model from the Headline Radar project."

    def __init__(self, pages: list):
        self.pages = pages

    def layout(self) -> html.Div:
        return html.Div(
            [
                dcc.Location(id=self.LOCATION_ID),
                html.Header(
                    html.Div(
                        [
                            html.A(
                                [
                                    html.Span(self.BRAND, className="brand-name"),
                                    html.Span("|", className="brand-divider"),
                                    html.Span(self.BRAND_DETAIL, className="brand-detail"),
                                ],
                                href="/",
                                className="brand",
                            ),
                            html.Nav(self.links("/"), id=self.NAV_ID, className="shell-nav"),
                        ],
                        className="shell-header-inner",
                    ),
                    className="shell-header",
                ),
                html.Main(dash.page_container, className="shell-main"),
                html.Footer(
                    html.Div(
                        self.FOOTER,
                        className="shell-footer-inner",
                    ),
                    className="shell-footer",
                ),
            ],
            className="shell",
        )

    def links(self, pathname: str) -> list:
        return [
            dcc.Link(
                page.name, href=page.path, className="shell-link" + (" is-active" if page.path == pathname else "")
            )
            for page in self.pages
        ]
