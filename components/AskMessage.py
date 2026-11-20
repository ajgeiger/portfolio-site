"""One message in the Ask conversation."""

from dash import dcc, html


class AskMessage:
    """A visitor question on the right; an answer on the left."""

    def build(self, message: dict) -> html.Div:
        role = message["role"]
        status = message.get("status", "answered")
        if role == "user":
            body = [html.P(message["content"], className="ask-text")]
        else:
            body = [dcc.Markdown(message["content"], className="ask-text")]
        author = "You" if role == "user" else "Answer"
        return html.Div(
            [html.Div(author, className="ask-author"), html.Div(body, className="ask-bubble-body")],
            className=f"ask-bubble is-{role} status-{status}",
        )
