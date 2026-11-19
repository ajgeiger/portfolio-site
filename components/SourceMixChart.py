"""Draw which sources cover the current selection."""

import pandas as pd
import plotly.graph_objects as go

from config.Theme import Theme


class SourceMixChart:
    """Horizontal bars of article counts per source, largest at the top."""

    def figure(self, table: pd.DataFrame) -> go.Figure:
        table = table.iloc[::-1]
        colors = [Theme.GRAY_SOFT if source.startswith("All other") else Theme.NAVY for source in table["source"]]
        figure = go.Figure(
            go.Bar(
                x=table["count"],
                y=table["source"],
                orientation="h",
                marker={"color": colors},
                text=[f"{share:.0%}" for share in table["share"]],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{y}<br>%{x:,} articles<extra></extra>",
            )
        )
        figure.update_layout(**Theme.figure_layout(260))
        figure.update_layout(margin={"l": 8, "r": 40, "t": 8, "b": 8})
        figure.update_xaxes(visible=False)
        figure.update_yaxes(tickfont={"size": 11, "color": Theme.INK}, automargin=True)
        figure.update_xaxes(fixedrange=True)
        figure.update_yaxes(fixedrange=True)
        return figure
