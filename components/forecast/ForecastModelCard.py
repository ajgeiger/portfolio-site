"""The model serving each horizon segment of one production forecast, with its error measures."""

import pandas as pd
from dash import html

from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from analytics.forecast.PredictionRuns import PredictionRuns
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class ForecastModelCard:
    """One highlighted row per event: the event days, the serving model and its role, then MAE, MAPE, WAPE and bias.

    The production rows say which model was stitched into each segment. The event winners
    for the same as-of date give the full event days and the role. When a run has no event
    winners, the days and role are read from the production rows. The error measures are
    the model's backtest scores for that horizon bucket.
    """

    MEASURES = (("mae", "MAE"), ("mape", "MAPE"), ("wape", "WAPE"), ("bias", "Bias"))

    def build(self, production: pd.DataFrame, events: pd.DataFrame, leaderboard: pd.DataFrame) -> html.Div:
        segments = PredictionRuns.segments(production)
        if segments.empty:
            return html.Div("No production runs yet.", className="panel-note")
        by_first_day = {int(event.first_day): event for event in events.itertuples()}
        rows = [
            self.row(segment, by_first_day.get(int(segment.first_day)), leaderboard)
            for segment in segments.itertuples()
        ]
        return html.Div(rows, className="model-events")

    def row(self, segment, event, leaderboard: pd.DataFrame) -> html.Div:
        if event is not None and event.model != segment.model:
            event = None
        first, last = (event.first_day, event.last_day) if event is not None else (segment.first_day, segment.last_day)
        color = ForecastModels.color(segment.model)
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(className="model-dot", style={"background": color}),
                                f"{ForecastModels.name(segment.model)} v{segment.model_version}",
                            ],
                            className="model-event-name",
                        ),
                        html.Span(
                            f"Days {int(first)} to {int(last)} \u00b7 {self.role(segment, event)}",
                            className="model-event-days",
                        ),
                    ],
                    className="model-event-head",
                ),
                self.measures(segment, leaderboard),
            ],
            className="model-event",
            style={"--model-color": color},
        )

    @staticmethod
    def role(segment, event) -> str:
        if event is None:
            return "Baseline" if segment.model == ForecastModels.BASELINE else "Champion"
        _, role = ForecastModels.stage_parts(event.stage)
        return ForecastModels.ROLE_NAMES.get(role, role.capitalize())

    def measures(self, segment, leaderboard: pd.DataFrame) -> html.Div:
        scores = ForecastAccuracy.bucket_scores(leaderboard, segment.model, segment.horizon_bucket)
        if scores is None:
            return html.Div("No backtest scores for this horizon", className="model-event-detail")
        return html.Dl(
            [
                html.Div([html.Dt(label), html.Dd(Formats.error(key, scores[key]))], className="model-measure")
                for key, label in self.MEASURES
            ],
            className="model-measures",
        )
