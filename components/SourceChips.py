"""The documents an answer drew on, as small chips."""

from dash import html

from config.AskCopy import AskCopy


class SourceChips:
    def build(self, sources: list[str]) -> html.Div | None:
        if not sources:
            return None
        return html.Div(
            [
                html.Span(AskCopy.SOURCES_TITLE, className="ask-small-title"),
                *[html.Span(source, className="tag-pill") for source in sources],
            ],
            className="ask-source-chips",
        )
