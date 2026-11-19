"""Matured live forecasts against the prices that settled."""

import pandas as pd
import plotly.graph_objects as go

from components.forecast.AbstractForecastFigure import AbstractForecastFigure
from config.ForecastModels import ForecastModels


class LiveActualsChart(AbstractForecastFigure):
    """Each stage's forecast for a target date, next to the settled price for that date."""

    HEIGHT = 340

    def build(self, actuals: pd.DataFrame, horizon_day: int = 1) -> go.Figure:
        rows = actuals[actuals["horizon_day"] == horizon_day].sort_values("target_date")
        if rows.empty:
            return self.empty(f"No matured day {horizon_day} forecasts yet.")
        figure = go.Figure()
        settled = rows.drop_duplicates("target_date")
        figure.add_trace(
            go.Scatter(
                x=settled["target_date"],
                y=settled["actual"],
                name="Actual",
                mode="lines+markers",
                line={"color": ForecastModels.ACTUAL_COLOR, "width": 2},
                marker={"size": 5},
                hovertemplate="%{y:.3f}",
            )
        )
        for stage, name in ForecastModels.STAGE_NAMES.items():
            stage_rows = rows[rows["stage"] == stage]
            if stage_rows.empty:
                continue
            figure.add_trace(
                go.Scatter(
                    x=stage_rows["target_date"],
                    y=stage_rows["forecast"],
                    name=f"{name} forecast",
                    mode="lines+markers",
                    line={"color": ForecastModels.STAGE_COLORS[stage], "width": 2},
                    marker={"size": 5},
                    hovertemplate="%{y:.3f}",
                )
            )
        figure.update_layout(**self.layout())
        return figure
