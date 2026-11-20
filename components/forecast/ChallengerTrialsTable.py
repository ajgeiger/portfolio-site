"""Each family's challenger and how far it is through its trial."""

import pandas as pd
from dash import html

from config.ForecastModels import ForecastModels
from config.Formats import Formats


class ChallengerTrialsTable:
    """Family, champion and challenger versions, trial progress, both MAEs and the trial status."""

    def build(self, trials: pd.DataFrame) -> html.Table:
        if trials.empty:
            return html.Div("No challengers in trials.", className="panel-note")
        header = html.Thead(
            html.Tr(
                [
                    html.Th("Family"),
                    html.Th("Champion"),
                    html.Th("Challenger"),
                    html.Th("Trial"),
                    html.Th("Champion MAE", className="number"),
                    html.Th("Challenger MAE", className="number"),
                    html.Th("Status"),
                ]
            )
        )
        body = [self.row(row) for _, row in trials.iterrows()]
        return html.Table([header, html.Tbody(body)], className="deck-table compact trials")

    @staticmethod
    def row(row: pd.Series) -> html.Tr:
        days, required = int(row["trial_days"]), int(row["required_days"])
        progress = min(days / required, 1.0) if required else 0.0
        return html.Tr(
            [
                html.Td(
                    [
                        html.Span(className="model-dot", style={"background": ForecastModels.color(row["family"])}),
                        ForecastModels.name(row["family"]),
                    ],
                    className="model-cell",
                ),
                html.Td(f"v{row['champion_version']}"),
                html.Td(f"v{row['challenger_version']}"),
                html.Td(
                    html.Div(
                        [
                            html.Div(html.Div(style={"width": f"{progress:.0%}"}), className="trial-bar"),
                            html.Span(f"{days} of {required} days", className="trial-days"),
                        ],
                        className="trial-progress",
                    )
                ),
                html.Td(Formats.decimal(row["champion_mae"]), className="number"),
                html.Td(Formats.decimal(row["challenger_mae"]), className="number"),
                html.Td(html.Span(str(row["status"]).capitalize(), className="badge is-trial")),
            ]
        )
