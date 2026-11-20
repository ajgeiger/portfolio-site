"""The Ask page against a stub chatbot service: answers, outage state and wiring."""

from dash import Dash

from components.AppShell import AppShell
from components.AskIds import AskIds
from config.AskCopy import AskCopy
from config.Settings import Settings
from pages.AskPage import AskPage
from tests.conftest import answering_handler, make_chatbot_client
from tests.test_portfolio_site import JOB_SEEKING, text_of


def test_page_follows_the_page_contract(chatbot):
    page = AskPage(chatbot)
    assert page.path == "/ask" and page.module_name == "pages.AskPage"
    layout = page.layout()
    rendered = str(layout)
    for component_id in (AskIds.MESSAGES, AskIds.INPUT, AskIds.SEND, AskIds.STATUS):
        assert component_id in rendered
    text = text_of(layout)
    assert AskCopy.TITLE in text
    assert all(question in text for question in AskCopy.SUGGESTED_QUESTIONS)
    assert AskCopy.METHOD_STEPS[0] in text


def test_ask_is_in_the_navigation():
    assert ("Ask", "/ask") in AppShell.NAV_ITEMS


def test_answer_adds_both_turns(chatbot):
    history = AskPage(chatbot).answer("  What is his   current role? ", [])
    assert [item["role"] for item in history] == ["user", "assistant"]
    assert history[0]["content"] == "What is his current role?"
    reply = history[1]
    assert reply["status"] == "answered"
    assert "Lead Applied AI Scientist" in reply["content"]
    assert "sources" not in reply and "citations" not in reply


def test_rendered_answer_hides_sources_and_citations(chatbot):
    page = AskPage(chatbot)
    text = text_of(page.panel.messages(page.answer("What is his current role?", [])))
    assert "Lead Applied AI Scientist at Signature Aviation" in text
    assert "Citations" not in text and "Sources" not in text
    assert "Name and current title" not in text


def test_history_is_sent_without_outage_turns():
    seen = []

    def handler(request):
        seen.append(request.read())
        return answering_handler(request)

    page = AskPage(make_chatbot_client(handler))
    history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": AskCopy.OUTAGE, "status": "outage"},
    ]
    page.answer("second", history)
    assert b"first" in seen[0] and AskCopy.OUTAGE.encode() not in seen[0]


def test_outage_gives_a_clear_message_and_offline_status(offline_chatbot):
    page = AskPage(offline_chatbot)
    history = page.answer("What is his current role?", [])
    assert history[1] == {"role": "assistant", "content": AskCopy.OUTAGE, "status": "outage"}
    assert page.service_info() is None
    assert AskCopy.STATUS_OFFLINE in text_of(page.method_note.status(None))


def test_status_names_the_model_or_retrieval_only(chatbot):
    page = AskPage(chatbot)
    assert "claude-sonnet-5-5" in text_of(page.method_note.status(page.service_info()))
    assert AskCopy.STATUS_RETRIEVAL in text_of(page.method_note.status({"demo_mode": True}))


def test_callbacks_register_on_a_dash_app(chatbot):
    app = Dash(__name__)
    page = AskPage(chatbot)
    app.layout = page.layout()
    page.register_callbacks(app)
    assert any(AskIds.MESSAGES in key for key in app.callback_map)
    assert any(AskIds.STATUS in key for key in app.callback_map)


def test_copy_never_suggests_job_seeking():
    copy = " ".join(
        value if isinstance(value, str) else " ".join(value)
        for value in vars(AskCopy).values()
        if isinstance(value, str | tuple)
    )
    assert JOB_SEEKING.search(copy) is None


def test_service_url_and_key_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("CHATBOT_API_URL", "https://example.hf.space")
    monkeypatch.setenv("CHATBOT_API_KEY", "secret-key")
    settings = Settings()
    assert settings.chatbot_api_url == "https://example.hf.space"
    assert settings.chatbot_api_key == "secret-key"
    assert "secret-key" not in repr(settings)
