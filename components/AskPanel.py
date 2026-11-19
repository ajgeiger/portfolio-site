"""The Ask card: conversation, suggested questions and the question box."""

from dash import dcc, html

from components.AskIds import AskIds
from components.AskMessage import AskMessage
from components.SuggestedQuestions import SuggestedQuestions
from config.AskCopy import AskCopy
from config.Theme import Theme


class AskPanel:
    MAX_QUESTION_CHARS = 500

    def __init__(self):
        self.message = AskMessage()

    @staticmethod
    def welcome() -> dict:
        return {"role": "assistant", "content": AskCopy.WELCOME, "status": "welcome"}

    def messages(self, history: list[dict]) -> list:
        return [self.message.build(item) for item in [self.welcome(), *history]]

    def build(self) -> html.Div:
        question_row = html.Div(
            [
                dcc.Input(
                    id=AskIds.INPUT,
                    type="text",
                    placeholder=AskCopy.PLACEHOLDER,
                    debounce=False,
                    maxLength=self.MAX_QUESTION_CHARS,
                    autoComplete="off",
                    className="ask-input",
                ),
                html.Button(AskCopy.SEND_LABEL, id=AskIds.SEND, n_clicks=0, className="button primary"),
            ],
            className="ask-input-row",
        )
        conversation = dcc.Loading(
            html.Div(self.messages([]), id=AskIds.MESSAGES, className="ask-messages"),
            type="dot",
            color=Theme.ACCENT,
            parent_className="ask-loading",
        )
        return html.Div(
            [
                dcc.Store(id=AskIds.HISTORY, data=[]),
                dcc.Store(id=AskIds.SCROLL_SINK),
                conversation,
                SuggestedQuestions().build(),
                question_row,
            ],
            className="ask-card",
        )
