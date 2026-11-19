"""Small, hand made fixtures so tests never depend on the real 41k article corpus."""

import pandas as pd
import pytest
from scipy import sparse

from analytics.KeywordNamer import KeywordNamer
from analytics.TopicTreeBuilder import TopicTreeBuilder
from data.FrameDataSource import FrameDataSource

LOAD_TIME = pd.Timestamp("2026-11-18 22:00", tz="UTC")

VOCABULARY = ["election", "senate", "vote", "football", "cup", "goal", "storm", "rain"]

# One row per topic. Topics 0 and 1 talk politics, 2 and 3 talk football, 4 talks weather.
PROFILES = [
    [0.9, 0.6, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.7, 0.8, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.9, 0.6, 0.4, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.6, 0.9, 0.5, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9, 0.7],
]

TOPIC_WORDS = {
    topic: [(VOCABULARY[column], score) for column, score in sorted(enumerate(row), key=lambda item: -item[1]) if score]
    for topic, row in enumerate(PROFILES)
}
TOPIC_WORDS[-1] = [("new", 0.5), ("year", 0.4)]
TOPIC_SIZES = {0: 6, 1: 4, 2: 5, 3: 3, 4: 2, -1: 4}


def make_articles() -> pd.DataFrame:
    """Twenty four articles: twenty in topics or unassigned, plus two blank rows and two old dates."""
    rows = []
    number = 0
    for topic, size in TOPIC_SIZES.items():
        for index in range(size):
            hours_back = 1 + (index * 5) % 20
            rows.append(
                {
                    "id": f"article_{number}",
                    "topic_id": topic,
                    "published_at": LOAD_TIME - pd.Timedelta(hours=hours_back),
                    "source": "wire.example" if index % 2 else "daily.example",
                    "source_type": "rss" if index % 3 == 0 else "gdelt",
                    "title": f"Headline {number} about topic {topic}",
                    "summary": f"Summary {number}",
                    "url": f"https://news.example/{number}",
                    "has_text": True,
                    "is_repeat_text": False,
                    "date_flag": "ok",
                }
            )
            number += 1
    for index in range(2):
        rows.append(
            {
                "id": f"blank_{index}",
                "topic_id": -2,
                "published_at": LOAD_TIME - pd.Timedelta(hours=2),
                "source": "daily.example",
                "source_type": "gdelt",
                "title": "",
                "summary": "",
                "url": "",
                "has_text": False,
                "is_repeat_text": False,
                "date_flag": "ok",
            }
        )
    articles = pd.DataFrame(rows)
    articles.loc[0, "published_at"] = pd.Timestamp("2004-03-05", tz="UTC")
    articles.loc[0, "date_flag"] = "stale"
    return articles


def make_topics() -> pd.DataFrame:
    rows = []
    namer = KeywordNamer()
    for topic in [-1, 0, 1, 2, 3, 4]:
        keywords = [word for word, _ in TOPIC_WORDS[topic]]
        rows.append(
            {
                "topic_id": topic,
                "document_count": TOPIC_SIZES[topic],
                "keywords": keywords,
                "keyword_scores": [score for _, score in TOPIC_WORDS[topic]],
                "keyword_name": namer.name(keywords) if topic >= 0 else "Unassigned",
                "representative_ids": [],
            }
        )
    topics = pd.DataFrame(rows)
    topics.at[1, "representative_ids"] = ["article_5"]
    return topics


@pytest.fixture
def tree() -> pd.DataFrame:
    builder = TopicTreeBuilder(latent_themes=3)
    counts = {topic: size for topic, size in TOPIC_SIZES.items() if topic >= 0}
    return builder.build(sparse.csr_matrix(PROFILES), [0, 1, 2, 3, 4], counts, TOPIC_WORDS)


@pytest.fixture
def articles() -> pd.DataFrame:
    return make_articles()


@pytest.fixture
def data_source(tree, articles) -> FrameDataSource:
    metadata = {
        "last_load_time": LOAD_TIME.isoformat(),
        "article_rows": len(articles),
        "rows_with_text": int(articles["has_text"].sum()),
        "topic_count": 5,
        "repeat_text_rows": 0,
        "earliest_published": str(articles["published_at"].min()),
        "stale_date_rows": 1,
        "future_date_rows": 0,
        "stale_after_days": 30,
    }
    return FrameDataSource(articles, make_topics(), tree, metadata, name="Test data")
