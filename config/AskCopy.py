"""Every fixed sentence on the Ask page, in one place so the tone stays consistent."""


class AskCopy:
    """Plain, understated wording for the Ask page."""

    EYEBROW = "ASK"
    TITLE = "Ask about my projects and experience"
    LEAD = (
        "Answers come only from my resume and project write ups, with the passages they rely on listed "
        "under each answer. If something is not covered, the answer says so."
    )
    PLACEHOLDER = "Ask a question about my projects or experience"
    SEND_LABEL = "Ask"
    SUGGESTED_TITLE = "Suggested questions"
    CITATIONS_TITLE = "Citations"
    SOURCES_TITLE = "Sources"
    WELCOME = (
        "Hello. I answer questions about Alex Geiger's projects and professional experience, "
        "using his resume and project documentation."
    )

    SUGGESTED_QUESTIONS = (
        "What does he work on at Signature Aviation?",
        "How does the news topic explorer work?",
        "What is his current role?",
        "Which tools and languages does he use?",
        "Where did he study?",
    )

    OUTAGE = (
        "The question service cannot be reached right now, so this page cannot answer. "
        "The resume and project pages cover the same material."
    )
    STATUS_ONLINE = "Online"
    STATUS_DEMO = "Online, demo mode"
    STATUS_OFFLINE = "Offline"
    MODEL_LINE = "Answers are written by {model}."
    DEMO_LINE = "No language model is connected, so answers quote the closest passages."
    OFFLINE_LINE = "The service did not respond. Questions will work again once it is back."

    METHOD_TITLE = "HOW IT WORKS"
    METHOD_STEPS = (
        "Your question is matched against short passages from my resume and project READMEs, "
        "using keyword search and semantic search together.",
        "A language model writes a brief answer from the best passages only and cites them by number.",
        "Questions with no matching passage get a plain not covered reply instead of a guess.",
        "It does not discuss job plans or pay, and never shares a phone number or email address.",
    )
    SERVICE_TITLE = "SERVICE"
    CODE_NOTE = "The retrieval service is its own repository, rag-chatbot."
