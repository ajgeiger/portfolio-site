"""One message in the Ask conversation."""

from dash import dcc, html

from components.CitationList import CitationList
from components.SourceChips import SourceChips


class AskMessage:
    """A visitor question on the right; an answer on the left with its source chips and citations."""

    def __init__(self):
        self.citations = CitationList()
        self.chips = SourceChips()

    def build(self, message: dict) -> html.Div:
        role = message["role"]
        status = message.get("status", "answered")
        if role == "user":
            body = [html.P(message["content"], className="ask-text")]
        else:
            body = [dcc.Markdown(message["content"], className="ask-text")]
            extras = [self.chips.build(message.get("sources", [])), self.citations.build(message.get("citations", []))]
            body += [item for item in extras if item is not None]
        author = "You" if role == "user" else "Answer"
        return html.Div(
            [html.Div(author, className="ask-author"), html.Div(body, className="ask-bubble-body")],
            className=f"ask-bubble is-{role} status-{status}",
        )
