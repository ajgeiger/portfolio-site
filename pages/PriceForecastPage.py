"""The natural gas price forecast: the model tournament, the published production forecast and the backtests."""

import pandas as pd
from dash import Dash, Input, Output, dcc, html

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.ForecastSummary import ForecastSummary
from analytics.forecast.PredictionRuns import PredictionRuns
from analytics.forecast.TournamentResults import TournamentResults
from components.CaseStudyHeader import CaseStudyHeader
from components.forecast.BacktestFanChart import BacktestFanChart
from components.forecast.BacktestScoreTable import BacktestScoreTable
from components.forecast.EventWinners import EventWinners
from components.forecast.ForecastIds import ForecastIds as Ids
from components.forecast.ForecastPathTable import ForecastPathTable
from components.forecast.KpiCards import KpiCards
from components.forecast.ProductionForecastChart import ProductionForecastChart
from components.forecast.RunDetails import RunDetails
from components.forecast.SectionHeading import SectionHeading
from components.forecast.StandingsTable import StandingsTable
from config.ForecastModels import ForecastModels
from config.Formats import Formats
from data.forecast.ForecastCache import ForecastCache
from pages.AbstractProjectPage import AbstractProjectPage
from portfolio.Project import Project


class PriceForecastPage(AbstractProjectPage):
    """The summary on top, then the tournament leaderboard, the published production forecast and the
    backtests every score starts from. Every number comes from the snapshot files.
    """

    PRODUCTION_ANCHOR = "production-forecast"
    COMPARE_CHOICES = ("gradient_boosting", "naive", "greykite")
    DEFAULT_BUCKET = "days 16 to 30"
    HISTORY_DAYS = 40
    GRAPH_CONFIG = {"displayModeBar": False, "responsive": True}

    def __init__(self, project: Project, cache: ForecastCache):
        super().__init__(project)
        self.cache = cache
        self.backtest = cache.backtest()
        self.window = BacktestWindow(self.backtest, cache.prices())
        self.runs = PredictionRuns(cache.predictions())
        self.tournament = TournamentResults(cache.standings(), cache.events(), cache.trials())
        self.summary = ForecastSummary.from_tables(self.backtest, cache.predictions(), cache.actuals())
        self.leaderboard = ForecastAccuracy.leaderboard(self.backtest) if len(self.backtest) else pd.DataFrame()
        self.as_of_dates = self.window.as_of_dates()

    # Layout

    def layout(self):
        header = CaseStudyHeader().build(
            self.project, self.highlights(), self.key_findings(), self.PRODUCTION_ANCHOR, "View production forecast"
        )
        if not self.cache.available:
            return html.Div([header, self.missing_snapshot()], className="forecast project-page")
        return html.Div(
            [
                header,
                KpiCards().build(self.summary),
                self.leaderboard_section(),
                self.production_section(),
                self.backtest_section(),
            ],
            className="forecast project-page",
        )

    @staticmethod
    def missing_snapshot() -> html.Div:
        return html.Div(
            [
                html.H3("The forecast snapshot is not built yet"),
                html.P("Run python build_forecast_cache.py next to a natural-gas-forecasting checkout to create it."),
            ],
            className="panel deck-section",
        )

    def leaderboard_section(self) -> html.Section:
        buckets = dcc.RadioItems(
            id=Ids.LEADERBOARD_BUCKET,
            options=[{"label": bucket.capitalize(), "value": bucket} for bucket in ForecastAccuracy.BUCKET_ORDER],
            value=self.DEFAULT_BUCKET,
            className="segmented pill",
            inline=True,
        )
        as_of = self.tournament.as_of_date
        return html.Section(
            [
                SectionHeading().build(
                    "Model leaderboard",
                    "Each family champion competes in three horizon events against the naive baseline. A champion "
                    f"qualifies by beating naive by at least {Formats.percent(TournamentResults.MIN_IMPROVEMENT, 0)} "
                    "on blended MAE, and the lowest qualified score wins the event."
                    + (f" Results as of {Formats.date(as_of)}." if as_of is not None else ""),
                ),
                EventWinners().build(self.tournament.events()),
                html.Details(
                    [
                        self.scoreboard_summary(),
                        html.Div(
                            [
                                html.Div(buckets, className="scoreboard-controls"),
                                html.Div(id=Ids.LEADERBOARD_TABLE, className="table-wrap flush"),
                                html.Div(self.standings_note(), className="panel-note"),
                            ],
                            className="scoreboard-body",
                        ),
                    ],
                    open=False,
                    className="panel deck-panel deck-gap scoreboard-details",
                ),
            ],
            className="deck-section",
        )

    def scoreboard_summary(self) -> html.Summary:
        """The always visible header of the collapsible scoreboard."""
        contenders = len(self.tournament.standings(self.DEFAULT_BUCKET))
        return html.Summary(
            [
                html.Div(
                    [
                        html.H3("Model scoreboard"),
                        html.Div(
                            "Every champion, challenger and the naive baseline, ranked by blended MAE for each horizon",
                            className="panel-subtitle",
                        ),
                    ]
                ),
                html.Span(
                    [
                        html.Span(f"{Formats.amount(contenders, 'contender')} \u00b7 click to expand"),
                        html.Span(className="scoreboard-chevron"),
                    ],
                    className="scoreboard-hint",
                ),
            ],
            className="scoreboard-summary",
        )

    def standings_note(self) -> str:
        note = (
            "Blended MAE weights a model's last 30 matured production days against its backtest MAE, in dollars per "
            "MMBtu. vs naive is the change in blended MAE against the baseline."
        )
        if self.tournament.production_days() == 0:
            note += " No forecast has matured in production yet, so every blended MAE equals the backtest MAE."
        return note

    def run_options(self) -> list[dict]:
        """One dropdown option per published run, newest first."""
        return [
            {
                "label": f"{Formats.date(run.as_of_date)} (run {str(run.run_id)[:8]} \u00b7 "
                f"{Formats.amount(run.contenders, 'contender')})",
                "value": run.run_id,
            }
            for run in self.runs.runs().itertuples()
        ]

    def production_section(self) -> html.Section:
        selector = html.Div(
            [
                html.Label("Scoring run", htmlFor=Ids.RUN_SELECTOR, className="control-label"),
                dcc.Dropdown(
                    id=Ids.RUN_SELECTOR,
                    options=self.run_options(),
                    value=self.runs.latest_run_id(),
                    clearable=False,
                    searchable=False,
                    className="run-selector",
                ),
            ],
            className="run-selector-block",
        )
        compare = dcc.Checklist(
            id=Ids.COMPARE_CHAMPIONS,
            options=[
                {"label": ForecastModels.name(ForecastModels.stage_parts(stage)[0]), "value": stage}
                for stage in ForecastModels.CHAMPION_STAGES
            ],
            value=[],
            className="compare-checklist",
            inline=True,
        )
        return html.Section(
            [
                SectionHeading().build(
                    "Active predictions in production",
                    "Every trading morning each contender forecasts the next 30 trading days, the tournament picks "
                    "the event winners, and their segments are stitched into one published forecast. Runs Tuesday to "
                    "Saturday at 7:00 AM ET.",
                    side=selector,
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3("Production forecast"),
                                        html.Div(
                                            [html.Span("Compare with champions", className="control-label"), compare],
                                            className="compare-row",
                                        ),
                                    ],
                                    className="panel-head",
                                ),
                                dcc.Graph(
                                    id=Ids.PRODUCTION_CHART,
                                    config=self.GRAPH_CONFIG,
                                    style={"height": f"{ProductionForecastChart.HEIGHT}px"},
                                ),
                            ],
                            className="panel deck-panel",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [html.H3("Run details"), html.Div(id=Ids.RUN_DETAILS)],
                                    className="panel deck-panel",
                                ),
                                html.Div(
                                    [
                                        html.H3("Forecast path"),
                                        html.Div(
                                            "Dollars per MMBtu",
                                            className="panel-subtitle",
                                        ),
                                        html.Div(id=Ids.PATH_TABLE, className="table-wrap"),
                                    ],
                                    className="panel deck-panel",
                                ),
                            ],
                            className="deck-stack",
                        ),
                    ],
                    className="deck-grid wide-left",
                ),
            ],
            className="deck-section",
            id=self.PRODUCTION_ANCHOR,
        )

    def backtest_section(self) -> html.Section:
        default = self.window.default_as_of()
        default_index = self.as_of_dates.index(default) if default in self.as_of_dates else len(self.as_of_dates) - 1
        controls = html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("As-of date", className="control-label"),
                                html.Div(id=Ids.AS_OF_LABEL, className="as-of-value"),
                            ],
                            className="control-label-row",
                        ),
                        dcc.Slider(
                            id=Ids.AS_OF_SLIDER,
                            min=0,
                            max=len(self.as_of_dates) - 1,
                            step=1,
                            value=default_index,
                            marks=self.year_marks(),
                            updatemode="drag",
                            allow_direct_input=False,
                            className="as-of-slider",
                        ),
                    ],
                    className="control-block slider-block",
                ),
                html.Div(
                    [
                        html.Label(
                            f"Compare {ForecastModels.name(ForecastModels.CHAMPION)} with", className="control-label"
                        ),
                        dcc.RadioItems(
                            id=Ids.COMPARE_MODEL,
                            options=[
                                {"label": ForecastModels.name(model), "value": model} for model in self.COMPARE_CHOICES
                            ],
                            value=ForecastModels.CHALLENGER,
                            className="segmented pill",
                            inline=True,
                        ),
                    ],
                    className="control-block",
                ),
            ],
            className="deck-controls",
        )
        return html.Section(
            [
                SectionHeading().build(
                    "Model selection backtests",
                    "The tournament starts from these rolling-origin backtests. Each family was trained and tuned at "
                    f"the same {Formats.count(self.summary.as_of_dates)} dates, its two best configurations became "
                    "the champion and the challenger, and their backtest MAE seeds every blended score until "
                    "production days replace it. Move the slider to see any forecast date.",
                ),
                html.Div(
                    [
                        controls,
                        dcc.Graph(id=Ids.FAN_CHART, config=self.GRAPH_CONFIG),
                        html.Div(id=Ids.FAN_STATS, className="fan-stats"),
                    ],
                    className="panel deck-panel",
                ),
                html.Div(
                    [
                        html.H3("Backtest accuracy over all 30 days"),
                        html.Div(
                            "Best configuration per family. MAE, RMSE and bias in dollars per MMBtu, MAPE and WAPE in "
                            "percent. Bias is forecast minus actual. The best value in each column is marked.",
                            className="panel-subtitle",
                        ),
                        html.Div(BacktestScoreTable().build(self.leaderboard), className="table-wrap"),
                    ],
                    className="panel deck-panel deck-gap",
                ),
            ],
            className="deck-section",
        )

    def year_marks(self) -> dict:
        """A slider mark at the first as-of date of each year, skipping a lone date before the first new year."""
        marks = {}
        for index, date in enumerate(self.as_of_dates):
            if index > 0 and date.year != self.as_of_dates[index - 1].year:
                marks[index] = str(date.year)
        if self.as_of_dates and (not marks or min(marks) > 6):
            marks[0] = str(self.as_of_dates[0].year)
        return marks

    # Callbacks

    def register_callbacks(self, app: Dash) -> None:
        if not self.cache.available:
            return

        @app.callback(
            Output(Ids.FAN_CHART, "figure"),
            Output(Ids.AS_OF_LABEL, "children"),
            Output(Ids.FAN_STATS, "children"),
            Input(Ids.AS_OF_SLIDER, "value"),
            Input(Ids.COMPARE_MODEL, "value"),
        )
        def show_backtest(index, compare):
            as_of = self.as_of_dates[int(index or 0)]
            models = [ForecastModels.CHAMPION, compare or ForecastModels.CHALLENGER]
            figure = BacktestFanChart().build(self.window, as_of, models)
            return figure, Formats.date(as_of), self.fan_stats(as_of, models)

        @app.callback(
            Output(Ids.PRODUCTION_CHART, "figure"),
            Output(Ids.PATH_TABLE, "children"),
            Output(Ids.RUN_DETAILS, "children"),
            Input(Ids.RUN_SELECTOR, "value"),
            Input(Ids.COMPARE_CHAMPIONS, "value"),
        )
        def show_run(run_id, compare):
            return self.run_view(run_id or self.runs.latest_run_id(), compare)

        @app.callback(Output(Ids.LEADERBOARD_TABLE, "children"), Input(Ids.LEADERBOARD_BUCKET, "value"))
        def show_leaderboard(bucket):
            return StandingsTable().build(self.tournament.standings(bucket or self.DEFAULT_BUCKET))

    def run_view(self, run_id: str | None, compare: list[str] | None = None) -> tuple:
        """Chart, forecast path table and details for one run."""
        run = self.runs.run(run_id)
        as_of = run["as_of_date"].max() if len(run) else None
        history = (
            self.window.history(as_of, self.HISTORY_DAYS)
            if as_of is not None
            else pd.DataFrame(columns=["date", "high"])
        )
        chart = ProductionForecastChart().build(history, run, compare)
        return chart, ForecastPathTable().build(self.runs.production(run_id)), RunDetails().build(run)

    def fan_stats(self, as_of: pd.Timestamp, models: list[str]) -> list:
        """Small chips under the fan chart: each model's MAE on this date."""
        chips = []
        for model in models:
            forecast = self.window.forecast(as_of, model)
            if forecast.empty:
                continue
            mae = ForecastAccuracy.scores(forecast, ["model"])["mae"].iloc[0]
            chips.append(self.chip(ForecastModels.name(model), f"MAE {Formats.decimal(mae, 3)}", model))
        return chips

    @staticmethod
    def chip(label: str, value: str, model: str | None) -> html.Div:
        dot = [html.Span(className="model-dot", style={"background": ForecastModels.color(model)})] if model else []
        return html.Div([*dot, html.Span(label, className="chip-label"), html.Span(value)], className="fan-chip")

    # Project summary

    def highlights(self) -> list[tuple[str, str]]:
        summary = self.summary
        if not self.cache.available:
            return [("n/a", "snapshot not built yet")]
        return [
            (str(len(self.tournament.families())), "model families plus a naive baseline"),
            (str(len(self.tournament.events())), "horizon events in the production forecast"),
            (Formats.count(summary.as_of_dates), "backtest dates behind every score"),
            (Formats.percent(TournamentResults.MIN_IMPROVEMENT, 0), "margin a champion needs over naive"),
        ]

    def key_findings(self) -> list[str]:
        """Plain findings computed from the snapshot each time the app starts."""
        if not self.cache.available:
            return ["The findings appear once the forecast snapshot is built."]
        summary = self.summary
        findings = []
        families = [ForecastModels.prose_name(family) for family in self.tournament.families()]
        if families:
            names = self.joined(families)
            findings.append(
                f"{names[:1].upper()}{names[1:]} compete with a naive baseline in three horizon events every trading "
                f"morning. A champion has to beat naive by at least "
                f"{Formats.percent(TournamentResults.MIN_IMPROVEMENT, 0)} on a blended production and backtest "
                "score to win an event."
            )
        events = self.tournament.events()
        if len(events):
            results = [self.event_result(event) for event in events.itertuples()]
            findings.append(
                f"In the latest round, as of {Formats.date(self.tournament.as_of_date)}, {self.joined(results)}. "
                "The winning segments make up the production forecast."
            )
        findings.append(
            f"Over all 30 days {ForecastModels.name(ForecastModels.CHAMPION)} has the lowest backtest error, MAE "
            f"{Formats.decimal(summary.champion_mae)} against {Formats.decimal(summary.baseline_mae)} for naive "
            f"({Formats.percent(summary.improvement, 2)} lower)."
        )
        return findings

    @staticmethod
    def event_result(event) -> str:
        days = f"days {int(event.first_day)} to {int(event.last_day)}"
        name = ForecastModels.prose_name(event.model)
        if event.improvement > 0:
            return f"{name} wins {days} ({Formats.percent(event.improvement, 2)} better than naive)"
        return f"{name} holds {days} because no champion beat it by 1%"

    @staticmethod
    def joined(items: list[str]) -> str:
        """Join a list as plain prose: "a", "a and b" or "a, b and c"."""
        if len(items) <= 1:
            return "".join(items)
        return f"{', '.join(items[:-1])} and {items[-1]}"
