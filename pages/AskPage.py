"""The Ask page: questions about my projects and experience, answered by the rag-chatbot service."""

from dash import ALL, Dash, Input, Output, State, ctx, html, no_update
from rag_chatbot_client import ChatbotClient, ChatbotError

from components.AskIds import AskIds
from components.AskMethodNote import AskMethodNote
from components.AskPanel import AskPanel
from config.AskCopy import AskCopy
from pages.AbstractPage import AbstractPage


class AskPage(AbstractPage):
    """A chat card that calls POST /chat through the rag-chatbot client, with a side card on the method.

    The service runs separately (CHATBOT_API_URL). When it cannot be reached,
    the page stays up, answers with a fixed outage message and marks the
    service as offline.
    """

    path = "/ask"
    name = "Ask"
    title = "Ask"
    description = "Ask questions about Alexander J. Geiger's projects and experience."

    HISTORY_TURNS = 6

    def __init__(self, client: ChatbotClient):
        self.client = client
        self.panel = AskPanel()
        self.method_note = AskMethodNote()

    def layout(self):
        heading = html.Div(
            [
                html.Div(AskCopy.EYEBROW, className="eyebrow"),
                html.H1(AskCopy.TITLE, className="page-title"),
                html.P(AskCopy.LEAD, className="section-lead"),
            ],
            className="page-heading",
        )
        body = html.Div([self.panel.build(), self.method_note.build()], className="ask-grid")
        return html.Div(html.Div([heading, body], className="ask-page"), className="site-page")

    def answer(self, question: str, history: list[dict]) -> list[dict]:
        """Ask the service and return the history with both new turns added."""
        question = " ".join(question.split())
        recent = [
            {"role": item["role"], "content": item["content"]} for item in history if item.get("status") != "outage"
        ]
        try:
            response = self.client.chat(question, recent[-self.HISTORY_TURNS :])
            reply = {"role": "assistant", "content": response.answer, "status": response.status}
        except ChatbotError:
            reply = {"role": "assistant", "content": AskCopy.OUTAGE, "status": "outage"}
        return [*history, {"role": "user", "content": question}, reply]

    def service_info(self) -> dict | None:
        try:
            return self.client.info()
        except ChatbotError:
            return None

    def register_callbacks(self, app: Dash) -> None:
        @app.callback(
            Output(AskIds.MESSAGES, "children"),
            Output(AskIds.HISTORY, "data"),
            Output(AskIds.INPUT, "value"),
            Input(AskIds.SEND, "n_clicks"),
            Input(AskIds.INPUT, "n_submit"),
            Input({"type": AskIds.SUGGESTED, "index": ALL}, "n_clicks"),
            State(AskIds.INPUT, "value"),
            State(AskIds.HISTORY, "data"),
            prevent_initial_call=True,
        )
        def ask(_send, _submit, _suggested, typed, history):
            trigger = ctx.triggered_id
            if isinstance(trigger, dict):
                if not ctx.triggered[0]["value"]:
                    return no_update, no_update, no_update
                question = AskCopy.SUGGESTED_QUESTIONS[trigger["index"]]
            else:
                question = typed or ""
            if not question.strip():
                return no_update, no_update, no_update
            history = self.answer(question, history or [])
            return self.panel.messages(history), history, ""

        @app.callback(
            Output(AskIds.STATUS, "children"),
            Input(AskIds.STATUS_TIMER, "n_intervals"),
            Input(AskIds.HISTORY, "data"),
        )
        def status(_ticks, _history):
            return self.method_note.status(self.service_info())

        app.clientside_callback(
            """
            function(children) {
                setTimeout(function() {
                    var box = document.getElementById('ask-messages');
                    if (box) { box.scrollTop = box.scrollHeight; }
                }, 50);
                return null;
            }
            """,
            Output(AskIds.SCROLL_SINK, "data"),
            Input(AskIds.MESSAGES, "children"),
        )
