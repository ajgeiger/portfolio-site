"""Read the CSV tables that the Headline Radar topic pipeline writes."""

from pathlib import Path

import pandas as pd


class TopicOutputReader:
    """Load document_topics.csv, topic_info.csv and fit_diagnostics.csv."""

    DOCUMENT_COLUMNS = ["id", "published_at", "source", "source_type", "text", "topic_id"]

    def __init__(self, document_topics_path: Path, topic_info_path: Path, fit_diagnostics_path: Path):
        self.document_topics_path = Path(document_topics_path)
        self.topic_info_path = Path(topic_info_path)
        self.fit_diagnostics_path = Path(fit_diagnostics_path)

    def read_document_topics(self) -> pd.DataFrame:
        """One row per article that went into the fit, with its topic id."""
        documents = pd.read_csv(self.document_topics_path, usecols=self.DOCUMENT_COLUMNS, keep_default_na=False)
        if not documents["id"].is_unique:
            raise ValueError("document_topics.csv must have one row per article id.")
        documents["topic_id"] = documents["topic_id"].astype(int)
        return documents

    def read_topic_info(self) -> pd.DataFrame:
        """One row per topic with its size and keyword name."""
        return pd.read_csv(self.topic_info_path)

    def read_fit_diagnostics(self) -> pd.DataFrame:
        """Cluster sizes before and after the duplicate vote."""
        return pd.read_csv(self.fit_diagnostics_path)
