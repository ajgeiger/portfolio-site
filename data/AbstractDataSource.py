"""The contract every data source must meet so pages can stay data agnostic."""

from abc import ABC, abstractmethod

import pandas as pd


class AbstractDataSource(ABC):
    """Provide the four tables the topic explorer reads.

    articles: one row per article with id, topic_id, published_at (UTC),
        source, source_type, title, summary, url, has_text, is_repeat_text
        and date_flag.
    topics: one row per topic with topic_id, document_count, keywords,
        keyword_name and representative_ids.
    tree: one row per node of the topic tree (see TopicTreeBuilder).
    metadata: a dictionary of totals and data notes.
    """

    name = "Data source"

    @abstractmethod
    def articles(self) -> pd.DataFrame:
        """Return the article table."""

    @abstractmethod
    def topics(self) -> pd.DataFrame:
        """Return the topic table."""

    @abstractmethod
    def tree(self) -> pd.DataFrame:
        """Return the topic tree node table."""

    @abstractmethod
    def metadata(self) -> dict:
        """Return totals and data notes."""
