"""Show which sources cover the current selection."""

import pandas as pd


class SourceMix:
    """Count articles by source and fold the long tail into one row."""

    OTHER_LABEL = "All other sources"

    def __init__(self, top_count: int = 8):
        self.top_count = top_count

    def table(self, articles: pd.DataFrame) -> pd.DataFrame:
        """Return source, count and share, largest first, with the tail combined."""
        counts = articles["source"].value_counts()
        top = counts.head(self.top_count)
        rows = [{"source": source, "count": int(count)} for source, count in top.items()]
        other = int(counts.iloc[self.top_count :].sum())
        if other:
            rows.append({"source": f"{self.OTHER_LABEL} ({len(counts) - self.top_count:,})", "count": other})
        table = pd.DataFrame(rows, columns=["source", "count"])
        total = int(counts.sum())
        table["share"] = table["count"] / total if total else 0.0
        return table
