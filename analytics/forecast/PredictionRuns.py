"""The production scoring runs: each one scores every contender and publishes a stitched forecast."""

import pandas as pd

from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from config.ForecastModels import ForecastModels


class PredictionRuns:
    """List the runs that published a production forecast and return the rows of any one of them.

    Runs from before the tournament only carry legacy stages, so they are not listed.
    """

    def __init__(self, predictions: pd.DataFrame):
        self.predictions = predictions

    @property
    def published(self) -> pd.DataFrame:
        return self.predictions[self.predictions["stage"] == ForecastModels.PRODUCTION]

    @property
    def empty(self) -> bool:
        return self.published.empty

    def runs(self) -> pd.DataFrame:
        """One row per published run, newest first, with its as-of date, time and contender count."""
        if self.empty:
            return pd.DataFrame(columns=["run_id", "as_of_date", "run_timestamp", "contenders"])
        run_ids = self.published["run_id"].unique()
        grouped = self.predictions[self.predictions["run_id"].isin(run_ids)].groupby("run_id")
        table = pd.DataFrame(
            {
                "as_of_date": grouped["as_of_date"].max(),
                "run_timestamp": grouped["run_timestamp"].min(),
                "contenders": grouped["stage"].agg(self.contender_count),
            }
        ).reset_index()
        return table.sort_values(["as_of_date", "run_timestamp"], ascending=False).reset_index(drop=True)

    @staticmethod
    def contender_count(stages: pd.Series) -> int:
        """How many contender stages a run scored, not counting the published production stage."""
        return int(stages[stages != ForecastModels.PRODUCTION].nunique())

    def latest_run_id(self) -> str | None:
        runs = self.runs()
        return None if runs.empty else str(runs.iloc[0]["run_id"])

    def run(self, run_id: str | None) -> pd.DataFrame:
        rows = self.predictions[self.predictions["run_id"] == run_id]
        return rows.sort_values(["stage", "horizon_day"]).reset_index(drop=True)

    def stage(self, run_id: str | None, stage: str) -> pd.DataFrame:
        rows = self.run(run_id)
        return rows[rows["stage"] == stage].sort_values("horizon_day").reset_index(drop=True)

    def production(self, run_id: str | None) -> pd.DataFrame:
        return self.stage(run_id, ForecastModels.PRODUCTION)

    @staticmethod
    def segments(production: pd.DataFrame) -> pd.DataFrame:
        """One row per horizon event in a production forecast: its days and the model that won it."""
        if production.empty:
            return pd.DataFrame(columns=["horizon_bucket", "first_day", "last_day", "model", "model_version"])
        rows = production.assign(horizon_bucket=production["horizon_day"].map(ForecastAccuracy.bucket))
        grouped = rows.groupby("horizon_bucket", sort=False)
        table = pd.DataFrame(
            {
                "first_day": grouped["horizon_day"].min(),
                "last_day": grouped["horizon_day"].max(),
                "model": grouped["model"].first(),
                "model_version": grouped["model_version"].first(),
            }
        ).reset_index()
        return table.sort_values("first_day").reset_index(drop=True)
