"""A numbered section title, so the page reads like a short deck."""

from dash import html


class SectionHeading:
    """Number, title and one plain sentence on what the section shows."""

    def build(self, number: int, title: str, lead: str, side=None) -> html.Div:
        text = html.Div(
            [
                html.Div(f"{number:02d}", className="deck-number"),
                html.Div([html.H2(title, className="deck-title"), html.P(lead, className="deck-lead")]),
            ],
            className="deck-heading-text",
        )
        return html.Div([text, side] if side is not None else [text], className="deck-heading")
