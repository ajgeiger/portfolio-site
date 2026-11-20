"""History, the 30 day forecast fan and the actuals for one backtest as-of date."""

import pandas as pd
import plotly.graph_objects as go

from analytics.forecast.BacktestWindow import BacktestWindow
from components.forecast.AbstractForecastFigure import AbstractForecastFigure
from config.ForecastModels import ForecastModels
from config.Theme import Theme


class BacktestFanChart(AbstractForecastFigure):
    """Price history up to the as-of date, then the champion, a second model and the actuals."""

    HEIGHT = 400

    def build(self, window: BacktestWindow, as_of: pd.Timestamp, models: list[str]) -> go.Figure:
        history = window.history(as_of)
        actuals = window.actuals(as_of)
        if history.empty and actuals.empty:
            return self.empty("No backtest data for this date.")

        figure = go.Figure()
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
        figure.add_trace(
            go.Scatter(
                x=actuals["target_date"],
                y=actuals["actual"],
                name="Actual",
                mode="lines+markers",
                line={"color": ForecastModels.ACTUAL_COLOR, "width": 2},
                marker={"size": 4},
                hovertemplate="%{y:.3f}",
            )
        )
        for model in models:
            forecast = window.forecast(as_of, model)
            if forecast.empty:
                continue
            anchor = history.tail(1)
            dates = list(anchor["date"]) + list(forecast["target_date"])
            values = list(anchor["high"]) + list(forecast["forecast"])
            figure.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    name=ForecastModels.name(model),
                    mode="lines",
                    line={
                        "color": ForecastModels.color(model),
                        "width": 2.6 if model == ForecastModels.CHAMPION else 2,
                        "dash": "dot" if model == ForecastModels.BASELINE else "solid",
                    },
                    hovertemplate="%{y:.3f}",
                )
            )
        figure.add_vline(x=pd.Timestamp(as_of), line={"color": Theme.LINE, "width": 1, "dash": "dash"})
        figure.add_annotation(
            x=pd.Timestamp(as_of),
            y=1,
            yref="paper",
            text="As-of date",
            showarrow=False,
            xanchor="right",
            xshift=-6,
            yanchor="top",
            font={"size": 11, "color": Theme.MUTED},
        )
        figure.update_layout(**self.layout())
        return figure
