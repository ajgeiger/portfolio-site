"""Answer every question the topic explorer page asks about the data."""

import pandas as pd

from analytics.ArticleFilter import ArticleFilter
from analytics.CoverageSummary import CoverageSummary
from analytics.LabelStore import LabelStore
from analytics.TopicTree import TopicTree
from data.AbstractDataSource import AbstractDataSource


class ExplorerQuery:
    """Join the article table, topic table and topic tree behind one simple interface.

    Every view is identified by a node key:
        all_topics    the whole corpus, the starting view
        assigned      every article that landed in a topic
        unassigned    topic -1, one off or vague stories
        missing       topic -2, articles with a blank headline
        group_<n>     a group of similar topics from the tree
        topic_<n>     a single topic
    """

    ALL = "all_topics"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    MISSING = "missing"
    OUTLIER_TOPIC = -1
    BLANK_TOPIC = -2

    KINDS = {ALL: "Overview", ASSIGNED: "Topic group", UNASSIGNED: "Unassigned", MISSING: "Missing"}
    NAMES = {ALL: "All topics", ASSIGNED: "Assigned topics", UNASSIGNED: "Unassigned", MISSING: "Missing text"}

    def __init__(self, data_source: AbstractDataSource, random_state: int = 42):
        self.data_source = data_source
        self.random_state = random_state
        self.articles = data_source.articles()
        self.article_index = self.articles.set_index("id", drop=False)
        self.topics = data_source.topics().set_index("topic_id", drop=False)
        self.tree = TopicTree(data_source.tree())
        self.metadata = data_source.metadata()
        self.last_load_time = pd.Timestamp(self.metadata["last_load_time"])

    # Filtering and counting

    def filtered(self, article_filter: ArticleFilter) -> pd.DataFrame:
        return article_filter.apply(self.articles)

    @staticmethod
    def topic_counts(articles: pd.DataFrame) -> pd.Series:
        return articles["topic_id"].value_counts()

    def tree_key(self, key: str) -> str:
        """The tree node behind a view. The two overview keys use the tree root."""
        return self.tree.root_key if key in (self.ALL, self.ASSIGNED) else key

    def count(self, key: str, counts: pd.Series, summary: CoverageSummary) -> int:
        if key == self.ALL:
            return summary.total_rows
        if key == self.UNASSIGNED:
            return int(counts.get(self.OUTLIER_TOPIC, 0))
        if key == self.MISSING:
            return int(counts.get(self.BLANK_TOPIC, 0))
        return int(counts.reindex(self.tree.topic_ids(self.tree_key(key))).fillna(0).sum())

    def share_base(self, key: str, summary: CoverageSummary) -> int:
        """The denominator for a node's share: every row for missing and the overview, text rows otherwise."""
        return summary.total_rows if key in (self.ALL, self.MISSING) else summary.rows_with_text

    def rows(self, key: str, articles: pd.DataFrame) -> pd.DataFrame:
        if key == self.ALL:
            return articles
        if key == self.UNASSIGNED:
            return articles[articles["topic_id"] == self.OUTLIER_TOPIC]
        if key == self.MISSING:
            return articles[articles["topic_id"] == self.BLANK_TOPIC]
        return articles[articles["topic_id"].isin(self.tree.topic_ids(self.tree_key(key)))]

    # Describing a node

    def is_known(self, key: str) -> bool:
        return key in self.KINDS or self.tree.has(key)

    def kind(self, key: str) -> str:
        if key in self.KINDS:
            return self.KINDS[key]
        return "Individual topic" if self.tree.is_topic(key) else "Topic group"

    def keyword_name(self, key: str) -> str:
        if key in self.NAMES:
            return self.NAMES[key]
        return self.tree.keyword_name(key)

    def name(self, key: str, labels: LabelStore) -> str:
        return labels.label(key, self.keyword_name(key))

    def keywords(self, key: str) -> list[str]:
        if key == self.MISSING:
            return []
        if key == self.UNASSIGNED:
            return (
                list(self.topics.at[self.OUTLIER_TOPIC, "keywords"]) if self.OUTLIER_TOPIC in self.topics.index else []
            )
        return self.tree.keywords(self.tree_key(key))

    def kicker(self, key: str) -> str:
        """The small upper case line on a card, such as TOPIC 12 or 14 TOPICS."""
        if key == self.UNASSIGNED:
            return "TOPIC -1"
        if key == self.MISSING:
            return "BLANK TEXT"
        tree_key = self.tree_key(key)
        if self.tree.is_topic(tree_key):
            return f"TOPIC {self.tree.topic_ids(tree_key)[0]}"
        return f"{len(self.tree.topic_ids(tree_key))} TOPICS"

    def shows_headlines(self, key: str) -> bool:
        """Single topics, unassigned and missing open into headlines rather than branches."""
        return key in (self.UNASSIGNED, self.MISSING) or (self.tree.has(key) and self.tree.is_topic(key))

    # Navigation

    def branch_keys(self, key: str, branch_count: int, counts: pd.Series, summary: CoverageSummary) -> list[str]:
        """Branches to draw around the hub, largest first, without empty ones."""
        if self.shows_headlines(key):
            return []
        keys = self.tree.branches(self.tree_key(key), branch_count)
        keys = sorted(keys, key=lambda branch: -self.count(branch, counts, summary))
        if key == self.ALL:
            keys += [self.UNASSIGNED, self.MISSING]
        return [branch for branch in keys if self.count(branch, counts, summary) > 0]

    def path_to(self, key: str, branch_count: int) -> list[str]:
        """The breadcrumb path a user would follow to reach key from the start."""
        if key == self.ALL:
            return [self.ALL]
        if key in self.KINDS:
            return [self.ALL, key]
        return [self.ALL] + self.tree.view_path(key, branch_count)[1:]

    def largest_topics(self, key: str, counts: pd.Series, limit: int = 8) -> list[str]:
        if key in (self.UNASSIGNED, self.MISSING):
            return []
        topics = self.tree.largest_topics(self.tree_key(key), counts, limit)
        return [self.tree.topic_key(topic) for topic in topics]

    # Headlines

    def article(self, article_id: str) -> dict | None:
        if article_id not in self.article_index.index:
            return None
        return self.article_index.loc[article_id].to_dict()

    def representative_ids(self, key: str, counts: pd.Series) -> list[str]:
        """Model chosen examples: from the topic itself, or the first example of each large topic."""
        if key == self.MISSING:
            return []
        if key == self.UNASSIGNED:
            topics = [self.OUTLIER_TOPIC]
        else:
            topics = self.tree.largest_topics(self.tree_key(key), counts, limit=8)
        if len(topics) == 1:
            return list(self.topics.at[topics[0], "representative_ids"])
        return [ids[0] for ids in (self.topics.at[topic, "representative_ids"] for topic in topics) if len(ids)]

    def headlines(self, key: str, articles: pd.DataFrame, limit: int) -> list[dict]:
        """Example headlines for a node: representative ones first, then a random sample.

        Repeated headlines (syndicated copies) are shown once.
        """
        node_rows = self.rows(key, articles)
        counts = self.topic_counts(articles)
        visible_ids = set(node_rows["id"])
        picked, seen_titles = [], set()

        for article_id in self.representative_ids(key, counts):
            if article_id in visible_ids and len(picked) < limit:
                row = self.article_index.loc[article_id]
                if row["title"] not in seen_titles:
                    picked.append(self.headline(row, "Representative"))
                    seen_titles.add(row["title"])

        if len(picked) < limit and len(node_rows):
            pool = node_rows.drop_duplicates("title") if key != self.MISSING else node_rows
            pool = pool[~pool["title"].isin(seen_titles) | (key == self.MISSING)]
            sample = pool.sample(min(len(pool), limit - len(picked)), random_state=self.random_state)
            picked.extend(self.headline(row, "Sampled") for _, row in sample.iterrows())
        return picked

    @staticmethod
    def headline(row: pd.Series, tag: str) -> dict:
        return {
            "id": row["id"],
            "title": row["title"] or "Untitled article",
            "source": row["source"],
            "published_at": row["published_at"],
            "tag": tag,
        }
