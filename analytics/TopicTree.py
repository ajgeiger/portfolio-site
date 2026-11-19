"""Navigate the precomputed topic tree one view at a time."""

import pandas as pd


class TopicTree:
    """Answer questions about the binary topic tree built by TopicTreeBuilder.

    A view shows a node and its branches. Branches are found by opening the
    node into its two children, then repeatedly opening the largest branch
    that is still a group, until there are as many branches as requested.
    This keeps each view readable no matter how deep the binary tree is.
    Branch structure uses the article counts from the fit, so a view does not
    reshape itself when filters change.
    """

    def __init__(self, nodes: pd.DataFrame):
        self.nodes = nodes.set_index("node_key", drop=False)
        self.root_key = str(self.nodes.loc[self.nodes["node_id"].idxmax(), "node_key"])
        self.topic_sets = {key: frozenset(topics) for key, topics in self.nodes["topic_ids"].items()}
        self.base_counts = self.nodes["document_count"].astype(int).to_dict()

    def has(self, key: str) -> bool:
        return key in self.nodes.index

    def is_topic(self, key: str) -> bool:
        return bool(self.nodes.at[key, "is_topic"])

    def topic_ids(self, key: str) -> list[int]:
        return [int(topic) for topic in self.nodes.at[key, "topic_ids"]]

    def keywords(self, key: str) -> list[str]:
        return list(self.nodes.at[key, "keywords"])

    def keyword_name(self, key: str) -> str:
        return str(self.nodes.at[key, "keyword_name"])

    def children(self, key: str) -> list[str]:
        row = self.nodes.loc[key]
        return [child for child in (row["left_key"], row["right_key"]) if child]

    def topic_key(self, topic_id: int) -> str:
        return f"topic_{int(topic_id)}"

    def branches(self, key: str, branch_count: int) -> list[str]:
        """Return up to branch_count node keys that together hold every topic of key."""
        if self.is_topic(key):
            return []
        branches = self.children(key)
        while len(branches) < branch_count:
            groups = [branch for branch in branches if not self.is_topic(branch)]
            if not groups:
                break
            largest = max(groups, key=lambda branch: (self.base_counts[branch], branch))
            position = branches.index(largest)
            branches[position : position + 1] = self.children(largest)
        return sorted(branches, key=lambda branch: (-self.base_counts[branch], branch))

    def contains(self, outer_key: str, inner_key: str) -> bool:
        """True when every topic of inner_key is inside outer_key."""
        return self.topic_sets[inner_key] <= self.topic_sets[outer_key]

    def view_path(self, target_key: str, branch_count: int) -> list[str]:
        """Return the views a user would open to reach target_key from the root."""
        path = [self.root_key]
        while path[-1] != target_key:
            next_key = next(
                (branch for branch in self.branches(path[-1], branch_count) if self.contains(branch, target_key)),
                None,
            )
            if next_key is None:
                break
            path.append(next_key)
        return path

    def largest_topics(self, key: str, counts: pd.Series, limit: int = 8) -> list[int]:
        """Topic ids inside key, largest first by the given counts."""
        topics = pd.Series(counts).reindex(self.topic_ids(key)).fillna(0)
        topics = topics[topics > 0].sort_values(ascending=False, kind="stable")
        return [int(topic) for topic in topics.index[:limit]]

    def group_keys(self) -> list[str]:
        return [str(key) for key in self.nodes.index[~self.nodes["is_topic"]]]
