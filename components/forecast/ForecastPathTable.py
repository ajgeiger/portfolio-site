"""Milestone days on the production forecast path, with the model that produced each one."""

import pandas as pd
from dash import html

from config.ForecastModels import ForecastModels
from config.Formats import Formats


class ForecastPathTable:
    """The first day of each event, day 10 and the last day, with the model and its forecast."""

    DAYS = (1, 6, 10, 16, 30)

    def build(self, production: pd.DataFrame) -> html.Div:
        if production.empty:
            return html.Div("No production runs yet.", className="panel-note")
        rows = production.set_index("horizon_day")
        header = html.Thead(
            html.Tr(
                [
                    html.Th("Day"),
                    html.Th("Model"),
                    html.Th("Forecast", className="number"),
                ]
            )
        )
        body = [self.row(day, rows.loc[day]) for day in self.DAYS if day in rows.index]
        return html.Table([header, html.Tbody(body)], className="deck-table compact path")

    @staticmethod
    def row(day: int, row: pd.Series) -> html.Tr:
        return html.Tr(
            [
                html.Td(
                    [html.Div(f"Day {day}"), html.Div(Formats.date(row["target_date"]), className="cell-note")],
                    className="model-cell",
                ),
                html.Td(
                    [
                        html.Span(className="model-dot", style={"background": ForecastModels.color(row["model"])}),
                        f"{ForecastModels.name(row['model'])} v{row['model_version']}",
                    ],
                    className="path-model",
                ),
                html.Td(Formats.decimal(row["forecast"], 3), className="number strong"),
            ]
        )
