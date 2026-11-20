"""A section title with one plain sentence on what the section shows."""

from dash import html


class SectionHeading:
    """Title and lead on the left, an optional control on the right."""

    def build(self, title: str, lead: str, side=None) -> html.Div:
        text = html.Div([html.H2(title, className="deck-title"), html.P(lead, className="deck-lead")])
        return html.Div([text, side] if side is not None else [text], className="deck-heading")
