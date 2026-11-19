"""Suggested questions, shown as clickable chips."""

from dash import html

from components.AskIds import AskIds
from config.AskCopy import AskCopy


class SuggestedQuestions:
    def build(self, questions: tuple[str, ...] = AskCopy.SUGGESTED_QUESTIONS) -> html.Div:
        chips = [
            html.Button(question, id={"type": AskIds.SUGGESTED, "index": index}, className="ask-chip", n_clicks=0)
            for index, question in enumerate(questions)
        ]
        return html.Div(
            [html.Div(AskCopy.SUGGESTED_TITLE, className="ask-label"), html.Div(chips, className="ask-chips")],
            className="ask-suggested",
        )
