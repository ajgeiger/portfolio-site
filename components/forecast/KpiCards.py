"""The headline numbers at the top of the forecast page."""

import pandas as pd
from dash import html

from analytics.forecast.ForecastSummary import ForecastSummary
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class KpiCards:
    """Six cards: the best 30 day backtest error, each event result, interval coverage and the latest run."""

    TONES = {"chronos": "accent", "gradient_boosting": "teal", "greykite": "amber"}

    def build(self, summary: ForecastSummary, events: pd.DataFrame) -> html.Div:
        cards = [
            (
                "Best 30 day MAE",
                Formats.decimal(summary.champion_mae),
                f"{ForecastModels.name(ForecastModels.CHAMPION)} \u00b7 naive {Formats.decimal(summary.baseline_mae)} "
                f"\u00b7 {Formats.percent(summary.improvement, 2)} lower",
                "accent",
            ),
            *[self.event_card(event) for event in events.itertuples()],
            (
                "Interval coverage",
                Formats.percent(summary.coverage),
                f"Backtest actuals inside the 80% band \u00b7 {Formats.count(summary.coverage_dates)} dates",
                "amber",
            ),
            (
                "Latest production run",
                Formats.date(summary.latest_run_as_of) if summary.latest_run_as_of is not None else "None yet",
                self.run_detail(summary),
                "navy",
            ),
        ]
        return html.Div([self.card(*card) for card in cards], className="kpi-cards")

    @staticmethod
    def event_card(event) -> tuple[str, str, str, str]:
        winner = f"{ForecastModels.name(event.model)} v{event.model_version}"
        title = f"Days {int(event.first_day)} to {int(event.last_day)}"
        if event.improvement > 0:
            tone = KpiCards.TONES.get(event.model, "muted")
            return title, f"+{Formats.percent(event.improvement, 2)}", f"{winner} against naive", tone
        return title, winner, "No champion beat naive by 1%", "muted"

    @staticmethod
    def run_detail(summary: ForecastSummary) -> str:
        if summary.latest_run_time is None:
            return "Waiting for the first scoring run"
        return f"As-of date \u00b7 scored {Formats.date_time(summary.latest_run_time)}"

    @staticmethod
    def card(title: str, value: str, detail: str, tone: str) -> html.Div:
        return html.Div(
            [
                html.Div(title, className="kpi-title"),
                html.Div(value, className="kpi-value"),
                html.Div(detail, className="kpi-detail"),
            ],
            className=f"kpi-card tone-{tone}",
        )
