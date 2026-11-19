"""The production and staging forecast paths from one live run."""

import pandas as pd
import plotly.graph_objects as go

from components.forecast.AbstractForecastFigure import AbstractForecastFigure
from config.ForecastModels import ForecastModels
from config.Theme import Theme


class StagedForecastChart(AbstractForecastFigure):
    """Recent history, then each stage's 30 day path. The production band is shaded."""

    HEIGHT = 380
    STAGES = ("production", "staging")

    def build(self, history: pd.DataFrame, run: pd.DataFrame) -> go.Figure:
        if run.empty:
            return self.empty("No live runs yet.")
        figure = go.Figure()
        production = run[run["stage"] == "production"]
        if production["lower"].notna().any():
            figure.add_traces(
                self.band(
                    production["target_date"],
                    production["lower"],
                    production["upper"],
                    "Production 80% band",
                    ForecastModels.BAND_FILL,
                )
            )
        figure.add_trace(
            go.Scatter(
                x=history["date"],
                y=history["high"],
                name="History",
                mode="lines",
                line={"color": Theme.MUTED, "width": 1.6},
                hovertemplate="%{y:.3f}",
            )
        )
        for stage in self.STAGES:
            rows = run[run["stage"] == stage]
            if rows.empty:
                continue
            model = ForecastModels.name(rows["model"].iloc[0])
            version = rows["model_version"].iloc[0]
            anchor = history.tail(1)
            figure.add_trace(
                go.Scatter(
                    x=list(anchor["date"]) + list(rows["target_date"]),
                    y=list(anchor["high"]) + list(rows["forecast"]),
                    name=f"{ForecastModels.STAGE_NAMES[stage]}: {model} v{version}",
                    mode="lines",
                    line={"color": ForecastModels.STAGE_COLORS[stage], "width": 2.6 if stage == "production" else 2},
                    hovertemplate="%{y:.3f}",
                )
            )
        as_of = run["as_of_date"].max()
        figure.add_vline(x=pd.Timestamp(as_of), line={"color": Theme.LINE, "width": 1, "dash": "dash"})
        figure.update_layout(**self.layout())
        return figure
