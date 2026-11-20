"""The list of production scoring runs. Each row is a button that opens that run."""

import pandas as pd
from dash import html

from components.forecast.ForecastIds import ForecastIds
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class RunList:
    """One clickable row per run, newest first, with points on its published production forecast."""

    ROW_CLASS = "run-row"
    SELECTED_CLASS = "run-row is-selected"
    DAYS = (1, 10, 30)

    def build(self, runs: pd.DataFrame, predictions: pd.DataFrame, selected: str | None) -> html.Div:
        if runs.empty:
            return html.Div("No production runs yet.", className="panel-note")
        header = html.Div(
            [html.Span("As-of date"), html.Span("Scored"), html.Span("Contenders")]
            + [html.Span(f"Day {day}") for day in self.DAYS],
            className="run-row run-head",
        )
        published = predictions[predictions["stage"] == ForecastModels.PRODUCTION]
        rows = [self.row(run, published, run.run_id == selected) for run in runs.itertuples()]
        return html.Div([header, *rows], className="run-list", role="listbox")

    def row(self, run, published: pd.DataFrame, is_selected: bool) -> html.Button:
        values = published[published["run_id"] == run.run_id].set_index("horizon_day")["forecast"]
        return html.Button(
            [
                html.Span(Formats.date(run.as_of_date), className="run-date"),
                html.Span(Formats.date_time(run.run_timestamp)),
                html.Span(str(run.contenders)),
            ]
            + [html.Span(self.value(values, day), className="number") for day in self.DAYS],
            id={"type": ForecastIds.RUN_ROW, "run": run.run_id},
            className=self.class_name(is_selected),
            n_clicks=0,
            title="Show this run",
        )

    @classmethod
    def class_name(cls, is_selected: bool) -> str:
        return cls.SELECTED_CLASS if is_selected else cls.ROW_CLASS

    @staticmethod
    def value(values: pd.Series, day: int) -> str:
        return Formats.decimal(values[day], 3) if day in values.index else "n/a"
