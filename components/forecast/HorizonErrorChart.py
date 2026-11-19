"""Mean absolute error at each day ahead, one line per model."""

import pandas as pd
import plotly.graph_objects as go

from components.forecast.AbstractForecastFigure import AbstractForecastFigure
from config.ForecastModels import ForecastModels


class HorizonErrorChart(AbstractForecastFigure):
    """How error grows with the horizon. Lower is better."""

    HEIGHT = 320

    def build(self, by_day: pd.DataFrame) -> go.Figure:
        if by_day.empty:
            return self.empty("No backtest data.")
        figure = go.Figure()
        for model in ForecastModels.ordered(by_day["model"]):
            rows = by_day[by_day["model"] == model]
            figure.add_trace(
                go.Scatter(
                    x=rows["horizon_day"],
                    y=rows["mae"],
                    name=ForecastModels.name(model),
                    mode="lines",
                    line={
                        "color": ForecastModels.color(model),
                        "width": 2.6 if model == ForecastModels.CHAMPION else 1.8,
                        "dash": "dot" if model == ForecastModels.BASELINE else "solid",
                    },
                    hovertemplate="%{y:.4f}",
                )
            )
        figure.update_layout(**self.layout(y_title="MAE, $/MMBtu"))
        figure.update_xaxes(title={"text": "Trading days ahead", "font": {"size": 12}}, dtick=5)
        return figure
