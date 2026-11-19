from analytics.TopicTree import TopicTree


def test_similar_topics_merge_first(tree):
    first_two_merges = tree[~tree["is_topic"]].sort_values("node_id").head(2)
    merged = {frozenset(topics) for topics in first_two_merges["topic_ids"]}
    assert frozenset({0, 1}) in merged
    assert frozenset({2, 3}) in merged


def test_root_holds_every_topic_and_counts_add_up(tree):
    navigator = TopicTree(tree)
    assert sorted(navigator.topic_ids(navigator.root_key)) == [0, 1, 2, 3, 4]
    assert navigator.base_counts[navigator.root_key] == 20


def test_branches_open_the_largest_group_until_the_count_is_reached(tree):
    navigator = TopicTree(tree)
    two = navigator.branches(navigator.root_key, 2)
    five = navigator.branches(navigator.root_key, 5)
    assert len(two) == 2
    assert sorted(five) == [f"topic_{topic}" for topic in range(5)]
    assert navigator.branches("topic_0", 6) == []


def test_view_path_reaches_a_topic(tree):
    navigator = TopicTree(tree)
    path = navigator.view_path("topic_3", 2)
    assert path[0] == navigator.root_key
    assert path[-1] == "topic_3"


def test_group_names_differ_from_names_inside_them(tree):
    navigator = TopicTree(tree)
    for key in navigator.group_keys():
        inner = {navigator.keyword_name(f"topic_{topic}") for topic in navigator.topic_ids(key)}
        assert navigator.keyword_name(key) not in inner
