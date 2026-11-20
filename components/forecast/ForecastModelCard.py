"""The model behind each horizon segment of one production forecast."""

import pandas as pd
from dash import html

from analytics.forecast.PredictionRuns import PredictionRuns
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class ForecastModelCard:
    """One highlighted row per event: the event days, the winning model and version, its role and score.

    The production rows say which model was stitched into each segment. The event winners
    for the same as-of date add the role, blended MAE and margin over naive. When a run has
    no event winners, the role is read from the model and the score is left out.
    """

    def build(self, production: pd.DataFrame, events: pd.DataFrame) -> html.Div:
        segments = PredictionRuns.segments(production)
        if segments.empty:
            return html.Div("No production runs yet.", className="panel-note")
        by_first_day = {int(event.first_day): event for event in events.itertuples()}
        rows = [self.row(segment, by_first_day.get(int(segment.first_day))) for segment in segments.itertuples()]
        return html.Div(rows, className="model-events")

    def row(self, segment, event) -> html.Div:
        if event is not None and event.model != segment.model:
            event = None
        first, last = (event.first_day, event.last_day) if event is not None else (segment.first_day, segment.last_day)
        color = ForecastModels.color(segment.model)
        return html.Div(
            [
                html.Div(f"Days {int(first)} to {int(last)}", className="model-event-days"),
                html.Div(
                    [
                        html.Span(className="model-dot", style={"background": color}),
                        f"{ForecastModels.name(segment.model)} v{segment.model_version}",
                    ],
                    className="model-event-name",
                ),
                html.Div(self.detail(segment, event), className="model-event-detail"),
            ],
            className="model-event",
            style={"--model-color": color},
        )

    @staticmethod
    def detail(segment, event) -> str:
        if event is None:
            role = "Baseline" if segment.model == ForecastModels.BASELINE else "Champion"
            return f"{role} \u00b7 from the production forecast"
        _, role = ForecastModels.stage_parts(event.stage)
        role_name = ForecastModels.ROLE_NAMES.get(role, role.capitalize())
        if event.improvement > 0:
            margin = f"{Formats.percent(event.improvement, 2)} better than naive"
        else:
            margin = "no champion beat naive by 1%"
        return f"{role_name} \u00b7 blended MAE {Formats.decimal(event.blended_mae)} \u00b7 {margin}"
