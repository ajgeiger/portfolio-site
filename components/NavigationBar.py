"""Back, Home, breadcrumbs, search and graph controls above the graph."""

from dash import html

from components.ExplorerIds import ExplorerIds
from components.SearchBox import SearchBox


class NavigationBar:
    """Ways to move around the topic tree."""

    def build(self) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [
                        html.Button("\u2190 Back", id=ExplorerIds.BACK, className="nav-button", n_clicks=0),
                        html.Button("Home", id=ExplorerIds.HOME, className="nav-button", n_clicks=0),
                        html.Nav(id=ExplorerIds.BREADCRUMBS, className="breadcrumbs", **{"aria-label": "Breadcrumb"}),
                    ],
                    className="nav-left",
                ),
                html.Div(
                    [
                        SearchBox().build(
                            ExplorerIds.SEARCH,
                            "Search by keyword, label or topic id",
                        ),
                        html.Button("+", id=ExplorerIds.ZOOM_IN, className="icon-button", n_clicks=0, title="Zoom in"),
                        html.Button(
                            "\u2212", id=ExplorerIds.ZOOM_OUT, className="icon-button", n_clicks=0, title="Zoom out"
                        ),
                        html.Button(
                            "Fit",
                            id=ExplorerIds.FIT,
                            className="icon-button wide",
                            n_clicks=0,
                            title="Fit the graph to the frame",
                        ),
                    ],
                    className="nav-right",
                ),
            ],
            className="navigation-bar",
        )

    @staticmethod
    def breadcrumbs(names: list[str]) -> list:
        """Each crumb except the last is a button that jumps back to that view."""
        items = []
        for index, name in enumerate(names):
            if index:
                items.append(html.Span("\u203a", className="crumb-separator"))
            if index == len(names) - 1:
                items.append(html.Span(name, className="crumb current"))
            else:
                items.append(
                    html.Button(name, id={"type": ExplorerIds.CRUMB, "index": index}, className="crumb", n_clicks=0)
                )
        return items
