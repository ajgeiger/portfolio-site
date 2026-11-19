"""Build the topic tree from the c-TF-IDF keyword profiles of the fitted topics."""

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.cluster.hierarchy import linkage
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from analytics.KeywordNamer import KeywordNamer


class TopicTreeBuilder:
    """Merge the most similar topics step by step into a binary tree.

    Each topic is represented by its c-TF-IDF keyword profile. Raw profiles
    share very few exact words, so on their own nearly every pair looks equally
    far apart and the tree turns into one long chain. The profiles are first
    projected onto a small number of latent themes (truncated SVD, also known
    as latent semantic analysis), so topics that use related words end up
    close. The projected profiles are scaled to unit length, which makes
    Euclidean distance a function of cosine similarity, and Ward linkage then
    merges the pair of clusters that adds the least spread, one merge at a time.

    Group names combine the keywords of their topics, weighted by article
    count. A group never reuses a name from inside its own branch, so the
    breadcrumb trail always reads as distinct steps.

    The result is a table with one row per node. Leaves are topics and every
    other node is a group of topics. The last node is the root.
    """

    def __init__(self, namer: KeywordNamer | None = None, latent_themes: int = 30, random_state: int = 42):
        self.namer = namer or KeywordNamer()
        self.latent_themes = latent_themes
        self.random_state = random_state

    def build(
        self,
        profiles: sparse.spmatrix,
        topic_ids: list[int],
        document_counts: dict[int, int],
        topic_words: dict[int, list[tuple[str, float]]],
    ) -> pd.DataFrame:
        """Return the node table.

        Args:
            profiles: c-TF-IDF matrix with one row per topic in topic_ids.
            topic_ids: Topic ids for the rows of profiles. Use topics >= 0 only.
            document_counts: {topic id: number of articles}.
            topic_words: {topic id: [(keyword, score), ...]}.
        """
        if len(topic_ids) < 2:
            raise ValueError("At least two topics are needed to build a tree.")
        merges = self.merge_order(profiles)

        nodes = [self.leaf_row(index, topic, document_counts, topic_words) for index, topic in enumerate(topic_ids)]
        for step, (left, right, distance, _) in enumerate(merges):
            node_id = len(topic_ids) + step
            nodes.append(
                self.group_row(node_id, nodes[int(left)], nodes[int(right)], distance, document_counts, topic_words)
            )

        table = pd.DataFrame(nodes).drop(columns="inner_names")
        table["topic_id"] = table["topic_id"].astype("Int64")
        parent_of = {}
        for row in nodes:
            for child in (row["left_key"], row["right_key"]):
                if child:
                    parent_of[child] = row["node_key"]
        table["parent_key"] = table["node_key"].map(parent_of).fillna("")
        return table

    def merge_order(self, profiles: sparse.spmatrix) -> np.ndarray:
        """Return the scipy linkage matrix for Ward merges on projected, unit length profiles."""
        unit_profiles = normalize(sparse.csr_matrix(profiles, dtype=np.float64), norm="l2", axis=1)
        components = min(self.latent_themes, unit_profiles.shape[0] - 1, unit_profiles.shape[1] - 1)
        if components >= 2:
            projected = TruncatedSVD(components, random_state=self.random_state).fit_transform(unit_profiles)
        else:
            projected = unit_profiles.toarray()
        return linkage(normalize(projected, norm="l2", axis=1), method="ward")

    def leaf_row(self, node_id: int, topic: int, document_counts: dict, topic_words: dict) -> dict:
        keywords = self.namer.remove_overlaps([word for word, _ in topic_words.get(topic, [])])
        return {
            "node_id": node_id,
            "node_key": f"topic_{topic}",
            "topic_id": topic,
            "is_topic": True,
            "left_key": "",
            "right_key": "",
            "topic_ids": [topic],
            "document_count": int(document_counts.get(topic, 0)),
            "keywords": keywords,
            "keyword_name": self.namer.name(keywords),
            "merge_distance": 0.0,
            "inner_names": set(),
        }

    def group_row(
        self, node_id: int, left: dict, right: dict, distance: float, document_counts: dict, topic_words: dict
    ) -> dict:
        topics = left["topic_ids"] + right["topic_ids"]
        weighted = [(topic_words.get(topic, []), document_counts.get(topic, 0)) for topic in topics]
        keywords = self.namer.combine(weighted)
        inner_names = left["inner_names"] | right["inner_names"] | {left["keyword_name"], right["keyword_name"]}
        name = self.namer.name(keywords, avoid=inner_names)
        return {
            "node_id": node_id,
            "node_key": f"group_{node_id}",
            "topic_id": None,
            "is_topic": False,
            "left_key": left["node_key"],
            "right_key": right["node_key"],
            "topic_ids": topics,
            "document_count": left["document_count"] + right["document_count"],
            "keywords": keywords,
            "keyword_name": name,
            "merge_distance": float(distance),
            "inner_names": inner_names | {name},
        }
