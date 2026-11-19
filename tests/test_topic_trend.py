import pandas as pd

from analytics.TopicTrend import TopicTrend
from tests.conftest import LOAD_TIME


def test_hourly_counts_cover_the_window_and_report_outside_rows(articles):
    trend = TopicTrend(LOAD_TIME, window_days=2)
    start, end = trend.window()
    table, outside = trend.counts(articles, "hour", start, end)
    assert table["count"].sum() + outside == len(articles)
    assert outside == 1
    assert table["period"].is_monotonic_increasing


def test_default_start_moves_up_to_where_articles_begin(articles):
    trend = TopicTrend(LOAD_TIME, window_days=7, published=articles["published_at"])
    start, _ = trend.window()
    assert start == pd.Timestamp("2026-11-18", tz="UTC")


def test_granularity_follows_the_span():
    day = pd.Timestamp("2026-01-01", tz="UTC")
    assert TopicTrend.default_granularity(day, day + pd.Timedelta(days=3)) == "hour"
    assert TopicTrend.default_granularity(day, day + pd.Timedelta(days=30)) == "day"
    assert TopicTrend.default_granularity(day, day + pd.Timedelta(days=200)) == "week"


def test_weekly_counts_add_up(articles):
    trend = TopicTrend(LOAD_TIME)
    start = pd.Timestamp("2026-10-01", tz="UTC")
    table, outside = trend.counts(articles, "week", start, LOAD_TIME)
    assert table["count"].sum() + outside == len(articles)
