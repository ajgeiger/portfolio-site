from analytics.ArticleFilter import ArticleFilter


def test_no_filter_keeps_every_row(articles):
    assert len(ArticleFilter().apply(articles)) == len(articles)


def test_date_filter_is_inclusive_and_drops_old_dates(articles):
    kept = ArticleFilter.from_inputs("2026-11-18", "2026-11-18", None, None).apply(articles)
    assert kept["published_at"].dt.date.astype(str).eq("2026-11-18").all()
    assert "article_0" not in set(kept["id"])


def test_source_and_feed_filters_combine(articles):
    kept = ArticleFilter.from_inputs(None, None, ["rss"], ["daily.example"]).apply(articles)
    assert set(kept["source_type"]) == {"rss"}
    assert set(kept["source"]) == {"daily.example"}
