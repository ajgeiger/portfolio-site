"""Key points on each stage's forecast path for one live run."""

import pandas as pd
from dash import html

from config.ForecastModels import ForecastModels
from config.Formats import Formats


class StagedRunTable:
    """Day 1, day 10 and day 30 forecasts per stage, with the model version and the band where there is one."""

    DAYS = (1, 10, 30)

    def build(self, run: pd.DataFrame) -> html.Div:
        if run.empty:
            return html.Div("No live runs yet.", className="panel-note")
        header = html.Thead(
            html.Tr([html.Th("Stage")] + [html.Th(f"Day {day}", className="number") for day in self.DAYS])
        )
        body = []
        for stage, name in ForecastModels.STAGE_NAMES.items():
            rows = run[run["stage"] == stage].set_index("horizon_day")
            if rows.empty:
                continue
            model = f"{ForecastModels.name(rows['model'].iloc[0])} v{rows['model_version'].iloc[0]}"
            cells = [
                html.Td(
                    [
                        html.Div(
                            [
                                html.Span(
                                    className="model-dot", style={"background": ForecastModels.STAGE_COLORS[stage]}
                                ),
                                name,
                            ]
                        ),
                        html.Div(model, className="cell-note indent"),
                    ],
                    className="model-cell",
                )
            ]
            for day in self.DAYS:
                cells.append(html.Td(self.point(rows, day), className="number"))
            body.append(html.Tr(cells))
        target_dates = run.drop_duplicates("horizon_day").set_index("horizon_day")["target_date"]
        footer = html.Tr(
            [html.Td("Target date", className="role-cell")]
            + [html.Td(Formats.date(target_dates.get(day)), className="number role-cell") for day in self.DAYS]
        )
        return html.Table([header, html.Tbody(body + [footer])], className="deck-table compact")

    @staticmethod
    def point(rows: pd.DataFrame, day: int):
        if day not in rows.index:
            return "n/a"
        row = rows.loc[day]
        value = Formats.decimal(row["forecast"], 3)
        if pd.isna(row["lower"]):
            return value
        band = f"{Formats.decimal(row['lower'], 3)} to {Formats.decimal(row['upper'], 3)}"
        return html.Div([html.Div(value), html.Div(band, className="cell-note")])
