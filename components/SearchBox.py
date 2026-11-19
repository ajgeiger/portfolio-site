"""Rounded search field used above the topic graph."""

from dash import dcc, html


class SearchBox:
    """A pill-shaped wrapper around the article and topic search dropdown."""

    def build(self, component_id: str, placeholder: str) -> html.Div:
        return html.Div(
            [
                html.Span(className="search-icon", **{"aria-hidden": "true"}),
                dcc.Dropdown(
                    id=component_id,
                    options=[],
                    placeholder=placeholder,
                    className="search",
                    clearable=True,
                ),
            ],
            className="search-wrap",
        )
