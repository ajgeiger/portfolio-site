"""Rounded search field used above the topic graph and in the article list."""

from dash import dcc, html


class SearchBox:
    """A pill-shaped wrapper around a search dropdown or a text input."""

    def build(self, component_id: str, placeholder: str, kind: str = "dropdown") -> html.Div:
        if kind == "input":
            control = dcc.Input(
                id=component_id,
                type="search",
                placeholder=placeholder,
                debounce=False,
                className="search-input",
            )
        else:
            control = dcc.Dropdown(
                id=component_id,
                options=[],
                placeholder=placeholder,
                className="search",
                clearable=True,
            )
        return html.Div(
            [
                html.Span(className="search-icon", **{"aria-hidden": "true"}),
                control,
            ],
            className="search-wrap",
        )
