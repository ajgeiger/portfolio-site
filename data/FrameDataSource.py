"""A data source backed by tables that are already in memory."""

import pandas as pd

from data.AbstractDataSource import AbstractDataSource


class FrameDataSource(AbstractDataSource):
    """Serve tables passed in directly. Useful for tests and notebooks."""

    def __init__(
        self,
        articles: pd.DataFrame,
        topics: pd.DataFrame,
        tree: pd.DataFrame,
        metadata: dict,
        name: str = "In memory data",
    ):
        self._articles = articles
        self._topics = topics
        self._tree = tree
        self._metadata = metadata
        self.name = name

    def articles(self) -> pd.DataFrame:
        return self._articles

    def topics(self) -> pd.DataFrame:
        return self._topics

    def tree(self) -> pd.DataFrame:
        return self._tree

    def metadata(self) -> dict:
        return self._metadata
