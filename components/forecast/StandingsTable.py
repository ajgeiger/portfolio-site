"""Tournament standings for one horizon bucket: every champion, challenger and the naive baseline."""

import pandas as pd
from dash import html

from analytics.forecast.TournamentResults import TournamentResults
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class StandingsTable:
    """Rank, model, blended score with its backtest and production parts, and a status."""

    BADGES = {
        "Winner": "is-winner",
        "Qualified": "is-qualified",
        "Baseline": "is-baseline",
        "Champion": "is-champion",
        "In trials": "is-trial",
        "Below the 1% bar": "is-below",
        "Breaks rules": "is-below",
    }

    def build(self, standings: pd.DataFrame) -> html.Table:
        if standings.empty:
            return html.Div("No standings yet.", className="panel-note")
        header = html.Thead(
            html.Tr(
                [
                    html.Th("Rank", className="number rank-cell"),
                    html.Th("Model"),
                    html.Th("Blended MAE", className="number"),
                    html.Th("Backtest MAE", className="number"),
                    html.Th("Production MAE, weight", className="number"),
                    html.Th("Status"),
                ]
            )
        )
        body = [self.row(row) for _, row in standings.iterrows()]
        return html.Table([header, html.Tbody(body)], className="deck-table compact standings")

    def row(self, row: pd.Series) -> html.Tr:
        status = TournamentResults.status(row)
        family, role = ForecastModels.stage_parts(row["stage"])
        return html.Tr(
            [
                html.Td(str(int(row["rank"])), className="number rank-cell"),
                html.Td(
                    [
                        html.Div(
                            [
                                html.Span(className="model-dot", style={"background": ForecastModels.color(family)}),
                                ForecastModels.name(family),
                            ]
                        ),
                        html.Div(
                            f"{ForecastModels.ROLE_NAMES.get(role, role).lower()} v{row['model_version']}",
                            className="cell-note indent",
                        ),
                    ],
                    className="model-cell",
                ),
                html.Td(Formats.decimal(row["blended_mae"]), className="number strong"),
                html.Td(Formats.decimal(row["backtest_mae"]), className="number"),
                html.Td(
                    self.production(row), className="number" + (" role-cell" if int(row["prod_days"]) == 0 else "")
                ),
                html.Td(html.Span(status, className=f"badge {self.BADGES[status]}")),
            ],
            className="is-top" if status == "Winner" else None,
        )

    @staticmethod
    def production(row: pd.Series) -> str:
        """Production MAE and its weight in the blend. With no matured days there is no MAE and the weight is zero."""
        days, weight = int(row["prod_days"]), Formats.percent(row["prod_weight"], 0)
        if days == 0:
            return f"0 days · {weight}"
        return f"{Formats.decimal(row['prod_mae'])} · {weight}"
