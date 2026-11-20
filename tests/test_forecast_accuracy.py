import math

import pandas as pd
import pytest

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.ForecastSummary import ForecastSummary
from analytics.forecast.PredictionRuns import PredictionRuns
from analytics.forecast.TournamentResults import TournamentResults
from config.ForecastModels import ForecastModels
from config.Formats import Formats
from tests.forecast_tables import (
    AS_OF_DATES,
    make_actuals,
    make_backtest,
    make_events,
    make_predictions,
    make_prices,
    make_standings,
    make_trials,
)


def typed(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in ("as_of_date", "target_date", "date", "trial_started"):
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


def test_improvement_is_positive_when_lower_than_baseline():
    assert ForecastAccuracy.improvement(0.5192, 0.5259) == pytest.approx(0.01274, abs=1e-5)
    assert ForecastAccuracy.improvement(1.0, 0.0) == 0.0


def test_summary_reads_champion_baseline_and_latest_run():
    summary = ForecastSummary.from_tables(typed(make_backtest()), typed(make_predictions()), typed(make_actuals()))
    assert summary.champion_mae == pytest.approx(0.10)
    assert summary.baseline_mae == pytest.approx(0.30)
    assert summary.improvement == pytest.approx(2 / 3)
    assert summary.champion_bias == pytest.approx(0.10)
    assert summary.baseline_bias == pytest.approx(0.30)
    assert summary.champion_mape < summary.baseline_mape
    assert summary.champion_wape < summary.baseline_wape
    assert not hasattr(summary, "coverage")
    assert summary.as_of_dates == 3
    assert summary.horizon_days == 6
    assert summary.latest_run_as_of == pd.Timestamp("2024-03-15")
    assert summary.prediction_runs == 1
    assert summary.matured_forecasts == 4


def test_backtest_window_slices_one_date():
    window = BacktestWindow(typed(make_backtest()), typed(make_prices()))
    assert window.default_as_of() == pd.Timestamp(AS_OF_DATES[-1])
    as_of = pd.Timestamp(AS_OF_DATES[1])
    assert window.history(as_of, 10)["date"].max() == as_of
    assert len(window.history(as_of, 10)) == 10
    assert len(window.forecast(as_of, "chronos")) == 6
    assert len(window.actuals(as_of)) == 6


def test_prediction_runs_list_only_runs_that_published_a_forecast():
    runs = PredictionRuns(typed(make_predictions()))
    assert runs.latest_run_id() == "run1"
    assert runs.runs()["run_id"].tolist() == ["run1"]
    assert runs.runs().iloc[0]["contenders"] == 5
    assert len(runs.production("run1")) == 20
    assert len(runs.stage("run1", "chronos:champion")) == 20
    assert PredictionRuns(make_predictions().iloc[0:0]).latest_run_id() is None


def test_production_segments_name_the_winner_of_each_event():
    runs = PredictionRuns(typed(make_predictions()))
    segments = runs.segments(runs.production("run1"))
    assert segments[["first_day", "last_day", "model"]].values.tolist() == [
        [1, 5, "naive"],
        [6, 15, "gradient_boosting"],
        [16, 20, "chronos"],
    ]
    assert runs.segments(runs.production("missing")).empty


def tournament() -> TournamentResults:
    return TournamentResults(typed(make_standings()), typed(make_events()), typed(make_trials()))


def test_tournament_reads_the_latest_round():
    results = tournament()
    assert results.as_of_date == pd.Timestamp("2024-03-15")
    assert results.events()["model"].tolist() == ["naive", "gradient_boosting", "chronos"]
    assert results.families() == ["chronos", "gradient_boosting", "greykite"]
    assert results.trials()["family"].tolist() == ["chronos", "gradient_boosting", "greykite"]
    assert results.standings("days 6 to 15")["stage"].iloc[0] == "gradient_boosting:champion"
    assert results.winner("days 16 to 30")["model"] == "chronos"
    assert results.production_days() == 12


def test_tournament_status_labels():
    results = tournament()
    labels = dict(
        zip(
            results.standings("days 6 to 15")["stage"],
            results.standings("days 6 to 15").apply(TournamentResults.status, axis=1),
            strict=True,
        )
    )
    assert labels == {
        "gradient_boosting:champion": "Winner",
        "chronos:champion": "Qualified",
        "baseline:naive": "Baseline",
        "chronos:challenger": "In trials",
        "greykite:champion": "Below the 1% bar",
    }
    overall = results.standings("all days").apply(TournamentResults.status, axis=1).tolist()
    assert "Winner" not in overall and "Champion" in overall


def test_empty_tournament_tables():
    empty = TournamentResults(make_standings().iloc[0:0], make_events().iloc[0:0], make_trials().iloc[0:0])
    assert empty.empty
    assert empty.as_of_date is None
    assert empty.events().empty and empty.trials().empty and empty.families() == []
    assert empty.production_days() == 0


def test_stage_names_cover_the_tournament_stages():
    assert ForecastModels.stage_parts("chronos:champion") == ("chronos", "champion")
    assert ForecastModels.stage_parts("baseline:naive") == ("naive", "baseline")
    assert ForecastModels.stage_name("gradient_boosting:challenger") == "Gradient boosting challenger"
    assert ForecastModels.stage_name("baseline:naive") == "Naive baseline"
    assert ForecastModels.stage_name("production") == "Production"
    assert ForecastModels.prose_name("gradient_boosting") == "gradient boosting"


def test_bucket_scores_read_one_model_and_horizon():
    board = ForecastAccuracy.leaderboard(typed(make_backtest()))
    scores = ForecastAccuracy.bucket_scores(board, "chronos", "days 1 to 5")
    assert scores["mae"] == pytest.approx(0.10)
    assert scores["bias"] == pytest.approx(0.10)
    assert ForecastAccuracy.bucket_scores(board, "chronos", "days 16 to 30") is None
    assert ForecastAccuracy.bucket_scores(board.iloc[0:0], "chronos", "days 1 to 5") is None


def test_error_formats_follow_each_measure():
    assert Formats.error("mae", 0.51919) == "0.5192"
    assert Formats.error("mape", 13.1234) == "13.12%"
    assert Formats.error("wape", 13.6512) == "13.65%"
    assert Formats.error("bias", -0.04201) == "-0.0420"
