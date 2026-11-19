"""Small hand made forecast tables, so forecast tests never need the real snapshot."""

import sqlite3
from pathlib import Path

import pandas as pd

AS_OF_DATES = ["2024-01-05", "2024-01-19", "2024-02-02"]
MODELS = {"chronos": 0.10, "gradient_boosting": 0.20, "naive": 0.30, "greykite": 0.50}
HORIZON = 6


def make_prices() -> pd.DataFrame:
    dates = pd.bdate_range("2023-12-01", "2024-03-15")
    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "high": [3.0 + 0.01 * i for i in range(len(dates))]})


def make_backtest() -> pd.DataFrame:
    """Each model misses by a fixed amount: forecast = actual + offset. Chronos has a band."""
    prices = make_prices().set_index("date")["high"]
    dates = list(prices.index)
    rows = []
    for as_of in AS_OF_DATES:
        start = dates.index(as_of)
        for day in range(1, HORIZON + 1):
            target = dates[start + day]
            actual = float(prices[target])
            for model, offset in MODELS.items():
                has_band = model == "chronos" and as_of != AS_OF_DATES[-1]
                rows.append(
                    {
                        "as_of_date": as_of,
                        "target_date": target,
                        "horizon_day": day,
                        "model": model,
                        "model_version": {"chronos": "8", "gradient_boosting": "9"}.get(model, "run-abc"),
                        "forecast": actual + offset,
                        "lower": actual + offset - (0.05 if day % 2 else 0.2) if has_band else None,
                        "upper": actual + offset + 0.2 if has_band else None,
                        "actual": actual,
                    }
                )
    return pd.DataFrame(rows)


def make_predictions() -> pd.DataFrame:
    rows = []
    targets = pd.bdate_range("2024-03-18", periods=HORIZON).strftime("%Y-%m-%d")
    for stage, model, version in (("production", "chronos", "8"), ("staging", "gradient_boosting", "9")):
        for day, target in enumerate(targets, start=1):
            rows.append(
                {
                    "run_id": "run1",
                    "run_timestamp": "2024-03-18 12:05:00",
                    "as_of_date": "2024-03-15",
                    "target_date": target,
                    "horizon_day": day,
                    "model": model,
                    "model_version": version,
                    "stage": stage,
                    "forecast": 3.5 + 0.01 * day,
                    "lower": 3.3 if stage == "production" else None,
                    "upper": 3.7 if stage == "production" else None,
                }
            )
    return pd.DataFrame(rows)


def make_actuals() -> pd.DataFrame:
    """The first two production and staging forecasts, matured."""
    rows = make_predictions()
    rows = rows[rows["horizon_day"] <= 2].drop(columns=["run_timestamp"]).copy()
    rows["horizon_bucket"] = "days 1 to 5"
    rows["actual"] = 3.45
    rows["error"] = rows["forecast"] - rows["actual"]
    rows["filled_at"] = "2024-03-20 12:00:00"
    return rows


def write_source(folder: Path, actuals: bool = False, unsettled_price: bool = True) -> Path:
    """A natural-gas-forecasting style folder with data/natgas.db and outputs/backtest_forecasts.parquet."""
    (folder / "data").mkdir(parents=True)
    (folder / "outputs").mkdir()
    prices = make_prices()
    prices["ingested_at"] = "2024-03-18 12:00:00"
    if unsettled_price:
        prices.loc[len(prices)] = {"date": "2024-03-18", "high": 9.99, "ingested_at": "2024-03-18 15:00:00"}
    backtest = make_backtest()
    with sqlite3.connect(folder / "data" / "natgas.db") as connection:
        prices.to_sql("prices", connection, index=False)
        backtest.to_sql("backtest_forecasts", connection, index=False)
        make_predictions().to_sql("predictions", connection, index=False)
        table = make_actuals() if actuals else make_actuals().iloc[0:0]
        table.to_sql("forecast_actuals", connection, index=False)
        connection.execute(
            "CREATE VIEW forecast_accuracy AS SELECT model, stage, horizon_bucket, COUNT(*) AS forecasts, "
            "AVG(ABS(error)) AS mae, 100.0 * AVG(ABS(error) / ABS(actual)) AS mape, "
            "100.0 * SUM(ABS(error)) / SUM(ABS(actual)) AS wape, AVG(error) AS bias "
            "FROM forecast_actuals GROUP BY model, stage, horizon_bucket"
        )
        connection.execute(
            "CREATE VIEW forecast_accuracy_rolling AS SELECT model, stage, horizon_bucket, as_of_date, "
            "AVG(ABS(error)) AS mae FROM forecast_actuals GROUP BY model, stage, horizon_bucket, as_of_date"
        )
    backtest.to_parquet(folder / "outputs" / "backtest_forecasts.parquet", index=False)
    return folder
