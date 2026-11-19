"""The list of production scoring runs. Each row is a button that opens that run."""

import pandas as pd
from dash import html

from components.forecast.ForecastIds import ForecastIds
from config.Formats import Formats


class RunList:
    """One clickable row per run, newest first, with its day 1 forecast for each stage."""

    ROW_CLASS = "run-row"
    SELECTED_CLASS = "run-row is-selected"

    def build(self, runs: pd.DataFrame, predictions: pd.DataFrame, selected: str | None) -> html.Div:
        if runs.empty:
            return html.Div("No production runs yet.", className="panel-note")
        header = html.Div(
            [html.Span("As-of date"), html.Span("Scored"), html.Span("Production day 1"), html.Span("Staging day 1")],
            className="run-row run-head",
        )
        rows = [self.row(run, predictions, run.run_id == selected) for run in runs.itertuples()]
        return html.Div([header, *rows], className="run-list", role="listbox")

    def row(self, run, predictions: pd.DataFrame, is_selected: bool) -> html.Button:
        day_one = predictions[(predictions["run_id"] == run.run_id) & (predictions["horizon_day"] == 1)]
        values = day_one.set_index("stage")["forecast"]
        return html.Button(
            [
                html.Span(Formats.date(run.as_of_date), className="run-date"),
                html.Span(Formats.date_time(run.run_timestamp)),
                html.Span(self.value(values, "production"), className="number"),
                html.Span(self.value(values, "staging"), className="number"),
            ],
            id={"type": ForecastIds.RUN_ROW, "run": run.run_id},
            className=self.class_name(is_selected),
            n_clicks=0,
            title="Show this run",
        )

    @classmethod
    def class_name(cls, is_selected: bool) -> str:
        return cls.SELECTED_CLASS if is_selected else cls.ROW_CLASS

    @staticmethod
    def value(values: pd.Series, stage: str) -> str:
        return Formats.decimal(values[stage], 3) if stage in values.index else "n/a"
