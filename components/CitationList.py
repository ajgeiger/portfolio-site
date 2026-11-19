"""The numbered passages an answer cites."""

from dash import html

from config.AskCopy import AskCopy


class CitationList:
    """One expandable row per citation: number, source and section, with the passage inside."""

    SNIPPET_WORDS = 60

    def build(self, citations: list[dict]) -> html.Div | None:
        if not citations:
            return None
        return html.Div(
            [html.Div(AskCopy.CITATIONS_TITLE, className="ask-small-title"), *[self.row(item) for item in citations]],
            className="ask-citations",
        )

    def row(self, citation: dict) -> html.Details:
        words = citation["text"].split()
        snippet = " ".join(words[: self.SNIPPET_WORDS]) + (" ..." if len(words) > self.SNIPPET_WORDS else "")
        return html.Details(
            [
                html.Summary(
                    [
                        html.Span(str(citation["number"]), className="ask-citation-number"),
                        html.Span(citation["source"], className="ask-citation-source"),
                        html.Span(citation["section"], className="ask-citation-section"),
                    ]
                ),
                html.P(snippet, className="ask-citation-text"),
            ],
            className="ask-citation",
        )
