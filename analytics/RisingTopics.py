"""Find the topics whose share of coverage grew or shrank the most."""

import pandas as pd

from analytics.ComparisonWindow import ComparisonWindow


class RisingTopics:
    """Compare each topic's share of coverage in a recent window with the prior window.

    Share means the topic's articles divided by all articles with text in the
    same window, unassigned included, so a busy news day does not make every
    topic look like it is rising. The change is reported in percentage points.

    The default comparison is the last 7 days against the 7 days before.
    When the prior period holds too few articles to compare against, as with
    a corpus collected over a single day, the window shrinks to 24 hours and
    then 6 hours, and the chosen window is always named in the chart.
    """

    WINDOWS = [
        ComparisonWindow("7d", "Last 7 days vs the prior 7 days", pd.Timedelta(days=7)),
        ComparisonWindow("24h", "Last 24 hours vs the prior 24 hours", pd.Timedelta(hours=24)),
        ComparisonWindow("6h", "Last 6 hours vs the prior 6 hours", pd.Timedelta(hours=6)),
    ]

    def __init__(self, last_load_time: pd.Timestamp, min_prior_articles: int = 1000, min_topic_articles: int = 10):
        self.last_load_time = pd.Timestamp(last_load_time)
        self.min_prior_articles = min_prior_articles
        self.min_topic_articles = min_topic_articles

    def window(self, key: str) -> ComparisonWindow:
        return next(window for window in self.WINDOWS if window.key == key)

    def periods(self, articles: pd.DataFrame, window: ComparisonWindow) -> tuple[pd.Series, pd.Series]:
        """Return masks for the recent and prior periods."""
        published = articles["published_at"]
        recent_start = self.last_load_time - window.length
        prior_start = recent_start - window.length
        recent = (published > recent_start) & (published <= self.last_load_time)
        prior = (published > prior_start) & (published <= recent_start)
        return recent, prior

    def choose_window(self, articles: pd.DataFrame) -> ComparisonWindow:
        """Pick the longest window whose prior period has enough articles."""
        with_text = articles[articles["has_text"]]
        for window in self.WINDOWS:
            _, prior = self.periods(with_text, window)
            if prior.sum() >= self.min_prior_articles:
                return window
        return self.WINDOWS[-1]

    def compare(self, articles: pd.DataFrame, window: ComparisonWindow) -> pd.DataFrame:
        """One row per topic with recent and prior counts, shares and the change.

        Sorted from the biggest rise to the biggest fall. Topics with fewer
        than min_topic_articles in both periods are left out as noise.
        """
        with_text = articles[articles["has_text"]]
        recent, prior = self.periods(with_text, window)
        recent_total, prior_total = int(recent.sum()), int(prior.sum())

        assigned = with_text["topic_id"] >= 0
        recent_counts = with_text.loc[recent & assigned, "topic_id"].value_counts()
        prior_counts = with_text.loc[prior & assigned, "topic_id"].value_counts()
        table = pd.DataFrame({"recent_count": recent_counts, "prior_count": prior_counts}).fillna(0).astype(int)
        table = table[
            (table["recent_count"] >= self.min_topic_articles) | (table["prior_count"] >= self.min_topic_articles)
        ]

        table["recent_share"] = table["recent_count"] / recent_total if recent_total else 0.0
        table["prior_share"] = table["prior_count"] / prior_total if prior_total else 0.0
        table["change_points"] = (table["recent_share"] - table["prior_share"]) * 100
        table.attrs.update({"recent_total": recent_total, "prior_total": prior_total, "window": window.label})
        table = table.rename_axis("topic_id").reset_index()
        return table.sort_values(["change_points", "topic_id"], ascending=[False, True], ignore_index=True)
