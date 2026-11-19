import re

import pandas as pd
import pytest
from dash import Dash

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from components.forecast.BacktestFanChart import BacktestFanChart
from components.forecast.HorizonErrorChart import HorizonErrorChart
from components.forecast.LeaderboardTable import LeaderboardTable
from components.forecast.LiveActualsChart import LiveActualsChart
from components.forecast.RollingAccuracyChart import RollingAccuracyChart
from components.forecast.StagedForecastChart import StagedForecastChart
from config.Settings import Settings
from data.forecast.ForecastCache import ForecastCache
from data.forecast.ForecastSnapshotBuilder import ForecastSnapshotBuilder
from pages.PriceForecastPage import PriceForecastPage
from portfolio.Project import Project
from portfolio.ProjectRegistry import ProjectRegistry
from tests.forecast_tables import AS_OF_DATES, write_source
from tests.test_portfolio_site import ASSETS, JOB_SEEKING, text_of

LONG_DASHES = re.compile("[\u2013\u2014]")


def make_forecast_project() -> Project:
    return Project(
        slug="natural-gas-price-forecast",
        title="Natural Gas Price Forecast",
        summary="Summary.",
        question="Can a model beat repeating the last price?",
        data="Public data.",
        approach="Backtests.",
        tags=("Forecasting",),
        thumbnail="images/natural-gas-price-forecast.png",
        repo_url="https://github.com/ajgeiger/natural-gas-forecasting",
        repo_label="Code on GitHub",
        build_page=lambda project: None,
    )


@pytest.fixture
def cache_factory(tmp_path):
    def build(actuals: bool = False) -> ForecastCache:
        source = write_source(tmp_path / f"source-{actuals}", actuals=actuals)
        settings = Settings(natgas_source_folder=source, natgas_cache_folder=tmp_path / f"cache-{actuals}")
        ForecastSnapshotBuilder(settings).build()
        return ForecastCache(settings)

    return build


def trace_names(figure) -> list[str]:
    return [trace.name for trace in figure.data if trace.name]


def test_fan_chart_draws_band_history_actuals_and_both_models(cache_factory):
    cache = cache_factory()
    window = BacktestWindow(cache.backtest(), cache.prices())
    figure = BacktestFanChart().build(window, pd.Timestamp(AS_OF_DATES[0]), ["chronos", "gradient_boosting"])
    names = trace_names(figure)
    assert names[0].startswith("Chronos-2 80% band")
    assert {"History", "Actual", "Chronos-2", "Gradient boosting"} <= set(names)
    champion = next(trace for trace in figure.data if trace.name == "Chronos-2")
    assert len(champion.x) == 7  # the last known price, then 6 forecast days


def test_fan_chart_leaves_out_the_band_where_there_is_none(cache_factory):
    cache = cache_factory()
    window = BacktestWindow(cache.backtest(), cache.prices())
    figure = BacktestFanChart().build(window, pd.Timestamp(AS_OF_DATES[-1]), ["chronos", "naive"])
    assert not any("band" in name for name in trace_names(figure))
    assert next(trace for trace in figure.data if trace.name == "Naive").line.dash == "dot"


def test_horizon_chart_has_one_line_per_model_in_display_order(cache_factory):
    by_day = ForecastAccuracy.by_horizon_day(cache_factory().backtest())
    assert trace_names(HorizonErrorChart().build(by_day)) == ["Chronos-2", "Gradient boosting", "Naive", "Greykite"]


def test_staged_chart_shows_both_stages_with_versions(cache_factory):
    cache = cache_factory()
    run = cache.predictions()
    history = BacktestWindow(cache.backtest(), cache.prices()).history(run["as_of_date"].max(), 20)
    names = trace_names(StagedForecastChart().build(history, run))
    assert "Production 80% band" in names
    assert "Production: Chronos-2 v8" in names
    assert "Staging: Gradient boosting v9" in names


def test_charts_fall_back_to_a_note_when_empty(cache_factory):
    cache = cache_factory()
    assert StagedForecastChart().build(cache.prices(), cache.predictions().iloc[0:0]).layout.annotations
    assert LiveActualsChart().build(cache.actuals()).layout.annotations
    assert RollingAccuracyChart().build(cache.rolling_accuracy()).layout.annotations


def test_live_charts_draw_matured_forecasts(cache_factory):
    cache = cache_factory(actuals=True)
    assert trace_names(LiveActualsChart().build(cache.actuals())) == [
        "Actual",
        "Production forecast",
        "Staging forecast",
    ]
    assert trace_names(RollingAccuracyChart().build(cache.rolling_accuracy(), "days 1 to 5")) == [
        "Production",
        "Staging",
    ]


def test_leaderboard_marks_the_best_value_and_compares_with_naive(cache_factory):
    board = ForecastAccuracy.leaderboard(cache_factory().backtest())
    table = LeaderboardTable().build(board)
    rows = table.children[1].children
    first = rows[0].children
    assert text_of(first[0]).strip() == "Chronos-2"
    assert "is-best" in first[2].className
    assert text_of(first[-1]) == "66.67% better"
    assert "Baseline" in text_of(table)


def test_page_shows_six_sections_and_a_pending_state(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    layout = page.layout()
    text = text_of(layout)
    for title in ("Summary", "Backtest demo", "Model leaderboard", "Staged predictions", "How it runs"):
        assert title in text
    assert "Actuals pending" in text
    assert "Mar 18, 2024" in text
    assert "days 11 to 30" in text
    assert not JOB_SEEKING.search(text)
    assert not LONG_DASHES.search(text)
    assert not re.search("signature aviation|fuel demand", text, re.IGNORECASE)
    page.register_callbacks(Dash(__name__))


def test_page_shows_live_accuracy_once_actuals_arrive(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory(actuals=True))
    text = text_of(page.layout())
    assert "Actuals pending" not in text
    assert "Rolling MAE" in text
    assert "has run once" in " ".join(page.key_findings())


def test_page_highlights_are_read_from_the_data(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    assert page.highlights()[0] == ("66.67%", "lower MAE than naive")
    assert page.highlights()[1] == ("3", "backtest dates")
    assert page.versions() == {"chronos": "8", "gradient_boosting": "9"}


def test_page_without_a_snapshot_still_renders(tmp_path):
    page = PriceForecastPage(make_forecast_project(), ForecastCache(folder=tmp_path / "none"))
    assert "not built yet" in text_of(page.layout())
    assert page.highlights() == [("n/a", "snapshot not built yet")]
    page.register_callbacks(Dash(__name__))


def test_default_registry_lists_the_forecast_with_its_thumbnail():
    projects = {project.slug: project for project in ProjectRegistry.default_projects(Settings())}
    project = projects["natural-gas-price-forecast"]
    assert project.route == "/projects/natural-gas-price-forecast"
    assert (ASSETS / project.thumbnail).exists()
    assert not JOB_SEEKING.search(" ".join([project.summary, project.question, project.data, project.approach]))
