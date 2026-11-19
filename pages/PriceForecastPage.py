"""The natural gas price forecast: backtests, staged live predictions and how the pipeline runs."""

import pandas as pd
from dash import Dash, Input, Output, dcc, html

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.ForecastSummary import ForecastSummary
from analytics.forecast.PredictionRuns import PredictionRuns
from components.CaseStudyHeader import CaseStudyHeader
from components.forecast.BacktestFanChart import BacktestFanChart
from components.forecast.ForecastIds import ForecastIds as Ids
from components.forecast.ForecastNotes import ForecastNotes
from components.forecast.HorizonErrorChart import HorizonErrorChart
from components.forecast.KpiCards import KpiCards
from components.forecast.LeaderboardTable import LeaderboardTable
from components.forecast.LiveAccuracyTable import LiveAccuracyTable
from components.forecast.LiveActualsChart import LiveActualsChart
from components.forecast.PendingState import PendingState
from components.forecast.PipelineDiagram import PipelineDiagram
from components.forecast.RollingAccuracyChart import RollingAccuracyChart
from components.forecast.SectionHeading import SectionHeading
from components.forecast.StagedForecastChart import StagedForecastChart
from components.forecast.StagedRunTable import StagedRunTable
from config.ForecastModels import ForecastModels
from config.Formats import Formats
from data.forecast.ForecastCache import ForecastCache
from pages.AbstractProjectPage import AbstractProjectPage
from portfolio.Project import Project


class PriceForecastPage(AbstractProjectPage):
    """Six sections that read like a short deck: summary, backtest demo, leaderboard, staged
    predictions, live accuracy and how it runs. Every number comes from the snapshot files.
    """

    DEMO_ANCHOR = "backtest-demo"
    COMPARE_CHOICES = ("gradient_boosting", "naive", "greykite")
    STAGED_HISTORY_DAYS = 40
    GRAPH_CONFIG = {"displayModeBar": False, "responsive": True}

    def __init__(self, project: Project, cache: ForecastCache):
        super().__init__(project)
        self.cache = cache
        self.metadata = cache.metadata()
        self.backtest = cache.backtest()
        self.window = BacktestWindow(self.backtest, cache.prices())
        self.runs = PredictionRuns(cache.predictions())
        self.actuals = cache.actuals()
        self.summary = ForecastSummary.from_tables(self.backtest, cache.predictions(), self.actuals)
        self.leaderboard = ForecastAccuracy.leaderboard(self.backtest) if len(self.backtest) else pd.DataFrame()
        self.as_of_dates = self.window.as_of_dates()

    # Layout

    def layout(self):
        header = CaseStudyHeader().build(
            self.project, self.highlights(), self.key_findings(), self.DEMO_ANCHOR, "Jump to the backtest demo"
        )
        if not self.cache.available:
            return html.Div([header, self.missing_snapshot()], className="forecast project-page")
        return html.Div(
            [
                header,
                self.summary_section(),
                self.backtest_section(),
                self.leaderboard_section(),
                self.staged_section(),
                self.live_section(),
                self.pipeline_section(),
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

    def summary_section(self) -> html.Section:
        return html.Section(
            [
                SectionHeading().build(
                    1,
                    "Summary",
                    "Chronos-2 beats repeating the last price by a small, steady margin over 30 trading days, "
                    "and now forecasts every trading morning beside a gradient boosting challenger.",
                ),
                KpiCards().build(self.summary),
            ],
            className="deck-section",
        )

    def backtest_section(self) -> html.Section:
        default = self.window.default_as_of()
        default_index = self.as_of_dates.index(default) if default in self.as_of_dates else len(self.as_of_dates) - 1
        marks = self.year_marks()
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
                            marks=marks,
                            updatemode="drag",
                            allow_direct_input=False,
                            className="as-of-slider",
                        ),
                    ],
                    className="control-block slider-block",
                ),
                html.Div(
                    [
                        html.Label("Compare the champion with", className="control-label"),
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
                    2,
                    "Backtest demo",
                    "Pick any of the backtest dates. The chart shows what each model knew on that date, what it "
                    "forecast for the next 30 trading days, and what the price actually did.",
                ),
                html.Div(
                    [
                        controls,
                        dcc.Graph(id=Ids.FAN_CHART, config=self.GRAPH_CONFIG),
                        html.Div(id=Ids.FAN_STATS, className="fan-stats"),
                    ],
                    className="panel deck-panel",
                ),
            ],
            className="deck-section",
            id=self.DEMO_ANCHOR,
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

    def leaderboard_section(self) -> html.Section:
        buckets = html.Div(
            dcc.RadioItems(
                id=Ids.LEADERBOARD_BUCKET,
                options=[{"label": bucket.capitalize(), "value": bucket} for bucket in ForecastAccuracy.BUCKET_ORDER],
                value=ForecastAccuracy.ALL_DAYS,
                className="segmented pill",
                inline=True,
            )
        )
        by_day = ForecastAccuracy.by_horizon_day(self.backtest)
        return html.Section(
            [
                SectionHeading().build(
                    3,
                    "Model leaderboard",
                    "Every model on the same dates and horizons. Lower is better for every column; bias closest "
                    "to zero is best. The best value in each column is marked.",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div([html.H3("Error by model"), buckets], className="panel-header align-center"),
                                html.Div(id=Ids.LEADERBOARD_TABLE, className="table-wrap"),
                                html.Div(
                                    "MAE, RMSE and bias in dollars per MMBtu. MAPE and WAPE in percent. Bias is "
                                    "forecast minus actual.",
                                    className="panel-note",
                                ),
                            ],
                            className="panel deck-panel",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3("Error by day ahead"),
                                        html.Div("Mean absolute error at each horizon", className="panel-subtitle"),
                                    ],
                                ),
                                dcc.Graph(figure=HorizonErrorChart().build(by_day), config=self.GRAPH_CONFIG),
                            ],
                            className="panel deck-panel",
                        ),
                    ],
                    className="deck-stack",
                ),
            ],
            className="deck-section",
        )

    def staged_section(self) -> html.Section:
        runs = self.runs.runs()
        options = [
            {
                "label": f"As of {Formats.date(row.as_of_date)} \u00b7 scored {Formats.date_time(row.run_timestamp)}",
                "value": row.run_id,
            }
            for row in runs.itertuples()
        ]
        selector = html.Div(
            [
                html.Label("Run", className="control-label"),
                dcc.Dropdown(
                    id=Ids.RUN_SELECT,
                    options=options,
                    value=self.runs.latest_run_id(),
                    clearable=False,
                    className="run-select",
                ),
            ],
            className="control-block run-block",
        )
        return html.Section(
            [
                SectionHeading().build(
                    4,
                    "Staged predictions",
                    "Each scoring run forecasts with two registered versions. Production is the champion that "
                    "would be used; staging is the challenger, scored the same way so it can earn a promotion.",
                    side=selector,
                ),
                html.Div(
                    [
                        html.Div(
                            dcc.Graph(id=Ids.STAGED_CHART, config=self.GRAPH_CONFIG), className="panel deck-panel"
                        ),
                        html.Div(
                            [
                                html.H3("Forecast path"),
                                html.Div("Dollars per MMBtu, with the production 80% band", className="panel-subtitle"),
                                html.Div(id=Ids.STAGED_TABLE, className="table-wrap"),
                                html.Div(
                                    f"{Formats.amount(len(runs), 'run')} so far. The scoring job runs Tuesday to "
                                    "Saturday at 7:00 AM ET on the session that closed the day before.",
                                    className="panel-note",
                                ),
                            ],
                            className="panel deck-panel",
                        ),
                    ],
                    className="deck-grid wide-left",
                ),
            ],
            className="deck-section",
        )

    def live_section(self) -> html.Section:
        heading = SectionHeading().build(
            5,
            "Live forecast against actuals",
            "Live forecasts are scored against the settled price once each target date passes, then summarized "
            "over every matured forecast and over the last 20 as-of dates.",
        )
        if self.actuals.empty:
            body = html.Div(
                PendingState().build(self.runs.first_target_date(), len(self.runs.predictions)),
                className="panel deck-panel",
            )
        else:
            body = html.Div(
                [
                    html.Div(
                        [
                            html.H3("Day 1 forecasts against the settled price"),
                            dcc.Graph(figure=LiveActualsChart().build(self.actuals), config=self.GRAPH_CONFIG),
                        ],
                        className="panel deck-panel",
                    ),
                    html.Div(
                        [
                            html.H3("Rolling MAE, last 20 as-of dates"),
                            dcc.Graph(
                                figure=RollingAccuracyChart().build(self.cache.rolling_accuracy()),
                                config=self.GRAPH_CONFIG,
                            ),
                            html.Div(LiveAccuracyTable().build(self.cache.accuracy()), className="table-wrap"),
                        ],
                        className="panel deck-panel",
                    ),
                ],
                className="deck-grid",
            )
        return html.Section([heading, body], className="deck-section")

    def pipeline_section(self) -> html.Section:
        return html.Section(
            [
                SectionHeading().build(
                    6,
                    "How it runs",
                    "Forecasts refresh each trading morning. The scoring job runs Tuesday to Saturday at 7:00 AM "
                    "ET and works through five steps, and this site only reads what they produce.",
                ),
                html.Div(PipelineDiagram().build(), className="panel deck-panel"),
                ForecastNotes().build(
                    self.summary,
                    self.leaderboard,
                    self.versions(),
                    self.metadata,
                    self.window.dates_without_band(ForecastModels.CHAMPION),
                ),
            ],
            className="deck-section",
        )

    def versions(self) -> dict:
        """The registered version of each model, from the latest run, or from the backtest."""
        versions = {}
        for frame in (self.backtest, self.runs.predictions):
            for model, version in frame.groupby("model")["model_version"].last().items():
                if str(version).isdigit():
                    versions[model] = str(version)
        return versions

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
            Output(Ids.STAGED_CHART, "figure"), Output(Ids.STAGED_TABLE, "children"), Input(Ids.RUN_SELECT, "value")
        )
        def show_run(run_id):
            run = self.runs.run(run_id)
            as_of = run["as_of_date"].max() if len(run) else None
            history = self.window.history(as_of, self.STAGED_HISTORY_DAYS) if as_of is not None else run.iloc[0:0]
            return StagedForecastChart().build(history, run), StagedRunTable().build(run)

        @app.callback(Output(Ids.LEADERBOARD_TABLE, "children"), Input(Ids.LEADERBOARD_BUCKET, "value"))
        def show_leaderboard(bucket):
            return LeaderboardTable().build(self.leaderboard, bucket or ForecastAccuracy.ALL_DAYS)

    def fan_stats(self, as_of: pd.Timestamp, models: list[str]) -> list:
        """Small chips under the fan chart: each model's MAE on this date and the band hit rate."""
        chips = []
        for model in models:
            forecast = self.window.forecast(as_of, model)
            if forecast.empty:
                continue
            mae = ForecastAccuracy.scores(forecast, ["model"])["mae"].iloc[0]
            chips.append(self.chip(ForecastModels.name(model), f"MAE {Formats.decimal(mae, 3)}", model))
        champion = self.window.forecast(as_of, ForecastModels.CHAMPION)
        coverage = ForecastAccuracy.coverage(champion)
        if coverage["rows"]:
            inside = round(coverage["share"] * coverage["rows"])
            chips.append(self.chip("Inside the band", f"{inside} of {coverage['rows']} days", None))
        else:
            chips.append(self.chip("Band", "Not available on this date", None))
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
            (Formats.percent(summary.improvement, 2), "lower MAE than naive"),
            (Formats.count(summary.as_of_dates), "backtest dates"),
            (f"{summary.horizon_days} days", "forecast horizon, trading days"),
            (Formats.percent(summary.coverage), "of actuals inside the 80% band"),
        ]

    @staticmethod
    def times(count: int) -> str:
        return {1: "once", 2: "twice"}.get(count, f"{Formats.count(count)} times")

    def key_findings(self) -> list[str]:
        """Plain findings computed from the snapshot each time the app starts."""
        if not self.cache.available:
            return ["The findings appear once the forecast snapshot is built."]
        summary = self.summary
        board = self.leaderboard.set_index(["model", "horizon_bucket"])["mae"]
        champion, baseline = ForecastModels.CHAMPION, ForecastModels.BASELINE
        findings = [
            f"Chronos-2 has the lowest error over 30 trading days: MAE {Formats.decimal(summary.champion_mae)} "
            f"against {Formats.decimal(summary.baseline_mae)} for naive, {Formats.percent(summary.improvement, 2)} "
            "lower. Enough to promote, but a modest edge.",
            f"Over the first 5 days nothing beats repeating the last price (naive "
            f"{Formats.decimal(board[(baseline, 'days 1 to 5')])}, Chronos-2 "
            f"{Formats.decimal(board[(champion, 'days 1 to 5')])}). Chronos-2 pulls ahead on days 16 to 30.",
            f"The 80% band held {Formats.percent(summary.coverage)} of actuals, so it is somewhat too narrow.",
        ]
        if summary.latest_run_as_of is not None:
            matured = (
                "Actuals are pending."
                if summary.matured_forecasts == 0
                else f"{Formats.amount(summary.matured_forecasts, 'forecast')} "
                f"{'has' if summary.matured_forecasts == 1 else 'have'} matured."
            )
            findings.append(
                f"Live scoring has run {self.times(summary.prediction_runs)}, latest as of "
                f"{Formats.date(summary.latest_run_as_of)}. {matured}"
            )
        return findings
