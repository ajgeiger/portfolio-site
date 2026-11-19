import re

import pandas as pd
import pytest
from dash import Dash

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from components.forecast.BacktestFanChart import BacktestFanChart
from components.forecast.ForecastIds import ForecastIds
from components.forecast.LeaderboardTable import LeaderboardTable
from components.forecast.RunDetails import RunDetails
from components.forecast.RunList import RunList
from components.forecast.SectionHeading import SectionHeading
from components.forecast.StagedForecastChart import StagedForecastChart
from components.forecast.StagedRunTable import StagedRunTable
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


def test_leaderboard_switches_to_a_horizon_bucket(cache_factory):
    board = ForecastAccuracy.leaderboard(cache_factory().backtest())
    text = text_of(LeaderboardTable().build(board, "days 1 to 5"))
    assert "0.1000" in text and "0.5000" in text
    assert "No backtest data" in text_of(LeaderboardTable().build(board, "days 16 to 30"))


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
    window = BacktestWindow(cache.backtest().iloc[0:0], cache.prices().iloc[0:0])
    assert BacktestFanChart().build(window, pd.Timestamp(AS_OF_DATES[0]), ["chronos"]).layout.annotations


def test_run_list_has_one_clickable_row_per_run_with_day_one_values(cache_factory):
    cache = cache_factory()
    runs = (
        cache.predictions()
        .groupby("run_id", as_index=False)
        .agg(as_of_date=("as_of_date", "max"), run_timestamp=("run_timestamp", "min"))
    )
    listing = RunList().build(runs, cache.predictions(), "run1")
    header, row = listing.children
    assert row.id == {"type": ForecastIds.RUN_ROW, "run": "run1"}
    assert row.className == RunList.SELECTED_CLASS
    assert "3.510" in text_of(row)
    assert RunList.class_name(False) == RunList.ROW_CLASS
    assert "No production runs" in text_of(RunList().build(runs.iloc[0:0], cache.predictions(), None))


def test_run_details_and_path_table_describe_the_run(cache_factory):
    run = cache_factory().predictions()
    details = text_of(RunDetails().build(run))
    for expected in ("run1", "Mar 15, 2024", "6 trading days", "Chronos-2 v8", "Gradient boosting v9"):
        assert expected in details
    table = text_of(StagedRunTable().build(run))
    assert "3.300 to 3.700" in table
    assert "Staging" in table


def test_section_heading_has_no_number():
    heading = SectionHeading().build("Model leaderboard", "Lead.")
    assert text_of(heading).split() == ["Model", "leaderboard", "Lead."]


def test_leaderboard_marks_the_best_value_and_compares_with_naive(cache_factory):
    board = ForecastAccuracy.leaderboard(cache_factory().backtest())
    table = LeaderboardTable().build(board)
    rows = table.children[1].children
    first = rows[0].children
    assert text_of(first[0]).strip() == "Chronos-2"
    assert "is-best" in first[2].className
    assert text_of(first[-1]) == "66.67% better"
    assert "Baseline" in text_of(table)


def test_page_order_and_copy(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    text = text_of(page.layout())
    titles = ["Model leaderboard", "Active predictions in production", "Model selection backtests"]
    positions = [text.index(title) for title in titles]
    assert positions == sorted(positions)
    assert "View production forecast" in text
    for removed in (
        "Summary",
        "Error by model",
        "Error by day ahead",
        "Staged predictions",
        "How it runs",
        "Caveats",
        "pending",
    ):
        assert removed not in text
    assert not re.search("demo", text, re.IGNORECASE)
    assert "deck-number" not in str(page.layout())
    assert not JOB_SEEKING.search(text)
    assert not LONG_DASHES.search(text)
    assert not re.search("signature aviation|fuel demand", text, re.IGNORECASE)
    page.register_callbacks(Dash(__name__))


def test_clicking_a_run_selects_it(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    assert page.clicked_run({"type": ForecastIds.RUN_ROW, "run": "run9"}, "run1") == "run9"
    assert page.clicked_run(None, "run1") == "run1"
    chart, table, details = page.run_view("run1")
    assert "Production: Chronos-2 v8" in trace_names(chart)
    assert "run1" in text_of(details)


def test_page_highlights_are_read_from_the_data(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    assert page.highlights()[0] == ("66.67%", "lower MAE than naive")
    assert page.highlights()[1] == ("3", "backtest dates")
    assert "latest run is as of Mar 15, 2024" in " ".join(page.key_findings())


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
    copy = " ".join([project.summary, project.question, project.data, project.approach])
    assert not JOB_SEEKING.search(copy)
    assert "demo" not in copy.lower()
