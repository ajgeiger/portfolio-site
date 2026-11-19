"""Shared look for every chart on the natural gas forecast page."""

from abc import ABC, abstractmethod

import plotly.graph_objects as go

from config.Theme import Theme


class AbstractForecastFigure(ABC):
    """A chart class builds one Plotly figure. This base gives them the same axes, legend and hover."""

    HEIGHT = 360
    PRICE_AXIS = "$/MMBtu"

    def layout(self, height: int | None = None, y_title: str = PRICE_AXIS) -> dict:
        settings = Theme.figure_layout(height or self.HEIGHT)
        settings.update(
            {
                "margin": {"l": 56, "r": 16, "t": 36, "b": 40},
                "showlegend": True,
                "legend": {"orientation": "h", "x": 0, "y": 1.1, "font": {"size": 12}, "bgcolor": "rgba(0,0,0,0)"},
                "hovermode": "x unified",
                "xaxis": {"showgrid": False, "linecolor": Theme.LINE, "ticks": "outside", "tickcolor": Theme.LINE},
                "yaxis": {
                    "title": {"text": y_title, "font": {"size": 12, "color": Theme.MUTED}},
                    "gridcolor": Theme.GRAY_SOFT,
                    "zeroline": False,
                },
            }
        )
        return settings

    def empty(self, message: str, height: int | None = None) -> go.Figure:
        """A blank chart with a short note, used when there is nothing to draw."""
        figure = go.Figure()
        figure.update_layout(**Theme.figure_layout(height or self.HEIGHT))
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        figure.add_annotation(
            text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper", font={"color": Theme.MUTED}
        )
        return figure

    @staticmethod
    def band(dates, lower, upper, name: str, fill: str, legend_group: str | None = None) -> list[go.Scatter]:
        """Two traces that shade the area between lower and upper."""
        common = {"x": list(dates), "mode": "lines", "line": {"width": 0}, "legendgroup": legend_group or name}
        return [
            go.Scatter(y=list(upper), showlegend=False, hoverinfo="skip", **common),
            go.Scatter(
                y=list(lower),
                fill="tonexty",
                fillcolor=fill,
                name=name,
                hovertemplate="%{y:.3f}",
                **common,
            ),
        ]

    @abstractmethod
    def build(self, *args, **kwargs) -> go.Figure:
        """Return the finished figure."""
