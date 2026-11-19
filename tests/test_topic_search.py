from analytics.TopicSearch import TopicSearch


def test_search_by_topic_id(tree):
    results = TopicSearch(tree).search("3")
    assert [result["key"] for result in results] == ["topic_3"]


def test_search_by_keyword_finds_topics_and_groups(tree):
    keys = [result["key"] for result in TopicSearch(tree).search("football")]
    assert "topic_2" in keys
    assert any(key.startswith("group_") for key in keys)


def test_search_by_renamed_label(tree):
    results = TopicSearch(tree).search("weather", {"topic_4": "Weather alerts"})
    assert results[0]["key"] == "topic_4"
    assert "Weather alerts" in results[0]["label"]
