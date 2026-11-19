"""Filter a list of articles by a typed search query."""


class ArticleSearch:
    """Match listed articles against a free-text query.

    The query is applied to the title, source and tag, case insensitive.
    An empty query leaves the list unchanged.
    """

    FIELDS = ("title", "source", "tag")

    def apply(self, articles: list[dict], query: str | None) -> list[dict]:
        needle = (query or "").strip().lower()
        if not needle:
            return list(articles)
        return [article for article in articles if self.matches(article, needle)]

    @classmethod
    def matches(cls, article: dict, needle: str) -> bool:
        return any(needle in str(article.get(field) or "").lower() for field in cls.FIELDS)
