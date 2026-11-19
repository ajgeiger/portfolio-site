import pytest

from analytics.CoverageSummary import CoverageSummary


def test_counts_and_share_bases(articles):
    summary = CoverageSummary.from_articles(articles)
    assert summary.total_rows == 26
    assert summary.rows_with_text == 24
    assert summary.assigned_rows == 20
    assert summary.topic_count == 5
    assert summary.unassigned_rows == 4
    assert summary.missing_rows == 2
    assert summary.assigned_share == pytest.approx(20 / 24)
    assert summary.unassigned_share == pytest.approx(4 / 24)
    assert summary.missing_share == pytest.approx(2 / 26)


def test_empty_selection_has_zero_shares(articles):
    summary = CoverageSummary.from_articles(articles.iloc[0:0])
    assert summary.assigned_share == 0.0
