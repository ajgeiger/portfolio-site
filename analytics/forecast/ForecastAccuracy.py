"""Forecast error measures, computed the same way as the source accuracy views."""

import numpy as np
import pandas as pd


class ForecastAccuracy:
    """Score forecasts against actuals.

    MAE and bias are in dollars per MMBtu, MAPE and WAPE in percent. Error is
    forecast minus actual, so a positive bias means forecasts ran high. Every
    measure matches the forecast_accuracy view in natural-gas-forecasting.
    """

    ALL_DAYS = "all days"
    BUCKETS = (("days 1 to 5", 1, 5), ("days 6 to 15", 6, 15), ("days 16 to 30", 16, 30))
    BUCKET_ORDER = tuple(name for name, _, _ in BUCKETS) + (ALL_DAYS,)

    @classmethod
    def bucket(cls, horizon_day: int) -> str:
        for name, first, last in cls.BUCKETS:
            if first <= horizon_day <= last:
                return name
        return "later days"

    @staticmethod
    def errors(frame: pd.DataFrame) -> pd.DataFrame:
        """Add error and absolute error columns."""
        scored = frame.copy()
        scored["error"] = scored["forecast"] - scored["actual"]
        scored["abs_error"] = scored["error"].abs()
        return scored

    @classmethod
    def scores(cls, frame: pd.DataFrame, by: list[str]) -> pd.DataFrame:
        """MAE, RMSE, MAPE, WAPE and bias for each group, with the forecast count."""
        scored = cls.errors(frame)
        scored["pct_error"] = scored["abs_error"] / scored["actual"].abs()
        scored["squared_error"] = scored["error"] ** 2
        scored["abs_actual"] = scored["actual"].abs()
        grouped = scored.groupby(by, sort=False)
        table = pd.DataFrame(
            {
                "forecasts": grouped.size(),
                "mae": grouped["abs_error"].mean(),
                "rmse": np.sqrt(grouped["squared_error"].mean()),
                "mape": 100 * grouped["pct_error"].mean(),
                "wape": 100 * grouped["abs_error"].sum() / grouped["abs_actual"].sum(),
                "bias": grouped["error"].mean(),
            }
        )
        return table.reset_index()

    @classmethod
    def leaderboard(cls, frame: pd.DataFrame) -> pd.DataFrame:
        """Scores by model and horizon bucket, plus an 'all days' row per model."""
        bucketed = frame.assign(horizon_bucket=frame["horizon_day"].map(cls.bucket))
        by_bucket = cls.scores(bucketed, ["model", "horizon_bucket"])
        overall = cls.scores(frame, ["model"]).assign(horizon_bucket=cls.ALL_DAYS)
        table = pd.concat([by_bucket, overall], ignore_index=True)
        table["horizon_bucket"] = pd.Categorical(table["horizon_bucket"], cls.BUCKET_ORDER, ordered=True)
        return table.sort_values(["model", "horizon_bucket"]).reset_index(drop=True)

    @staticmethod
    def improvement(score: float, baseline: float) -> float:
        """Share by which a score beats the baseline, positive when lower is better."""
        return 1 - score / baseline if baseline else 0.0
