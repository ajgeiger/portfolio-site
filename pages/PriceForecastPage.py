"""The natural gas price forecast: the model in production, how it was chosen and the backtests behind it."""

import pandas as pd
from dash import ALL, Dash, Input, Output, State, callback_context, dcc, html

from analytics.forecast.BacktestWindow import BacktestWindow
from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.ForecastSummary import ForecastSummary
from analytics.forecast.PredictionRuns import PredictionRuns
from components.CaseStudyHeader import CaseStudyHeader
from components.forecast.BacktestFanChart import BacktestFanChart
from components.forecast.ForecastIds import ForecastIds as Ids
from components.forecast.HorizonErrorChart import HorizonErrorChart
from components.forecast.KpiCards import KpiCards
from components.forecast.LeaderboardTable import LeaderboardTable
from components.forecast.RunDetails import RunDetails
from components.forecast.RunList import RunList
from components.forecast.SectionHeading import SectionHeading
from components.forecast.StagedForecastChart import StagedForecastChart
from components.forecast.StagedRunTable import StagedRunTable
from config.ForecastModels import ForecastModels
from config.Formats import Formats
from data.forecast.ForecastCache import ForecastCache
from pages.AbstractProjectPage import AbstractProjectPage
from portfolio.Project import Project


class PriceForecastPage(AbstractProjectPage):
    """The summary on top, then the model leaderboard, the active production forecast and the
    backtests used to select the model. Every number comes from the snapshot files.
    """

    PRODUCTION_ANCHOR = "production-forecast"
    COMPARE_CHOICES = ("gradient_boosting", "naive", "greykite")
    STAGED_HISTORY_DAYS = 40
    GRAPH_CONFIG = {"displayModeBar": False, "responsive": True}

    def __init__(self, project: Project, cache: ForecastCache):
        super().__init__(project)
        self.cache = cache
        self.backtest = cache.backtest()
        self.window = BacktestWindow(self.backtest, cache.prices())
        self.runs = PredictionRuns(cache.predictions())
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
            value=ForecastAccuracy.ALL_DAYS,
            className="segmented pill",
            inline=True,
        )
        by_day = ForecastAccuracy.by_horizon_day(self.backtest)
        return html.Section(
            [
                SectionHeading().build(
                    "Model leaderboard",
                    f"The candidate models, scored on the same {Formats.count(self.summary.as_of_dates)} backtest "
                    "dates. The lowest error earns production.",
                    side=buckets,
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(id=Ids.LEADERBOARD_TABLE, className="table-wrap flush"),
                                html.Div(
                                    "MAE, RMSE and bias in dollars per MMBtu, MAPE and WAPE in percent. Bias is "
                                    "forecast minus actual. The best value in each column is marked.",
                                    className="panel-note",
                                ),
                            ],
                            className="panel deck-panel",
                        ),
                        html.Div(
                            [
                                html.H3("Error by day ahead"),
                                html.Div("Mean absolute error at each horizon", className="panel-subtitle"),
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

    def production_section(self) -> html.Section:
        selected = self.runs.latest_run_id()
        run_count = len(self.runs.runs())
        return html.Section(
            [
                dcc.Store(id=Ids.RUN_SELECTED, data=selected),
                SectionHeading().build(
                    "Active predictions in production",
                    "The champion forecasts every trading morning, with the challenger scored beside it in staging. "
                    "Select a run to see its forecast path, interval and details.",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3("Scoring runs"),
                                html.Div(
                                    f"{Formats.amount(run_count, 'run')}, newest first. Runs Tuesday to Saturday at "
                                    "7:00 AM ET.",
                                    className="panel-subtitle",
                                ),
                            ]
                        ),
                        RunList().build(self.runs.runs(), self.runs.predictions, selected),
                    ],
                    className="panel deck-panel",
                ),
                html.Div(
                    [
                        html.Div(
                            dcc.Graph(id=Ids.STAGED_CHART, config=self.GRAPH_CONFIG), className="panel deck-panel"
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
                                            "Dollars per MMBtu, with the production 80% band",
                                            className="panel-subtitle",
                                        ),
                                        html.Div(id=Ids.STAGED_TABLE, className="table-wrap"),
                                    ],
                                    className="panel deck-panel",
                                ),
                            ],
                            className="deck-stack",
                        ),
                    ],
                    className="deck-grid wide-left deck-gap",
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
                    "Model selection backtests",
                    f"Rolling-origin backtests over {Formats.count(self.summary.as_of_dates)} dates were used to "
                    "train each model family, tune its hyperparameters and compare the results. Chronos-2 had the "
                    "lowest error and was promoted to production. Move the slider to see any forecast date.",
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
            Output(Ids.RUN_SELECTED, "data"),
            Input({"type": Ids.RUN_ROW, "run": ALL}, "n_clicks"),
            State(Ids.RUN_SELECTED, "data"),
            prevent_initial_call=True,
        )
        def select_run(_clicks, current):
            return self.clicked_run(callback_context.triggered_id, current)

        @app.callback(
            Output(Ids.STAGED_CHART, "figure"),
            Output(Ids.STAGED_TABLE, "children"),
            Output(Ids.RUN_DETAILS, "children"),
            Output({"type": Ids.RUN_ROW, "run": ALL}, "className"),
            Input(Ids.RUN_SELECTED, "data"),
            State({"type": Ids.RUN_ROW, "run": ALL}, "id"),
        )
        def show_run(run_id, row_ids):
            chart, table, details = self.run_view(run_id)
            return chart, table, details, [RunList.class_name(row["run"] == run_id) for row in row_ids]

        @app.callback(Output(Ids.LEADERBOARD_TABLE, "children"), Input(Ids.LEADERBOARD_BUCKET, "value"))
        def show_leaderboard(bucket):
            return LeaderboardTable().build(self.leaderboard, bucket or ForecastAccuracy.ALL_DAYS)

    @staticmethod
    def clicked_run(triggered_id, current: str | None) -> str | None:
        """The run whose row was clicked, or the current run when the trigger was not a row."""
        if isinstance(triggered_id, dict) and triggered_id.get("type") == Ids.RUN_ROW:
            return triggered_id["run"]
        return current

    def run_view(self, run_id: str | None) -> tuple:
        """Chart, forecast path table and details for one run."""
        run = self.runs.run(run_id)
        as_of = run["as_of_date"].max() if len(run) else None
        history = self.window.history(as_of, self.STAGED_HISTORY_DAYS) if as_of is not None else run.iloc[0:0]
        return StagedForecastChart().build(history, run), StagedRunTable().build(run), RunDetails().build(run)

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

    def key_findings(self) -> list[str]:
        """Plain findings computed from the snapshot each time the app starts."""
        if not self.cache.available:
            return ["The findings appear once the forecast snapshot is built."]
        summary = self.summary
        board = self.leaderboard.set_index(["model", "horizon_bucket"])["mae"]
        champion, baseline = ForecastModels.CHAMPION, ForecastModels.BASELINE
        findings = [
            f"Chronos-2 had the lowest error over 30 trading days: MAE {Formats.decimal(summary.champion_mae)} "
            f"against {Formats.decimal(summary.baseline_mae)} for naive, {Formats.percent(summary.improvement, 2)} "
            "lower, which cleared the 1% bar for promotion.",
            f"Over the first 5 days repeating the last price is hard to beat (naive "
            f"{Formats.decimal(board[(baseline, 'days 1 to 5')])}, Chronos-2 "
            f"{Formats.decimal(board[(champion, 'days 1 to 5')])}). Chronos-2 pulls ahead on days 16 to 30.",
        ]
        if summary.latest_run_as_of is not None:
            findings.append(
                "Chronos-2 now runs in production every trading morning, with gradient boosting scored beside it "
                f"as the challenger. The latest run is as of {Formats.date(summary.latest_run_as_of)}."
            )
        return findings
