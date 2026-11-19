import math

import pandas as pd
import pytest

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.ForecastSummary import ForecastSummary
from analytics.forecast.PredictionRuns import PredictionRuns
from tests.forecast_tables import AS_OF_DATES, make_actuals, make_backtest, make_predictions, make_prices


def typed(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in ("as_of_date", "target_date", "date"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    if "run_timestamp" in frame.columns:
        frame["run_timestamp"] = pd.to_datetime(frame["run_timestamp"], utc=True)
    return frame


def test_scores_match_hand_worked_values():
    frame = pd.DataFrame({"model": ["a", "a"], "forecast": [11.0, 18.0], "actual": [10.0, 20.0]})
    row = ForecastAccuracy.scores(frame, ["model"]).iloc[0]
    assert row["mae"] == pytest.approx(1.5)
    assert row["mape"] == pytest.approx(100 * (0.1 + 0.1) / 2)
    assert row["wape"] == pytest.approx(100 * 3 / 30)
    assert row["bias"] == pytest.approx(-0.5)
    assert row["rmse"] == pytest.approx(math.sqrt((1 + 4) / 2))
    assert row["forecasts"] == 2


def test_buckets_follow_the_source_views():
    assert ForecastAccuracy.bucket(1) == "days 1 to 5"
    assert ForecastAccuracy.bucket(5) == "days 1 to 5"
    assert ForecastAccuracy.bucket(6) == "days 6 to 15"
    assert ForecastAccuracy.bucket(30) == "days 16 to 30"


def test_leaderboard_has_every_bucket_and_an_all_days_row():
    board = ForecastAccuracy.leaderboard(typed(make_backtest()))
    chronos = board[board["model"] == "chronos"].set_index("horizon_bucket")
    assert list(chronos.index.astype(str)) == ["days 1 to 5", "days 6 to 15", "all days"]
    assert chronos.loc["all days", "mae"] == pytest.approx(0.10)
    assert chronos.loc["all days", "forecasts"] == 18
    assert board[board["horizon_bucket"] == "all days"].set_index("model")["bias"]["naive"] == pytest.approx(0.30)


def test_coverage_counts_only_rows_with_a_band():
    backtest = typed(make_backtest())
    coverage = ForecastAccuracy.coverage(backtest[backtest["model"] == "chronos"])
    assert coverage == {"share": 0.5, "rows": 12, "as_of_dates": 2}


def test_improvement_is_positive_when_lower_than_baseline():
    assert ForecastAccuracy.improvement(0.5192, 0.5259) == pytest.approx(0.01274, abs=1e-5)
    assert ForecastAccuracy.improvement(1.0, 0.0) == 0.0


def test_summary_reads_champion_baseline_and_latest_run():
    summary = ForecastSummary.from_tables(typed(make_backtest()), typed(make_predictions()), typed(make_actuals()))
    assert summary.champion_mae == pytest.approx(0.10)
    assert summary.baseline_mae == pytest.approx(0.30)
    assert summary.improvement == pytest.approx(2 / 3)
    assert summary.coverage == 0.5
    assert summary.coverage_dates == 2
    assert summary.as_of_dates == 3
    assert summary.horizon_days == 6
    assert summary.latest_run_as_of == pd.Timestamp("2024-03-15")
    assert summary.prediction_runs == 1
    assert summary.matured_forecasts == 4


def test_backtest_window_slices_one_date():
    window = BacktestWindow(typed(make_backtest()), typed(make_prices()))
    as_of = pd.Timestamp(AS_OF_DATES[1])
    assert window.default_as_of() == as_of
    assert window.history(as_of, 10)["date"].max() == as_of
    assert len(window.history(as_of, 10)) == 10
    assert len(window.forecast(as_of, "chronos")) == 6
    assert len(window.actuals(as_of)) == 6


def test_prediction_runs_list_newest_first():
    runs = PredictionRuns(typed(make_predictions()))
    assert runs.latest_run_id() == "run1"
    assert runs.runs().iloc[0]["stages"] == "production, staging"
    assert len(runs.stage("run1", "production")) == 6
    assert PredictionRuns(make_predictions().iloc[0:0]).latest_run_id() is None
