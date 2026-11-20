"""The winner of each horizon event in the latest tournament round."""

import pandas as pd
from dash import html

from config.ForecastModels import ForecastModels
from config.Formats import Formats


class EventWinners:
    """One small card per event: its days, the winning model and how it compares with naive."""

    def build(self, events: pd.DataFrame) -> html.Div:
        if events.empty:
            return html.Div("No tournament results yet.", className="panel-note")
        return html.Div([self.card(event) for event in events.itertuples()], className="event-winners")

    @staticmethod
    def card(event) -> html.Div:
        family, role = ForecastModels.stage_parts(event.stage)
        if event.improvement > 0:
            versus = f"{Formats.percent(event.improvement, 2)} better than naive"
        else:
            versus = "No champion beat naive by 1%"
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
                html.Div(versus, className="event-versus" + (" is-up" if event.improvement > 0 else "")),
            ],
            className="event-card",
        )
