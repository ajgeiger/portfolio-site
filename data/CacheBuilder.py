"""Join the Headline Radar outputs once and save small tables the app can load fast."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from analytics.KeywordNamer import KeywordNamer
from analytics.TopicTreeBuilder import TopicTreeBuilder
from config.Settings import Settings
from data.ArticleDatabaseReader import ArticleDatabaseReader
from data.TopicModelReader import TopicModelReader
from data.TopicOutputReader import TopicOutputReader


class CacheBuilder:
    """Build the cache folder from fitted outputs. Nothing is fit or refit.

    Files written:
        articles.parquet   one row per article with topic, date, source and headline
        topics.parquet     one row per topic with keywords and representative articles
        tree.parquet       one row per node of the topic tree
        metadata.json      fit totals, data quirks and the time of the last load
    """

    OUTLIER_TOPIC = -1
    BLANK_TOPIC = -2
    STALE_AFTER_DAYS = 30

    ARTICLES_FILE = "articles.parquet"
    TOPICS_FILE = "topics.parquet"
    TREE_FILE = "tree.parquet"
    METADATA_FILE = "metadata.json"

    def __init__(self, settings: Settings, namer: KeywordNamer | None = None):
        self.settings = settings
        self.namer = namer or KeywordNamer()
        self.outputs = TopicOutputReader(
            settings.document_topics_path, settings.topic_info_path, settings.fit_diagnostics_path
        )
        self.database = ArticleDatabaseReader(settings.database_path)
        self.model = TopicModelReader(settings.model_path)

    def build(self) -> dict:
        """Read every source, write the cache files and return the metadata."""
        documents = self.outputs.read_document_topics()
        database_articles = self.database.read_articles()
        self.model.load()

        articles, join_report = self.join_articles(documents, database_articles)
        load_time = pd.to_datetime(database_articles["fetched_at"], utc=True, errors="coerce").max()
        articles = self.flag_dates(articles, load_time)
        topics = self.build_topics(documents)
        tree = self.build_tree(topics)
        metadata = self.build_metadata(articles, topics, join_report, load_time)

        folder = Path(self.settings.cache_folder)
        folder.mkdir(parents=True, exist_ok=True)
        articles.to_parquet(folder / self.ARTICLES_FILE, index=False)
        topics.to_parquet(folder / self.TOPICS_FILE, index=False)
        tree.to_parquet(folder / self.TREE_FILE, index=False)
        (folder / self.METADATA_FILE).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata

    def join_articles(self, documents: pd.DataFrame, database_articles: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        """Add headline, summary and link to every fitted article.

        The join is on article id with validate="many_to_one", so pandas raises
        if an id repeats on the database side and rows can never multiply.
        Database rows with a blank title were never sent to the model. They are
        added back with topic -2 so they show up as Missing text.
        """
        details = database_articles[["id", "title", "description", "url", "fetched_at"]]
        joined = documents.merge(details, on="id", how="left", validate="many_to_one")
        if len(joined) != len(documents):
            raise ValueError("The join changed the number of rows.")

        not_fitted = database_articles[~database_articles["id"].isin(documents["id"])]
        is_blank = not_fitted["title"].fillna("").str.strip().eq("")
        blank_rows = not_fitted[is_blank].assign(text="", topic_id=self.BLANK_TOPIC)
        report = {
            "fitted_rows": int(len(documents)),
            "fitted_rows_without_database_match": int(joined["title"].isna().sum()),
            "database_rows": int(len(database_articles)),
            "blank_rows_added_as_missing": int(len(blank_rows)),
            "database_rows_with_text_not_in_fit": int((~is_blank).sum()),
        }

        columns = ["id", "published_at", "source", "source_type", "text", "topic_id", "title", "description", "url"]
        articles = pd.concat([joined[columns], blank_rows[columns]], ignore_index=True)
        articles = articles.rename(columns={"description": "summary"})
        articles["title"] = articles["title"].fillna("").str.strip()
        articles["summary"] = articles["summary"].fillna("").str.strip()
        articles["url"] = articles["url"].fillna("")
        articles["source"] = articles["source"].replace("", pd.NA).fillna("Unknown source")
        articles["has_text"] = articles["text"].fillna("").str.strip().ne("")
        articles["topic_id"] = articles["topic_id"].astype(int)
        articles["is_repeat_text"] = articles["has_text"] & articles["text"].duplicated(keep="first")
        return articles, report

    def flag_dates(self, articles: pd.DataFrame, load_time: pd.Timestamp) -> pd.DataFrame:
        """Parse publish dates and flag the ones that cannot be right.

        Future means published after the last load. Stale means published more
        than STALE_AFTER_DAYS before the last load, usually an old page that a
        feed picked up again.
        """
        articles = articles.copy()
        published = pd.to_datetime(articles["published_at"], utc=True, errors="coerce")
        articles["published_at"] = published
        stale_before = load_time - pd.Timedelta(days=self.STALE_AFTER_DAYS)
        articles["date_flag"] = "ok"
        articles.loc[published.isna(), "date_flag"] = "unknown"
        articles.loc[published < stale_before, "date_flag"] = "stale"
        articles.loc[published > load_time, "date_flag"] = "future"
        return articles

    def build_topics(self, documents: pd.DataFrame) -> pd.DataFrame:
        """One row per topic with keywords, a keyword name and representative article ids."""
        counts = documents["topic_id"].value_counts()
        first_id_by_text = documents.drop_duplicates("text").set_index("text")["id"]
        topic_words = self.model.topic_words()
        examples = self.model.example_documents()

        rows = []
        for topic in self.model.topic_ids():
            keywords = self.namer.remove_overlaps([word for word, _ in topic_words.get(topic, [])])
            representative_ids = [
                first_id_by_text[text] for text in examples.get(topic, []) if text in first_id_by_text
            ]
            rows.append(
                {
                    "topic_id": topic,
                    "document_count": int(counts.get(topic, 0)),
                    "keywords": keywords,
                    "keyword_scores": [float(score) for _, score in topic_words.get(topic, [])],
                    "keyword_name": self.namer.name(keywords) if topic >= 0 else "Unassigned",
                    "representative_ids": [str(article_id) for article_id in representative_ids],
                }
            )
        return pd.DataFrame(rows)

    def build_tree(self, topics: pd.DataFrame) -> pd.DataFrame:
        """Merge assigned topics by keyword profile into the topic tree."""
        all_topic_ids = self.model.topic_ids()
        rows = [row for row, topic in enumerate(all_topic_ids) if topic >= 0]
        topic_ids = [all_topic_ids[row] for row in rows]
        profiles = self.model.keyword_profiles()[rows]
        counts = topics.set_index("topic_id")["document_count"].to_dict()
        return TopicTreeBuilder(self.namer).build(profiles, topic_ids, counts, self.model.topic_words())

    def build_metadata(self, articles: pd.DataFrame, topics: pd.DataFrame, join_report: dict, load_time) -> dict:
        """Totals and data quirks shown in the method notes."""
        ok_dates = articles.loc[articles["date_flag"] == "ok", "published_at"]
        flags = articles["date_flag"].value_counts()
        topic_info = self.outputs.read_topic_info().set_index("topic_id")["document_count"]
        diagnostics = self.outputs.read_fit_diagnostics()
        check = topics.set_index("topic_id")["document_count"]
        return {
            "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "source_folder": str(self.settings.headline_radar_folder),
            "last_load_time": load_time.isoformat(),
            "article_rows": int(len(articles)),
            "rows_with_text": int(articles["has_text"].sum()),
            "topic_count": int((topics["topic_id"] >= 0).sum()),
            "unassigned_rows": int((articles["topic_id"] == self.OUTLIER_TOPIC).sum()),
            "missing_rows": int((articles["topic_id"] == self.BLANK_TOPIC).sum()),
            "repeat_text_rows": int(articles["is_repeat_text"].sum()),
            "earliest_published": str(articles["published_at"].min()),
            "latest_published": str(articles["published_at"].max()),
            "earliest_recent_published": str(ok_dates.min()),
            "stale_date_rows": int(flags.get("stale", 0)),
            "future_date_rows": int(flags.get("future", 0)),
            "unknown_date_rows": int(flags.get("unknown", 0)),
            "stale_after_days": self.STALE_AFTER_DAYS,
            "hdbscan_clusters": int((diagnostics["cluster_id"] >= 0).sum()),
            "clusters_kept_as_topics": int(diagnostics["kept"].sum()),
            "topic_info_counts_match": bool(topic_info.reindex(check.index).eq(check).all()),
            "labels_saved_in_model": {str(topic): label for topic, label in self.model.saved_labels().items()},
            "join": join_report,
        }
