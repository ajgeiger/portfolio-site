import sqlite3

import pandas as pd
import pytest

from config.Settings import Settings
from data.ArticleDatabaseReader import ArticleDatabaseReader
from data.CacheBuilder import CacheBuilder


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "news.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE articles (id TEXT PRIMARY KEY, title TEXT, description TEXT, url TEXT, source TEXT, "
            "source_type TEXT, published_at TEXT, fetched_at TEXT)"
        )
        connection.executemany(
            "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "a",
                    "Senate passes bill",
                    "Details",
                    "https://x/a",
                    "wire",
                    "rss",
                    "2026-11-18T10:00:00Z",
                    "2026-11-18T20:00:00Z",
                ),
                (
                    "b",
                    "Storm hits coast",
                    None,
                    "https://x/b",
                    "daily",
                    "gdelt",
                    "2026-11-18T11:00:00Z",
                    "2026-11-18T20:00:00Z",
                ),
                ("c", "  ", None, "https://x/c", "daily", "gdelt", "2026-11-18T12:00:00Z", "2026-11-18T20:00:00Z"),
            ],
        )
    return path


def test_reader_opens_the_database_read_only(database_path):
    reader = ArticleDatabaseReader(database_path)
    assert "mode=ro" in reader.connection_uri()
    assert len(reader.read_articles()) == 3
    with sqlite3.connect(reader.connection_uri(), uri=True) as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM articles")


def test_join_adds_details_and_blank_rows_as_missing(database_path, tmp_path):
    builder = CacheBuilder(Settings(headline_radar_folder=tmp_path, cache_folder=tmp_path / "cache"))
    documents = pd.DataFrame(
        {
            "id": ["a", "b"],
            "published_at": ["2026-11-18T10:00:00Z", "2026-11-18T11:00:00Z"],
            "source": ["wire", "daily"],
            "source_type": ["rss", "gdelt"],
            "text": ["Senate passes bill. Details", "Storm hits coast"],
            "topic_id": [0, -1],
        }
    )
    articles, report = builder.join_articles(documents, ArticleDatabaseReader(database_path).read_articles())
    assert len(articles) == 3
    assert articles.set_index("id").at["c", "topic_id"] == -2
    assert articles.set_index("id").at["a", "title"] == "Senate passes bill"
    assert report["blank_rows_added_as_missing"] == 1


def test_join_refuses_to_multiply_rows(tmp_path):
    builder = CacheBuilder(Settings(headline_radar_folder=tmp_path, cache_folder=tmp_path / "cache"))
    documents = pd.DataFrame(
        {
            "id": ["a"],
            "published_at": [""],
            "source": ["wire"],
            "source_type": ["rss"],
            "text": ["x"],
            "topic_id": [0],
        }
    )
    duplicated = pd.DataFrame(
        {
            "id": ["a", "a"],
            "title": ["x", "y"],
            "description": ["", ""],
            "url": ["", ""],
            "fetched_at": ["", ""],
        }
    )
    with pytest.raises(pd.errors.MergeError):
        builder.join_articles(documents, duplicated)


def test_dates_are_flagged(tmp_path):
    builder = CacheBuilder(Settings(headline_radar_folder=tmp_path, cache_folder=tmp_path / "cache"))
    rows = pd.DataFrame({"published_at": ["2004-03-05T05:00:00Z", "2026-11-18T10:00:00Z", "2026-12-01T05:00:00Z", ""]})
    flagged = builder.flag_dates(rows, pd.Timestamp("2026-11-18T20:00:00Z"))
    assert flagged["date_flag"].tolist() == ["stale", "ok", "future", "unknown"]
