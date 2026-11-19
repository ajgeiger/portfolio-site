"""Read the fitted attributes stored in the Headline Radar topic model file."""

from pathlib import Path

import joblib
from scipy import sparse


class TopicModelReader:
    """Load topic_model.joblib and expose the attributes the explorer needs.

    The file holds the fitted TopicModel attributes as a dictionary. Loading it
    needs the same libraries the model was fit with (umap-learn, hdbscan and
    scikit-learn) because the reducer and clusterer are pickled objects. This
    class only reads attributes. It never fits, refits or predicts.

    joblib uses pickle, so only load model files you created yourself.
    """

    REQUIRED_ATTRIBUTES = ["topic_ids_", "c_tf_idf_", "topic_words_", "example_documents_"]

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self.state = None

    def load(self) -> "TopicModelReader":
        """Read the model file once and check that it has every attribute."""
        state = joblib.load(self.model_path)
        missing = [name for name in self.REQUIRED_ATTRIBUTES if state.get(name) is None]
        if missing:
            raise ValueError(f"The model file is missing fitted attributes: {missing}")
        self.state = state
        return self

    def topic_ids(self) -> list[int]:
        """Topic ids in the same order as the rows of the c-TF-IDF matrix."""
        return [int(topic) for topic in self.state["topic_ids_"]]

    def keyword_profiles(self) -> sparse.csr_matrix:
        """The c-TF-IDF matrix: one row per topic, one column per word or phrase."""
        return sparse.csr_matrix(self.state["c_tf_idf_"])

    def topic_words(self) -> dict[int, list[tuple[str, float]]]:
        """{topic id: [(keyword, score), ...]} with the best keyword first."""
        return {int(topic): list(words) for topic, words in self.state["topic_words_"].items()}

    def example_documents(self) -> dict[int, list[str]]:
        """{topic id: representative texts chosen by the model}."""
        return {int(topic): list(texts) for topic, texts in self.state["example_documents_"].items()}

    def saved_labels(self) -> dict[int, str]:
        """Custom labels stored in the model, if any were set with set_topic_labels."""
        return {int(topic): str(label) for topic, label in (self.state.get("topic_labels_") or {}).items()}
