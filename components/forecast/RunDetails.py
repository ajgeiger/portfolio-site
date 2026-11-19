"""The facts about one production scoring run."""

import pandas as pd
from dash import html

from config.ForecastModels import ForecastModels
from config.Formats import Formats


class RunDetails:
    """Run id, as-of date, scoring time, horizon and the version in each stage."""

    def build(self, run: pd.DataFrame) -> html.Div:
        if run.empty:
            return html.Div()
        items = [
            ("Run", str(run["run_id"].iloc[0])[:8]),
            ("As-of date", Formats.date(run["as_of_date"].max())),
            ("Scored", Formats.date_time(run["run_timestamp"].min())),
            ("Horizon", f"{int(run['horizon_day'].max())} trading days"),
        ]
        for stage, name in ForecastModels.STAGE_NAMES.items():
            rows = run[run["stage"] == stage]
            if len(rows):
                items.append((name, f"{ForecastModels.name(rows['model'].iloc[0])} v{rows['model_version'].iloc[0]}"))
        return html.Dl(
            [html.Div([html.Dt(label), html.Dd(value)], className="run-fact") for label, value in items],
            className="run-facts",
        )
