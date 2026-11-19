"""Rolling live error over the last 20 as-of dates, one line per stage."""

import pandas as pd
import plotly.graph_objects as go

from components.forecast.AbstractForecastFigure import AbstractForecastFigure
from config.ForecastModels import ForecastModels


class RollingAccuracyChart(AbstractForecastFigure):
    """Reads the forecast_accuracy_rolling view for one horizon bucket."""

    HEIGHT = 340

    def build(self, rolling: pd.DataFrame, bucket: str = "all days", measure: str = "mae") -> go.Figure:
        rows = rolling[rolling["horizon_bucket"] == bucket].sort_values("as_of_date") if len(rolling) else rolling
        if rows.empty:
            return self.empty("Rolling accuracy starts once forecasts mature.")
        figure = go.Figure()
        for stage, name in ForecastModels.STAGE_NAMES.items():
            stage_rows = rows[rows["stage"] == stage]
            if stage_rows.empty:
                continue
            figure.add_trace(
                go.Scatter(
                    x=stage_rows["as_of_date"],
                    y=stage_rows[measure],
                    name=name,
                    mode="lines+markers",
                    line={"color": ForecastModels.STAGE_COLORS[stage], "width": 2},
                    marker={"size": 5},
                    hovertemplate="%{y:.4f}",
                )
            )
        figure.update_layout(**self.layout(y_title=f"Rolling {measure.upper()}"))
        return figure
