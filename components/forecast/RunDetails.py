"""The facts about one production scoring run."""

import pandas as pd
from dash import html

from analytics.forecast.PredictionRuns import PredictionRuns
from config.Formats import Formats


class RunDetails:
    """Run id, as-of date, scoring time, horizon and how many contenders were scored."""

    def build(self, run: pd.DataFrame) -> html.Div:
        if run.empty:
            return html.Div()
        items = [
            ("Run", str(run["run_id"].iloc[0])[:8]),
            ("As-of date", Formats.date(run["as_of_date"].max())),
            ("Scored", Formats.date_time(run["run_timestamp"].min())),
            ("Horizon", f"{int(run['horizon_day'].max())} trading days"),
            ("Contenders", str(PredictionRuns.contender_count(run["stage"]))),
        ]
        return html.Dl(
            [html.Div([html.Dt(label), html.Dd(value)], className="run-fact") for label, value in items],
            className="run-facts",
        )
