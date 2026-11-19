import pandas as pd
import pytest

from analytics.RisingTopics import RisingTopics
from tests.conftest import LOAD_TIME


def make_rows(topic_counts_recent: dict, topic_counts_prior: dict) -> pd.DataFrame:
    rows = []
    for counts, hours_back in ((topic_counts_recent, 1), (topic_counts_prior, 8)):
        for topic, count in counts.items():
            rows += [
                {"topic_id": topic, "published_at": LOAD_TIME - pd.Timedelta(hours=hours_back), "has_text": True}
            ] * count
    return pd.DataFrame(rows)


def test_change_is_in_share_points_with_unassigned_in_the_base():
    rows = make_rows({0: 30, 1: 10, -1: 60}, {0: 10, 1: 30, -1: 60})
    rising = RisingTopics(LOAD_TIME, min_prior_articles=50, min_topic_articles=5)
    window = rising.choose_window(rows)
    assert window.key == "6h", "the 7 day and 24 hour prior periods are empty, so 6 hours is chosen"
    table = rising.compare(rows, window)
    top = table.iloc[0]
    assert top["topic_id"] == 0
    assert top["change_points"] == pytest.approx(20.0)
    assert table.iloc[-1]["topic_id"] == 1


def test_falls_back_to_the_shortest_window_when_data_is_thin():
    rows = make_rows({0: 5}, {0: 5})
    rising = RisingTopics(LOAD_TIME, min_prior_articles=1000)
    assert rising.choose_window(rows).key == "6h"
