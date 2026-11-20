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


RUN_DAYS = 20
EVENT_WINNERS = (
    ("days 1 to 5", 1, 5, "naive"),
    ("days 6 to 15", 6, 15, "gradient_boosting"),
    ("days 16 to 30", 16, 30, "chronos"),
)
CONTENDERS = (
    ("chronos:champion", "chronos", "champion", "1"),
    ("chronos:challenger", "chronos", "challenger", "2"),
    ("gradient_boosting:champion", "gradient_boosting", "champion", "1"),
    ("greykite:champion", "greykite", "champion", "1"),
    ("baseline:naive", "naive", "baseline", "1"),
)
BLENDED = {
    "days 1 to 5": {
        "chronos:champion": 0.21,
        "chronos:challenger": 0.22,
        "gradient_boosting:champion": 0.199,
        "greykite:champion": 0.30,
        "baseline:naive": 0.20,
    },
    "days 6 to 15": {
        "chronos:champion": 0.415,
        "chronos:challenger": 0.43,
        "gradient_boosting:champion": 0.40,
        "greykite:champion": 0.55,
        "baseline:naive": 0.42,
    },
    "days 16 to 30": {
        "chronos:champion": 0.60,
        "chronos:challenger": 0.62,
        "gradient_boosting:champion": 0.64,
        "greykite:champion": 0.90,
        "baseline:naive": 0.65,
    },
    "all days": {
        "chronos:champion": 0.40,
        "chronos:challenger": 0.41,
        "gradient_boosting:champion": 0.405,
        "greykite:champion": 0.60,
        "baseline:naive": 0.41,
    },
}


def winner_for(day: int) -> str:
    return next(model for _, first, last, model in EVENT_WINNERS if first <= day <= last)


def prediction_row(
    run_id: str, as_of: str, stamp: str, target: str, day: int, stage: str, model: str, version: str, banded: bool
) -> dict:
    return {
        "run_id": run_id,
        "run_timestamp": stamp,
        "as_of_date": as_of,
        "target_date": target,
        "horizon_day": day,
        "model": model,
        "model_version": version,
        "stage": stage,
        "forecast": 3.5 + 0.01 * day,
        "lower": 3.3 if banded else None,
        "upper": 3.7 if banded else None,
    }


def make_predictions() -> pd.DataFrame:
    """One tournament run with every contender and the stitched production stage, and one older legacy run."""
    rows = []
    targets = pd.bdate_range("2024-03-18", periods=RUN_DAYS).strftime("%Y-%m-%d")
    for day, target in enumerate(targets, start=1):
        args = ("run1", "2024-03-15", "2024-03-18 12:05:00", target, day)
        winner = winner_for(day)
        rows.append(prediction_row(*args, "production", winner, "1", winner == "chronos"))
        for stage, family, _, version in CONTENDERS:
            rows.append(prediction_row(*args, stage, family, version, family == "chronos"))
        legacy = ("run0", "2024-03-14", "2024-03-15 12:05:00", target, day)
        rows.append(prediction_row(*legacy, "legacy:champion", "chronos", "8", True))
    return pd.DataFrame(rows)


def make_actuals() -> pd.DataFrame:
    """The first two production and naive baseline forecasts of the tournament run, matured."""
    rows = make_predictions()
    keep = (
        (rows["run_id"] == "run1") & rows["stage"].isin(["production", "baseline:naive"]) & (rows["horizon_day"] <= 2)
    )
    rows = rows[keep].drop(columns=["run_timestamp"]).copy()
    rows["horizon_bucket"] = "days 1 to 5"
    rows["actual"] = 3.45
    rows["error"] = rows["forecast"] - rows["actual"]
    rows["filled_at"] = "2024-03-20 12:00:00"
    return rows


def make_standings() -> pd.DataFrame:
    """Blended scores per bucket. Chronos-2 has 12 production days on days 16 to 30, everyone else none."""
    rows = []
    for bucket, scores in BLENDED.items():
        baseline = scores["baseline:naive"]
        event = bucket != "all days"
        ranked = sorted(scores, key=scores.get)
        winner = next(model for name, _, _, model in EVENT_WINNERS if name == bucket) if event else None
        for stage, family, role, version in CONTENDERS:
            improvement = 1 - scores[stage] / baseline
            qualified = event and (role == "baseline" or (role == "champion" and improvement >= 0.01))
            produced = bucket == "days 16 to 30" and stage == "chronos:champion"
            rows.append(
                {
                    "as_of_date": "2024-03-15",
                    "horizon_bucket": bucket,
                    "stage": stage,
                    "run_id": "tour1",
                    "family": family,
                    "role": role,
                    "model": family,
                    "model_version": version,
                    "registered_model": f"natgas-{family}",
                    "prod_days": 12 if produced else 0,
                    "prod_mae": 0.61 if produced else 0.0,
                    "backtest_mae": scores[stage],
                    "backtest_source": "grid",
                    "prod_weight": 0.4 if produced else 0.0,
                    "blended_mae": scores[stage],
                    "baseline_mae": baseline,
                    "improvement": improvement,
                    "rules_passed": 1,
                    "qualified": int(qualified),
                    "rank": ranked.index(stage) + 1,
                    "is_winner": int(event and family == winner and role != "challenger"),
                }
            )
    return pd.DataFrame(rows)


def make_events() -> pd.DataFrame:
    rows = []
    for bucket, first, last, model in EVENT_WINNERS:
        stage = "baseline:naive" if model == "naive" else f"{model}:champion"
        score, baseline = BLENDED[bucket][stage], BLENDED[bucket]["baseline:naive"]
        rows.append(
            {
                "as_of_date": "2024-03-15",
                "horizon_bucket": bucket,
                "run_id": "tour1",
                "first_day": first,
                "last_day": last,
                "family": model,
                "stage": stage,
                "model": model,
                "model_version": "1",
                "registered_model": f"natgas-{model}",
                "blended_mae": score,
                "baseline_mae": baseline,
                "improvement": 1 - score / baseline,
                "qualified_count": 0 if model == "naive" else 1,
                "reason": "test",
            }
        )
    return pd.DataFrame(rows)


def make_trials() -> pd.DataFrame:
    rows = []
    for family, days in (("greykite", 0), ("chronos", 12), ("gradient_boosting", 0)):
        rows.append(
            {
                "as_of_date": "2024-03-15",
                "family": family,
                "run_id": "tour1",
                "registered_model": f"natgas-{family}",
                "champion_version": "1",
                "challenger_version": "2",
                "trial_started": "2024-02-27",
                "trial_days": days,
                "required_days": 60,
                "champion_mae": BLENDED["all days"].get(f"{family}:champion", 0.5),
                "challenger_mae": 0.41,
                "challenger_ahead": 0,
                "promoted": 0,
                "promoted_at": None,
                "status": "in trials",
            }
        )
    return pd.DataFrame(rows)


def write_source(folder: Path, actuals: bool = False, unsettled_price: bool = True, tournament: bool = True) -> Path:
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
        if tournament:
            make_standings().to_sql("tournament_standings", connection, index=False)
            make_events().to_sql("event_winners", connection, index=False)
            make_trials().to_sql("challenger_trials", connection, index=False)
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
