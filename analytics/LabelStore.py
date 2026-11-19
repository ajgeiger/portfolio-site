"""Keep plain language labels that replace keyword names during a session."""

import csv
import io
import json


class LabelStore:
    """Hold renamed labels for topics and topic groups.

    Labels live in the browser session only. Export writes them in a format
    the Headline Radar pipeline can read on its next run:

        topic_labels.json   {"0": "Crime and arrests", "12": "GTA VI launch"}
            Load with: model.set_topic_labels({int(k): v for k, v in json.load(file).items()})
        topic_labels.csv    node_key, kind, topic_id, keyword_name, label
            One row per renamed topic or group. Topic rows carry topic_id.
    """

    TOPIC_PREFIX = "topic_"

    def __init__(self, labels: dict | None = None):
        self.labels = {str(key): str(label) for key, label in (labels or {}).items() if str(label).strip()}

    def rename(self, key: str, label: str | None) -> dict:
        """Return the labels with key renamed. A blank label restores the keyword name."""
        labels = dict(self.labels)
        label = (label or "").strip()
        if label:
            labels[key] = label
        else:
            labels.pop(key, None)
        return labels

    def label(self, key: str, default: str) -> str:
        return self.labels.get(key, default)

    def is_renamed(self, key: str) -> bool:
        return key in self.labels

    def topic_labels(self) -> dict[int, str]:
        """{topic id: label} for renamed topics only, ready for TopicModel.set_topic_labels."""
        return {
            int(key.removeprefix(self.TOPIC_PREFIX)): label
            for key, label in self.labels.items()
            if key.startswith(self.TOPIC_PREFIX)
        }

    def to_json(self) -> str:
        topic_labels = dict(sorted(self.topic_labels().items()))
        return json.dumps({str(topic): label for topic, label in topic_labels.items()}, indent=2)

    def to_csv(self, keyword_names: dict[str, str]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["node_key", "kind", "topic_id", "keyword_name", "label"])
        for key, label in sorted(self.labels.items()):
            is_topic = key.startswith(self.TOPIC_PREFIX)
            topic_id = key.removeprefix(self.TOPIC_PREFIX) if is_topic else ""
            writer.writerow([key, "topic" if is_topic else "group", topic_id, keyword_names.get(key, ""), label])
        return buffer.getvalue()
