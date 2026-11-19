"""The live forecast runs: one per scoring day, each with a production and a staging path."""

import pandas as pd


class PredictionRuns:
    """List the runs in the predictions table and return the rows of any one of them."""

    def __init__(self, predictions: pd.DataFrame):
        self.predictions = predictions

    @property
    def empty(self) -> bool:
        return self.predictions.empty

    def runs(self) -> pd.DataFrame:
        """One row per run, newest first, with its as-of date, time and stages."""
        if self.empty:
            return pd.DataFrame(columns=["run_id", "as_of_date", "run_timestamp", "stages", "rows"])
        grouped = self.predictions.groupby("run_id")
        table = pd.DataFrame(
            {
                "as_of_date": grouped["as_of_date"].max(),
                "run_timestamp": grouped["run_timestamp"].min(),
                "stages": grouped["stage"].agg(lambda stages: ", ".join(sorted(stages.unique()))),
                "rows": grouped.size(),
            }
        ).reset_index()
        return table.sort_values(["as_of_date", "run_timestamp"], ascending=False).reset_index(drop=True)

    def latest_run_id(self) -> str | None:
        runs = self.runs()
        return None if runs.empty else str(runs.iloc[0]["run_id"])

    def run(self, run_id: str | None) -> pd.DataFrame:
        rows = self.predictions[self.predictions["run_id"] == run_id]
        return rows.sort_values(["stage", "horizon_day"]).reset_index(drop=True)

    def stage(self, run_id: str | None, stage: str) -> pd.DataFrame:
        rows = self.run(run_id)
        return rows[rows["stage"] == stage].reset_index(drop=True)
