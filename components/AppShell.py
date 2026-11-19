"""The website frame around every page: sticky header, navigation and footer."""

from datetime import date

import dash
from dash import dcc, html

from config.Profile import Profile


class AppShell:
    """Build the site header, navigation and footer.

    Navigation has two kinds of links: pages (Home, Projects) and anchors on
    the home page (About, Contact). Page links stay inside the app; anchor
    links are plain links that scroll to their section once it is drawn.
    """

    NAV_ID = "shell-navigation"
    LOCATION_ID = "shell-location"

    NAV_ITEMS = [
        ("Home", "/"),
        ("Projects", "/projects"),
        ("About", "/#about"),
        ("Contact", "/#contact"),
    ]

    def layout(self) -> html.Div:
        return html.Div(
            [
                dcc.Location(id=self.LOCATION_ID),
                html.A("Skip to content", href="#content", className="skip-link"),
                self.header(),
                html.Main(dash.page_container, id="content", className="shell-main"),
                self.footer(),
            ],
            className="shell",
        )

    def header(self) -> html.Header:
        brand = dcc.Link(
            [
                html.Span("AG", className="brand-mark"),
                html.Span(
                    [html.Span(Profile.NAME, className="brand-name"), html.Span(Profile.ROLE, className="brand-role")],
                    className="brand-text",
                ),
            ],
            href="/",
            className="brand",
        )
        navigation = html.Nav(self.links("/"), id=self.NAV_ID, className="shell-nav", **{"aria-label": "Main"})
        return html.Header(html.Div([brand, navigation], className="shell-header-inner"), className="shell-header")

    def links(self, pathname: str) -> list:
        """Navigation links with the current section marked as active."""
        links = []
        for label, href in self.NAV_ITEMS:
            class_name = "shell-link" + (" is-active" if self.is_active(href, pathname) else "")
            if "#" in href:
                links.append(html.A(label, href=href, className=class_name))
            else:
                links.append(dcc.Link(label, href=href, className=class_name))
        return links

    @staticmethod
    def is_active(href: str, pathname: str) -> bool:
        if "#" in href:
            return False
        if href == "/":
            return pathname == "/"
        return pathname == href or pathname.startswith(href + "/")

    def footer(self) -> html.Footer:
        about = html.Div(
            [
                html.Div(Profile.NAME, className="footer-name"),
                html.P(
                    f"{Profile.ROLE}. Live analytics projects built on open data, with the code behind them.",
                    className="footer-text",
                ),
            ],
            className="footer-column wide",
        )
        site = self.footer_column("Site", [dcc.Link(label, href=href) for label, href in self.NAV_ITEMS[:2]])
        elsewhere = self.footer_column(
            "Elsewhere",
            [
                html.A("GitHub", href=Profile.GITHUB_URL, target="_blank", rel="noopener noreferrer"),
                html.A("Kaggle", href=Profile.KAGGLE_URL, target="_blank", rel="noopener noreferrer"),
            ],
        )
        legal = html.Div(
            f"\u00a9 {date.today().year} {Profile.NAME}. Built with Python and Plotly Dash.", className="footer-legal"
        )
        return html.Footer(
            html.Div(
                [html.Div([about, site, elsewhere], className="footer-grid"), legal], className="shell-footer-inner"
            ),
            className="shell-footer",
        )

    @staticmethod
    def footer_column(title: str, links: list) -> html.Div:
        return html.Div(
            [html.Div(title, className="footer-title"), html.Ul([html.Li(link) for link in links])],
            className="footer-column",
        )
