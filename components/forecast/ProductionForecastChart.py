"""The published production forecast from one run, drawn as one segment per horizon event."""

import pandas as pd
import plotly.graph_objects as go

from analytics.forecast.PredictionRuns import PredictionRuns
from components.forecast.AbstractForecastFigure import AbstractForecastFigure
from config.ForecastModels import ForecastModels
from config.Theme import Theme


class ProductionForecastChart(AbstractForecastFigure):
    """Recent history, then the stitched production path colored by the event winner behind each segment.

    The 80% band is shaded where the winning model has one. Family champions can be
    drawn as thin dotted lines for comparison.
    """

    HEIGHT = 580
    HISTORY_COLOR = "#A3ABB8"

    def build(self, history: pd.DataFrame, run: pd.DataFrame, compare: list[str] | None = None) -> go.Figure:
        production = run[run["stage"] == ForecastModels.PRODUCTION].sort_values("horizon_day")
        if production.empty:
            return self.empty("No production runs yet.")
        figure = go.Figure()
        banded = production[production["lower"].notna()]
        if len(banded):
            figure.add_traces(
                self.band(banded["target_date"], banded["lower"], banded["upper"], "80% band", ForecastModels.BAND_FILL)
            )
        figure.add_trace(
            go.Scatter(
                x=history["date"],
                y=history["high"],
                name="History",
                mode="lines",
                line={"color": self.HISTORY_COLOR, "width": 1.6},
                hovertemplate="%{y:.3f}",
            )
        )
        for stage in compare or []:
            self.add_champion(figure, run, stage, history)
        self.add_segments(figure, production, history)
        figure.add_vline(
            x=pd.Timestamp(run["as_of_date"].max()), line={"color": Theme.LINE, "width": 1, "dash": "dash"}
        )
        figure.update_layout(**self.layout())
        figure.update_layout(
            margin={"l": 56, "r": 16, "t": 16, "b": 116},
            legend={"orientation": "h", "x": 0, "y": -0.16, "yanchor": "top"},
        )
        return figure

    def add_segments(self, figure: go.Figure, production: pd.DataFrame, history: pd.DataFrame) -> None:
        """One line per event. Each starts at the previous point so the path stays continuous."""
        previous = history.tail(1).rename(columns={"date": "target_date", "high": "forecast"})
        for segment in PredictionRuns.segments(production).itertuples():
            rows = production[production["horizon_day"].between(segment.first_day, segment.last_day)]
            path = pd.concat([previous[["target_date", "forecast"]], rows[["target_date", "forecast"]]])
            label = f"{ForecastModels.name(segment.model)}, days {segment.first_day} to {segment.last_day}"
            figure.add_trace(
                go.Scatter(
                    x=path["target_date"],
                    y=path["forecast"],
                    name=label,
                    mode="lines",
                    line={"color": ForecastModels.color(segment.model), "width": 2.8},
                    hovertemplate="%{y:.3f}",
                )
            )
            if segment.first_day > 1:
                start = rows["target_date"].iloc[0]
                figure.add_vline(x=pd.Timestamp(start), line={"color": Theme.GRAY_SOFT, "width": 1})
            previous = rows.tail(1)

    @staticmethod
    def add_champion(figure: go.Figure, run: pd.DataFrame, stage: str, history: pd.DataFrame) -> None:
        rows = run[run["stage"] == stage].sort_values("horizon_day")
        if rows.empty:
            return
        family, _ = ForecastModels.stage_parts(stage)
        anchor = history.tail(1)
        figure.add_trace(
            go.Scatter(
                x=list(anchor["date"]) + list(rows["target_date"]),
                y=list(anchor["high"]) + list(rows["forecast"]),
                name=f"{ForecastModels.stage_name(stage)} path",
                mode="lines",
                line={"color": ForecastModels.color(family), "width": 1.4, "dash": "dot"},
                opacity=0.85,
                hovertemplate="%{y:.3f}",
            )
        )
