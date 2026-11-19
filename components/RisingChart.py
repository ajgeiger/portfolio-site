"""Draw the topics gaining and losing the most share of coverage."""

import pandas as pd
import plotly.graph_objects as go

from config.Theme import Theme


class RisingChart:
    """A diverging bar chart: rising topics in teal, fading topics in coral.

    Each bar carries its node key so a click can open that topic.
    """

    def figure(
        self, table: pd.DataFrame, names: dict[int, str], rising_count: int = 7, fading_count: int = 5
    ) -> go.Figure:
        rising = table[table["change_points"] > 0].head(rising_count)
        fading = table[table["change_points"] < 0].tail(fading_count)
        shown = pd.concat([rising, fading]).iloc[::-1]

        labels = [f"{names.get(topic, f'Topic {topic}')}  (T{topic})" for topic in shown["topic_id"]]
        colors = [Theme.TEAL if change > 0 else Theme.CORAL for change in shown["change_points"]]
        hover = [
            f"{label}<br>{row.recent_count:,} recent vs {row.prior_count:,} prior articles"
            f"<br>Share {row.recent_share:.1%} vs {row.prior_share:.1%}"
            for label, row in zip(labels, shown.itertuples(), strict=True)
        ]
        figure = go.Figure(
            go.Bar(
                x=shown["change_points"],
                y=labels,
                orientation="h",
                marker={"color": colors},
                customdata=[f"topic_{topic}" for topic in shown["topic_id"]],
                text=[f"{change:+.1f} pts" for change in shown["change_points"]],
                textposition="outside",
                cliponaxis=False,
                hovertext=hover,
                hovertemplate="%{hovertext}<extra></extra>",
            )
        )
        figure.update_layout(**Theme.figure_layout(max(240, 30 * len(shown) + 40)))
        figure.update_layout(margin={"l": 8, "r": 60, "t": 8, "b": 8}, bargap=0.35)
        figure.update_xaxes(
            zeroline=True,
            zerolinecolor=Theme.MUTED,
            gridcolor=Theme.GRAY_SOFT,
            ticksuffix=" pts",
            tickfont={"color": Theme.MUTED},
        )
        figure.update_yaxes(tickfont={"size": 11, "color": Theme.INK}, automargin=True)
        figure.update_xaxes(fixedrange=True)
        figure.update_yaxes(fixedrange=True)
        return figure
