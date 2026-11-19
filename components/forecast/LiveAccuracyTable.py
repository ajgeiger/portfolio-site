"""Live accuracy by stage, read from the forecast_accuracy view."""

import pandas as pd
from dash import html

from config.ForecastModels import ForecastModels
from config.Formats import Formats


class LiveAccuracyTable:
    """One row per stage for the chosen horizon bucket: forecasts scored, MAE, MAPE, WAPE and bias."""

    def build(self, accuracy: pd.DataFrame, bucket: str = "all days") -> html.Table:
        rows = accuracy[accuracy["horizon_bucket"] == bucket] if len(accuracy) else accuracy
        if rows.empty:
            return html.Div("No matured forecasts yet.", className="panel-note")
        header = html.Thead(
            html.Tr(
                [html.Th("Stage"), html.Th("Model")]
                + [html.Th(label, className="number") for label in ("Forecasts", "MAE", "MAPE", "WAPE", "Bias")]
            )
        )
        body = []
        for stage, name in ForecastModels.STAGE_NAMES.items():
            for _, row in rows[rows["stage"] == stage].iterrows():
                body.append(
                    html.Tr(
                        [
                            html.Td(
                                [
                                    html.Span(
                                        className="model-dot", style={"background": ForecastModels.STAGE_COLORS[stage]}
                                    ),
                                    name,
                                ],
                                className="model-cell",
                            ),
                            html.Td(ForecastModels.name(row["model"]), className="role-cell"),
                            html.Td(Formats.count(row["forecasts"]), className="number"),
                            html.Td(Formats.decimal(row["mae"]), className="number"),
                            html.Td(Formats.percent(row["mape"] / 100, 2), className="number"),
                            html.Td(Formats.percent(row["wape"] / 100, 2), className="number"),
                            html.Td(Formats.signed(row["bias"]), className="number"),
                        ]
                    )
                )
        return html.Table([header, html.Tbody(body)], className="deck-table compact")
