"""Trim and cap the Ask conversation before it is sent to the chatbot service."""


class AskHistory:
    """Keep the last ten turns, drop outage replies, and cap each message."""

    TURNS = 10
    MAX_CHARS = 2000

    def for_request(self, history: list[dict]) -> list[dict]:
        """Earlier turns only, oldest first, ready for POST /chat."""
        recent = []
        for item in history:
            if item.get("status") == "outage":
                continue
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and content:
                recent.append({"role": role, "content": str(content)[: self.MAX_CHARS]})
        return recent[-2 * self.TURNS :]
