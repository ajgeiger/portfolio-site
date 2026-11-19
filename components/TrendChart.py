"""Draw article counts over time for the current selection."""

import pandas as pd
import plotly.graph_objects as go

from config.Theme import Theme


class TrendChart:
    """An area chart of article counts per hour, day or week."""

    HOVER_FORMATS = {"hour": "%b %d, %H:00 UTC", "day": "%b %d, %Y", "week": "Week of %b %d, %Y"}

    def figure(self, table: pd.DataFrame, granularity: str) -> go.Figure:
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=table["period"],
                y=table["count"],
                mode="lines",
                line={"color": Theme.ACCENT, "width": 2, "shape": "hv" if granularity != "hour" else "linear"},
                fill="tozeroy",
                fillcolor="rgba(31, 94, 255, 0.12)",
                hovertemplate=f"%{{x|{self.HOVER_FORMATS[granularity]}}}<br>%{{y:,}} articles<extra></extra>",
            )
        )
        if len(table) and table["count"].max() > 0:
            peak = table.loc[table["count"].idxmax()]
            figure.add_annotation(
                x=peak["period"],
                y=peak["count"],
                text=f"Peak {int(peak['count']):,}",
                showarrow=False,
                yshift=12,
                font={"size": 11, "color": Theme.NAVY},
            )
        figure.update_layout(**Theme.figure_layout(260))
        figure.update_xaxes(showgrid=False, linecolor=Theme.LINE, tickfont={"color": Theme.MUTED})
        figure.update_yaxes(gridcolor=Theme.GRAY_SOFT, zeroline=False, tickformat=",", tickfont={"color": Theme.MUTED})
        figure.update_xaxes(fixedrange=True)
        figure.update_yaxes(fixedrange=True)
        return figure
