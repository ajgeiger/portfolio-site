"""The model leaderboard: error measures by model for one horizon bucket."""

import pandas as pd
from dash import html

from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class LeaderboardTable:
    """A rounded table, best value in each column marked, with each model's change against naive."""

    COLUMNS = (("mae", "MAE"), ("rmse", "RMSE"), ("mape", "MAPE"), ("wape", "WAPE"), ("bias", "Bias"))

    def build(self, leaderboard: pd.DataFrame, bucket: str = ForecastAccuracy.ALL_DAYS) -> html.Table:
        rows = leaderboard[leaderboard["horizon_bucket"] == bucket].set_index("model")
        if rows.empty:
            return html.Div("No backtest data.", className="panel-note")
        baseline = rows.loc[ForecastModels.BASELINE, "mae"] if ForecastModels.BASELINE in rows.index else None
        best = {key: (rows[key].abs().idxmin() if key == "bias" else rows[key].idxmin()) for key, _ in self.COLUMNS}
        header = html.Thead(
            html.Tr(
                [html.Th("Model"), html.Th("Role")]
                + [html.Th(label, className="number") for _, label in self.COLUMNS]
                + [html.Th("MAE vs naive", className="number")]
            )
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
                html.Td(ForecastModels.ROLES.get(model, ""), className="role-cell"),
            ]
            for key, _ in self.COLUMNS:
                value = rows.loc[model, key]
                text = (
                    Formats.signed(value)
                    if key == "bias"
                    else Formats.percent(value / 100, 2)
                    if key in ("mape", "wape")
                    else Formats.decimal(value)
                )
                cells.append(html.Td(text, className="number" + (" is-best" if best[key] == model else "")))
            cells.append(html.Td(self.versus(rows.loc[model, "mae"], baseline, model), className="number"))
            body.append(html.Tr(cells, className="is-champion" if model == ForecastModels.CHAMPION else None))
        return html.Table([header, html.Tbody(body)], className="deck-table")

    @staticmethod
    def versus(mae: float, baseline: float | None, model: str) -> str:
        if baseline is None or model == ForecastModels.BASELINE:
            return "Baseline"
        change = ForecastAccuracy.improvement(mae, baseline)
        return f"{Formats.percent(abs(change), 2)} {'better' if change >= 0 else 'worse'}"
