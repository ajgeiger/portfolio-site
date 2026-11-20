"""Backtest error measures by model family, the scores that seed the tournament."""

import pandas as pd
from dash import html

from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class BacktestScoreTable:
    """A rounded table of MAE, MAPE, WAPE and bias per model, with the best value in each column marked."""

    COLUMNS = (("mae", "MAE"), ("mape", "MAPE"), ("wape", "WAPE"), ("bias", "Bias"))

    def build(self, leaderboard: pd.DataFrame, bucket: str = ForecastAccuracy.ALL_DAYS) -> html.Table:
        rows = leaderboard[leaderboard["horizon_bucket"] == bucket].set_index("model")
        if rows.empty:
            return html.Div("No backtest data.", className="panel-note")
        best = {key: (rows[key].abs().idxmin() if key == "bias" else rows[key].idxmin()) for key, _ in self.COLUMNS}
        header = html.Thead(
            html.Tr([html.Th("Model")] + [html.Th(label, className="number") for _, label in self.COLUMNS])
        )
        body = []
        ordered = sorted(ForecastModels.ordered(rows.index), key=lambda model: rows.loc[model, "mae"])
        for model in ordered:
            cells = [
                html.Td(
                    [
                        html.Span(className="model-dot", style={"background": ForecastModels.color(model)}),
                        ForecastModels.name(model),
                    ],
                    className="model-cell",
                ),
            ]
            for key, _ in self.COLUMNS:
                text = Formats.error(key, rows.loc[model, key])
                cells.append(html.Td(text, className="number" + (" is-best" if best[key] == model else "")))
            body.append(html.Tr(cells))
        return html.Table([header, html.Tbody(body)], className="deck-table compact")
