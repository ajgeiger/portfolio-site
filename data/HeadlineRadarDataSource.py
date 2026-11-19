"""Serve Headline Radar topic results from the prebuilt cache folder."""

import json
from pathlib import Path

import pandas as pd

from config.Settings import Settings
from data.AbstractDataSource import AbstractDataSource
from data.CacheBuilder import CacheBuilder


class HeadlineRadarDataSource(AbstractDataSource):
    """Load the parquet tables written by CacheBuilder.

    The cache is built once with build_cache.py, so the app itself never
    needs the model libraries and starts in a few seconds.
    """

    name = "Headline Radar"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.folder = Path(self.settings.cache_folder)
        self._tables = {}

    def articles(self) -> pd.DataFrame:
        return self._read_table(CacheBuilder.ARTICLES_FILE)

    def topics(self) -> pd.DataFrame:
        return self._read_table(CacheBuilder.TOPICS_FILE)

    def tree(self) -> pd.DataFrame:
        return self._read_table(CacheBuilder.TREE_FILE)

    def metadata(self) -> dict:
        if "metadata" not in self._tables:
            path = self._require(CacheBuilder.METADATA_FILE)
            self._tables["metadata"] = json.loads(path.read_text(encoding="utf-8"))
        return self._tables["metadata"]

    def _read_table(self, file_name: str) -> pd.DataFrame:
        if file_name not in self._tables:
            self._tables[file_name] = pd.read_parquet(self._require(file_name))
        return self._tables[file_name]

    def _require(self, file_name: str) -> Path:
        path = self.folder / file_name
        if not path.exists():
            raise FileNotFoundError(f"{path} is missing. Run: python build_cache.py")
        return path
