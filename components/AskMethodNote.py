"""The side card on the Ask page: how answers are made, and whether the service is up."""

from dash import dcc, html

from components.AskIds import AskIds
from config.AskCopy import AskCopy


class AskMethodNote:
    STATUS_CHECK_MS = 60_000

    def build(self) -> html.Aside:
        return html.Aside(
            [
                html.Div(AskCopy.METHOD_TITLE, className="eyebrow"),
                html.Ol([html.Li(step) for step in AskCopy.METHOD_STEPS], className="ask-steps"),
                html.Div(AskCopy.SERVICE_TITLE, className="eyebrow ask-gap"),
                html.Div(self.status(None), id=AskIds.STATUS),
                html.P(AskCopy.CODE_NOTE, className="muted ask-code-note"),
                dcc.Interval(id=AskIds.STATUS_TIMER, interval=self.STATUS_CHECK_MS),
            ],
            className="ask-side",
        )

    @staticmethod
    def status(info: dict | None) -> list:
        """A status pill and one line, from the service's /info response or None when it is down."""
        if info is None:
            label, line, state = AskCopy.STATUS_OFFLINE, AskCopy.OFFLINE_LINE, "is-offline"
        elif info.get("demo_mode"):
            # demo_mode is the service's name for running without a language model
            label, line, state = AskCopy.STATUS_RETRIEVAL, AskCopy.RETRIEVAL_LINE, "is-retrieval"
        else:
            label, line, state = AskCopy.STATUS_ONLINE, AskCopy.MODEL_LINE.format(model=info["llm_model"]), "is-online"
        return [
            html.Span([html.Span(className="ask-status-dot"), label], className=f"ask-status {state}"),
            html.P(line, className="ask-status-line"),
        ]
