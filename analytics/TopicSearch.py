"""Find topics and topic groups by keyword, label or topic id."""

import pandas as pd


class TopicSearch:
    """Search the topic tree.

    A number finds that topic id. Words find every topic or group whose label,
    keyword name or keywords contain all of the words. Results are ranked by
    where the words matched (label first), then by size.
    """

    def __init__(self, nodes: pd.DataFrame):
        self.entries = pd.DataFrame(
            {
                "key": nodes["node_key"].astype(str),
                "is_topic": nodes["is_topic"].astype(bool),
                "topic_id": nodes["topic_id"],
                "keyword_name": nodes["keyword_name"].astype(str),
                "keywords": nodes["keywords"].map(lambda words: " ".join(words).lower()),
                "size": nodes["document_count"].astype(int),
                "topic_count": nodes["topic_ids"].map(len),
            }
        )

    def search(self, query: str, labels: dict[str, str] | None = None, limit: int = 12) -> list[dict]:
        """Return up to limit results as dictionaries with key, label and size."""
        query = (query or "").strip().lower()
        if not query:
            return []
        labels = labels or {}
        names = self.entries["key"].map(labels).fillna(self.entries["keyword_name"])
        if query.isdigit():
            matches = self.entries[self.entries["is_topic"] & (self.entries["topic_id"] == int(query))]
            return [self.result(row, names[index]) for index, row in matches.iterrows()]

        words = query.split()
        in_name = pd.Series(True, index=self.entries.index)
        in_any = pd.Series(True, index=self.entries.index)
        haystack = names.str.lower() + " " + self.entries["keywords"]
        for word in words:
            in_name &= names.str.lower().str.contains(word, regex=False)
            in_any &= haystack.str.contains(word, regex=False)
        ranked = self.entries[in_any].assign(rank=(~in_name[in_any]).astype(int), name=names[in_any])
        ranked = ranked.sort_values(["rank", "is_topic", "size"], ascending=[True, False, False]).head(limit)
        return [self.result(row, row["name"]) for _, row in ranked.iterrows()]

    @staticmethod
    def result(row: pd.Series, name: str) -> dict:
        if row["is_topic"]:
            kind = f"Topic {int(row['topic_id'])}"
        else:
            kind = f"{int(row['topic_count'])} topics"
        return {
            "key": row["key"],
            "label": f"{name}  ({kind}, {int(row['size']):,} articles)",
            "size": int(row["size"]),
        }
