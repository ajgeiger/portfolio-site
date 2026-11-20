"""The headline numbers for the natural gas forecast, read from the snapshot."""

from dataclasses import dataclass

import pandas as pd

from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.PredictionRuns import PredictionRuns
from config.ForecastModels import ForecastModels


@dataclass(frozen=True)
class ForecastSummary:
    """Champion against baseline on MAE, MAPE, WAPE and bias, the backtest size and the latest live run."""

    champion_mae: float
    baseline_mae: float
    improvement: float
    champion_mape: float
    baseline_mape: float
    champion_wape: float
    baseline_wape: float
    champion_bias: float
    baseline_bias: float
    as_of_dates: int
    first_as_of: pd.Timestamp | None
    last_as_of: pd.Timestamp | None
    horizon_days: int
    latest_run_as_of: pd.Timestamp | None
    latest_run_time: pd.Timestamp | None
    prediction_runs: int
    matured_forecasts: int

    @classmethod
    def from_tables(cls, backtest: pd.DataFrame, predictions: pd.DataFrame, actuals: pd.DataFrame) -> "ForecastSummary":
        scores = ForecastAccuracy.scores(backtest, ["model"]).set_index("model") if len(backtest) else None

        def score(model: str, measure: str) -> float:
            return float(scores.loc[model, measure]) if scores is not None and model in scores.index else float("nan")

        runs = PredictionRuns(predictions).runs()
        latest = runs.iloc[0] if len(runs) else None
        return cls(
            champion_mae=score(ForecastModels.CHAMPION, "mae"),
            baseline_mae=score(ForecastModels.BASELINE, "mae"),
            improvement=ForecastAccuracy.improvement(
                score(ForecastModels.CHAMPION, "mae"), score(ForecastModels.BASELINE, "mae")
            ),
            champion_mape=score(ForecastModels.CHAMPION, "mape"),
            baseline_mape=score(ForecastModels.BASELINE, "mape"),
            champion_wape=score(ForecastModels.CHAMPION, "wape"),
            baseline_wape=score(ForecastModels.BASELINE, "wape"),
            champion_bias=score(ForecastModels.CHAMPION, "bias"),
            baseline_bias=score(ForecastModels.BASELINE, "bias"),
            as_of_dates=int(backtest["as_of_date"].nunique()),
            first_as_of=backtest["as_of_date"].min() if len(backtest) else None,
            last_as_of=backtest["as_of_date"].max() if len(backtest) else None,
            horizon_days=int(backtest["horizon_day"].max()) if len(backtest) else 0,
            latest_run_as_of=None if latest is None else pd.Timestamp(latest["as_of_date"]),
            latest_run_time=None if latest is None else pd.Timestamp(latest["run_timestamp"]),
            prediction_runs=int(len(runs)),
            matured_forecasts=int(len(actuals)),
        )
