"""The row of headline numbers at the top of the forecast page."""

from dash import html

from analytics.forecast.ForecastSummary import ForecastSummary
from config.Formats import Formats


class KpiCards:
    """Five cards: champion error against naive, MAPE, interval coverage, backtest dates and the latest run."""

    def build(self, summary: ForecastSummary) -> html.Div:
        cards = [
            (
                "Champion MAE",
                Formats.decimal(summary.champion_mae),
                f"Naive {Formats.decimal(summary.baseline_mae)} \u00b7 {Formats.percent(summary.improvement, 2)} lower",
                "accent",
            ),
            (
                "Champion MAPE",
                Formats.percent(summary.champion_mape / 100, 2),
                f"Naive {Formats.percent(summary.baseline_mape / 100, 2)} \u00b7 WAPE "
                f"{Formats.percent(summary.champion_wape / 100, 2)}",
                "teal",
            ),
            (
                "Interval coverage",
                Formats.percent(summary.coverage),
                f"Actuals inside the 80% band \u00b7 {Formats.count(summary.coverage_dates)} dates",
                "amber",
            ),
            (
                "Backtest dates",
                Formats.count(summary.as_of_dates),
                f"{Formats.date(summary.first_as_of)} to {Formats.date(summary.last_as_of)} \u00b7 "
                f"{summary.horizon_days} days ahead",
                "muted",
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
