"""The model serving each horizon event in the latest tournament round."""

import pandas as pd
from dash import html

from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class EventWinners:
    """One card per event: its days, the winning model and role, its blended MAE and its backtest error measures."""

    MEASURES = (("mape", "MAPE"), ("wape", "WAPE"), ("bias", "Bias"))

    def build(self, events: pd.DataFrame, leaderboard: pd.DataFrame) -> html.Div:
        if events.empty:
            return html.Div("No tournament results yet.", className="panel-note")
        return html.Div([self.card(event, leaderboard) for event in events.itertuples()], className="event-winners")

    def card(self, event, leaderboard: pd.DataFrame) -> html.Div:
        _, role = ForecastModels.stage_parts(event.stage)
        return html.Div(
            [
                html.Div(f"Days {int(event.first_day)} to {int(event.last_day)}", className="event-days"),
                html.Div(
                    [
                        html.Span(className="model-dot", style={"background": ForecastModels.color(event.model)}),
                        f"{ForecastModels.name(event.model)} v{event.model_version}",
                    ],
                    className="event-model",
                ),
                html.Div(
                    f"{ForecastModels.ROLE_NAMES.get(role, role)} \u00b7 blended MAE "
                    f"{Formats.decimal(event.blended_mae)}",
                    className="event-detail",
                ),
                html.Div(self.measures(event, leaderboard), className="event-measures"),
            ],
            className="event-card",
        )

    def measures(self, event, leaderboard: pd.DataFrame) -> str:
        scores = ForecastAccuracy.bucket_scores(leaderboard, event.model, event.horizon_bucket)
        if scores is None:
            return "No backtest scores for this horizon"
        return " \u00b7 ".join(f"{label} {Formats.error(key, scores[key])}" for key, label in self.MEASURES)
