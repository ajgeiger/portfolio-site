import csv
import io
import json

from analytics.LabelStore import LabelStore


def test_rename_and_reset():
    labels = LabelStore().rename("topic_3", "  Weather alerts ")
    assert labels == {"topic_3": "Weather alerts"}
    assert LabelStore(labels).rename("topic_3", "") == {}


def test_json_export_matches_set_topic_labels():
    store = LabelStore({"topic_12": "Celebrity births", "topic_0": "Crime", "group_40": "Politics"})
    loaded = {int(topic): label for topic, label in json.loads(store.to_json()).items()}
    assert loaded == {0: "Crime", 12: "Celebrity births"}


def test_csv_export_lists_topics_and_groups():
    store = LabelStore({"topic_0": "Crime", "group_40": "Politics"})
    rows = list(csv.DictReader(io.StringIO(store.to_csv({"topic_0": "Man, Police"}))))
    assert {row["kind"] for row in rows} == {"topic", "group"}
    topic_row = next(row for row in rows if row["kind"] == "topic")
    assert topic_row["topic_id"] == "0"
    assert topic_row["keyword_name"] == "Man, Police"
