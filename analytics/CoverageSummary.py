"""Count articles by status for the summary cards."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CoverageSummary:
    """Totals for one filtered set of articles.

    Topic and unassigned shares use articles with text as the base.
    The missing share uses every row as the base.
    """

    OUTLIER_TOPIC = -1
    BLANK_TOPIC = -2

    total_rows: int
    rows_with_text: int
    assigned_rows: int
    topic_count: int
    unassigned_rows: int
    missing_rows: int

    @classmethod
    def from_articles(cls, articles: pd.DataFrame) -> "CoverageSummary":
        topics = articles["topic_id"]
        assigned = topics >= 0
        return cls(
            total_rows=int(len(articles)),
            rows_with_text=int(articles["has_text"].sum()),
            assigned_rows=int(assigned.sum()),
            topic_count=int(topics[assigned].nunique()),
            unassigned_rows=int((topics == cls.OUTLIER_TOPIC).sum()),
            missing_rows=int((topics == cls.BLANK_TOPIC).sum()),
        )

    @staticmethod
    def share(part: int, whole: int) -> float:
        return part / whole if whole else 0.0

    @property
    def assigned_share(self) -> float:
        return self.share(self.assigned_rows, self.rows_with_text)

    @property
    def unassigned_share(self) -> float:
        return self.share(self.unassigned_rows, self.rows_with_text)

    @property
    def missing_share(self) -> float:
        return self.share(self.missing_rows, self.total_rows)
