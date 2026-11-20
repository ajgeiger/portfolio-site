import re

import pandas as pd
import pytest
from dash import Dash

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.PredictionRuns import PredictionRuns
from analytics.forecast.TournamentResults import TournamentResults
from components.forecast.BacktestFanChart import BacktestFanChart
from components.forecast.BacktestScoreTable import BacktestScoreTable
from components.forecast.EventWinners import EventWinners
from components.forecast.ForecastIds import ForecastIds
from components.forecast.ForecastModelCard import ForecastModelCard
from components.forecast.KpiCards import KpiCards
from components.forecast.ProductionForecastChart import ProductionForecastChart
from components.forecast.RunDetails import RunDetails
from components.forecast.SectionHeading import SectionHeading
from components.forecast.StandingsTable import StandingsTable
from config.ForecastModels import ForecastModels
from config.Formats import Formats
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


def walk(component):
    """Every component in a layout tree, depth first."""
    yield component
    children = getattr(component, "children", None)
    for child in children if isinstance(children, (list, tuple)) else [children]:
        if child is not None and not isinstance(child, (str, int, float)):
            yield from walk(child)


def find_by_id(component, component_id: str):
    return next((item for item in walk(component) if getattr(item, "id", None) == component_id), None)


def find_by_class(component, class_name: str):
    return next((item for item in walk(component) if class_name in (getattr(item, "className", None) or "")), None)


def trace_names(figure) -> list[str]:
    return [trace.name for trace in figure.data if trace.name]


def test_fan_chart_draws_history_actuals_and_both_models_without_a_band(cache_factory):
    cache = cache_factory()
    window = BacktestWindow(cache.backtest(), cache.prices())
    figure = BacktestFanChart().build(window, pd.Timestamp(AS_OF_DATES[0]), ["chronos", "naive"])
    names = trace_names(figure)
    assert names == ["History", "Actual", "Chronos-2", "Naive"]
    assert not any(trace.fill for trace in figure.data)
    champion = next(trace for trace in figure.data if trace.name == "Chronos-2")
    assert len(champion.x) == 7  # the last known price, then 6 forecast days
    assert next(trace for trace in figure.data if trace.name == "Naive").line.dash == "dot"


def test_fan_stats_show_only_each_model_mae(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    text = text_of(page.fan_stats(pd.Timestamp(AS_OF_DATES[0]), ["chronos", "naive"]))
    assert "MAE 0.100" in text and "MAE 0.300" in text
    assert "band" not in text.lower()


def tournament_of(cache: ForecastCache) -> TournamentResults:
    return TournamentResults(cache.standings(), cache.events(), cache.trials())


def run_of(cache: ForecastCache) -> pd.DataFrame:
    return PredictionRuns(cache.predictions()).run("run1")


def test_standings_table_switches_bucket_and_marks_the_winner(cache_factory):
    results = tournament_of(cache_factory())
    text = text_of(StandingsTable().build(results.standings("days 6 to 15")))
    for expected in ("Winner", "Qualified", "In trials", "Baseline", "Below the 1% bar", "0.4000"):
        assert expected in text
    assert "vs naive" not in text.lower() and "+4.76%" not in text
    late = StandingsTable().build(results.standings("days 16 to 30"))
    assert "0.6100 \u00b7 40%" in text_of(late)
    assert "is-top" in late.children[1].children[0].className
    assert "Winner" not in text_of(StandingsTable().build(results.standings("all days")))
    assert "No standings" in text_of(StandingsTable().build(results.standings("days 99")))


def test_event_winners_show_each_winner_with_its_error_measures(cache_factory):
    cache = cache_factory()
    results = tournament_of(cache)
    board = ForecastAccuracy.leaderboard(cache.backtest())
    cards = EventWinners().build(results.events(), board)
    events = text_of(cards)
    for expected in (
        "Days 1 to 5",
        "Naive v1",
        "Baseline",
        "Gradient boosting v1",
        "Champion \u00b7 blended MAE 0.4000",
    ):
        assert expected in events
    scores = ForecastAccuracy.bucket_scores(board, "gradient_boosting", "days 6 to 15")
    expected = f"MAPE {Formats.error('mape', scores['mape'])} \u00b7 WAPE {Formats.error('wape', scores['wape'])}"
    assert expected + " \u00b7 Bias +0.2000" in events
    assert "No backtest scores for this horizon" in text_of(cards.children[2])
    assert "better" not in events and "1%" not in events
    assert "No tournament results" in text_of(EventWinners().build(results.events().iloc[0:0], board))


def test_kpi_cards_focus_on_mae_mape_wape_and_bias(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    cards = KpiCards().build(page.summary).children
    assert [text_of(card.children[0]) for card in cards] == ["MAE", "MAPE", "WAPE", "Bias"]
    text = text_of(KpiCards().build(page.summary))
    for expected in ("0.1000", "naive 0.3000", "+0.1000", "forecast minus actual", "naive +0.3000"):
        assert expected in text
    for removed in ("Days 1 to 5", "coverage", "band", "Latest production run", "lower", "better"):
        assert removed not in text


def test_production_chart_draws_one_segment_per_event_and_optional_champions(cache_factory):
    cache = cache_factory()
    run = run_of(cache)
    history = BacktestWindow(cache.backtest(), cache.prices()).history(run["as_of_date"].max(), 20)
    names = trace_names(ProductionForecastChart().build(history, run))
    assert names == [
        "History",
        "Naive, days 1 to 5",
        "Gradient boosting, days 6 to 15",
        "Chronos-2, days 16 to 20",
    ]
    assert not any(trace.fill for trace in ProductionForecastChart().build(history, run).data)
    compared = trace_names(ProductionForecastChart().build(history, run, ["greykite:champion", "baseline:naive"]))
    assert "Greykite champion path" in compared and "Naive baseline path" in compared


def test_charts_fall_back_to_a_note_when_empty(cache_factory):
    cache = cache_factory()
    assert ProductionForecastChart().build(cache.prices(), cache.predictions().iloc[0:0]).layout.annotations
    window = BacktestWindow(cache.backtest().iloc[0:0], cache.prices().iloc[0:0])
    assert BacktestFanChart().build(window, pd.Timestamp(AS_OF_DATES[0]), ["chronos"]).layout.annotations


def test_run_selector_defaults_to_the_newest_run(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    layout = page.layout()
    selector = find_by_id(layout, ForecastIds.RUN_SELECTOR)
    assert selector.value == "run1"
    assert selector.clearable is False and selector.searchable is False
    assert selector.options == [{"label": "Mar 15, 2024 (run run1 \u00b7 5 contenders)", "value": "run1"}]
    assert "Scoring run" in text_of(layout)


def test_run_details_stay_compact(cache_factory):
    details = RunDetails().build(run_of(cache_factory()))
    labels = [text_of(item.children[0]) for item in details.children]
    assert labels == ["Run", "As-of date", "Scored", "Horizon", "Contenders"]
    for expected in ("run1", "Mar 15, 2024", "20 trading days", "5"):
        assert expected in text_of(details)


def test_forecast_model_card_highlights_the_model_serving_each_event(cache_factory):
    cache = cache_factory()
    board = ForecastAccuracy.leaderboard(cache.backtest())
    production = PredictionRuns(cache.predictions()).production("run1")
    events = tournament_of(cache).events_on(pd.Timestamp("2024-03-15"))
    rows = ForecastModelCard().build(production, events, board).children
    heads = [row.children[0] for row in rows]
    assert [text_of(head.children[0]).strip() for head in heads] == [
        "Naive v1",
        "Gradient boosting v1",
        "Chronos-2 v1",
    ]
    assert [text_of(head.children[1]) for head in heads] == [
        "Days 1 to 5 \u00b7 Baseline",
        "Days 6 to 15 \u00b7 Champion",
        "Days 16 to 30 \u00b7 Champion",
    ]
    assert rows[0].style == {"--model-color": ForecastModels.color("naive")}
    assert rows[2].style == {"--model-color": ForecastModels.color("chronos")}
    measures = rows[1].children[1]
    assert [text_of(item.children[0]) for item in measures.children] == ["MAE", "MAPE", "WAPE", "Bias"]
    assert text_of(measures.children[0].children[1]) == "0.2000"
    assert text_of(measures.children[3].children[1]) == "+0.2000"
    assert "No backtest scores for this horizon" in text_of(rows[2])
    assert "better" not in text_of(rows[0]) and "1%" not in text_of(rows[0])


def test_forecast_model_card_falls_back_to_the_production_rows(cache_factory):
    cache = cache_factory()
    board = ForecastAccuracy.leaderboard(cache.backtest())
    production = PredictionRuns(cache.predictions()).production("run1")
    text = text_of(ForecastModelCard().build(production, cache.events().iloc[0:0], board))
    assert "Days 16 to 20 \u00b7 Champion" in text and "Days 1 to 5 \u00b7 Baseline" in text
    assert "Gradient boosting v1" in text
    empty = ForecastModelCard().build(production.iloc[0:0], cache.events(), board)
    assert "No production runs" in text_of(empty)


def test_section_heading_has_no_number():
    heading = SectionHeading().build("Model leaderboard", "Lead.")
    assert text_of(heading).split() == ["Model", "leaderboard", "Lead."]


def test_backtest_scores_show_only_mae_mape_wape_and_bias(cache_factory):
    board = ForecastAccuracy.leaderboard(cache_factory().backtest())
    table = BacktestScoreTable().build(board)
    header = [text_of(cell) for cell in table.children[0].children.children]
    assert header == ["Model", "MAE", "MAPE", "WAPE", "Bias"]
    first = table.children[1].children[0].children
    assert text_of(first[0]).strip() == "Chronos-2"
    assert "is-best" in first[1].className
    assert "RMSE" not in text_of(table) and "better" not in text_of(table)
    assert "0.1000" in text_of(BacktestScoreTable().build(board, "days 1 to 5"))
    assert "No backtest data" in text_of(BacktestScoreTable().build(board, "days 16 to 30"))


def test_page_order_and_copy(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    text = text_of(page.layout())
    titles = ["Active predictions in production", "Model leaderboard", "Model scoreboard", "Model selection backtests"]
    positions = [text.index(title) for title in titles]
    assert positions == sorted(positions)
    assert "View production forecast" in text
    for removed in (
        "Summary",
        "Error by model",
        "Error by day ahead",
        "Staged predictions",
        "Staging",
        "Challenger trials",
        "Scoring runs",
        "80% band",
        "Inside the band",
        "Interval coverage",
        "Forecast path",
        "RMSE",
        "vs naive",
        "% better",
        "% lower",
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


def test_run_view_updates_for_the_selected_run(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    chart, table, details = page.run_view("run1", ["chronos:champion"])
    assert "Chronos-2 champion path" in trace_names(chart)
    assert "run1" in text_of(details)
    assert "Chronos-2 v1" in text_of(table) and "Days 16 to 30" in text_of(table)


def test_scoreboard_is_collapsible_and_closed_by_default(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    details = find_by_class(page.layout(), "scoreboard-details")
    assert details.open is False
    summary = details.children[0]
    assert "Model scoreboard" in text_of(summary)
    assert "5 contenders \u00b7 click to expand" in text_of(summary)
    buckets = find_by_id(details, ForecastIds.LEADERBOARD_BUCKET)
    assert [option["label"] for option in buckets.options] == [
        "Days 1 to 5",
        "Days 6 to 15",
        "Days 16 to 30",
        "All days",
    ]
    assert buckets.value == PriceForecastPage.DEFAULT_BUCKET
    assert find_by_id(details, ForecastIds.LEADERBOARD_TABLE) is not None


def test_page_highlights_and_findings_are_read_from_the_data(cache_factory):
    page = PriceForecastPage(make_forecast_project(), cache_factory())
    assert page.highlights()[0] == ("3", "model families plus a naive baseline")
    assert page.highlights()[1] == ("3", "horizon events in the production forecast")
    assert page.highlights()[2] == ("3", "backtest dates behind every score")
    assert page.highlights()[3] == ("6", "trading days in each production forecast")
    findings = " ".join(page.key_findings())
    assert findings.startswith("Every trading morning Chronos-2, gradient boosting, Greykite and naive compete")
    assert "In production as of Mar 15, 2024, Naive v1 serves days 1 to 5" in findings
    assert "Chronos-2 leads with MAE 0.1000" in findings and "bias +0.1000" in findings
    assert "better" not in findings and "1%" not in findings
    assert len(page.key_findings()) == 3
    assert "band" not in findings and "challenger" not in findings


def test_page_without_tournament_tables_still_renders(tmp_path):
    source = write_source(tmp_path / "source", tournament=False)
    settings = Settings(natgas_source_folder=source, natgas_cache_folder=tmp_path / "cache")
    ForecastSnapshotBuilder(settings).build()
    page = PriceForecastPage(make_forecast_project(), ForecastCache(settings))
    text = text_of(page.layout())
    assert "No tournament results yet" in text and "No standings" not in text
    page.register_callbacks(Dash(__name__))


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
