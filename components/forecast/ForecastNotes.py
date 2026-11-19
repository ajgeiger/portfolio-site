"""Method notes and caveats for the natural gas forecast, with numbers read from the data."""

import pandas as pd
from dash import html

from analytics.forecast.ForecastSummary import ForecastSummary
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class ForecastNotes:
    """Two cards: how the forecast is made, and where it falls short."""

    def build(
        self,
        summary: ForecastSummary,
        leaderboard: pd.DataFrame,
        versions: dict,
        metadata: dict,
        missing_band: list | None = None,
    ) -> html.Div:
        """versions maps each model to its registered version, such as {"chronos": "8"}.
        missing_band lists champion as-of dates without an interval.
        """
        return html.Div(
            [
                self.card("Method", self.method(summary, versions), "method"),
                self.card("Caveats", self.caveats(summary, leaderboard, metadata, missing_band or []), "caveats"),
            ],
            className="notes-grid",
        )

    @staticmethod
    def card(title: str, items: list[str], tone: str) -> html.Div:
        return html.Div(
            [html.H3(title), html.Ul([html.Li(item) for item in items])], className=f"note-card tone-{tone}"
        )

    @staticmethod
    def version(versions: dict, model: str) -> str:
        version = versions.get(model)
        return f" version {version}" if version else ""

    def method(self, summary: ForecastSummary, versions: dict) -> list[str]:
        return [
            "Target: the daily high of the front-month natural gas futures contract (Yahoo Finance NG=F), in "
            "dollars per MMBtu. Inputs are heating and cooling degree days in major gas-demand cities and EIA "
            "weekly storage. All of it is public data.",
            f"Backtest: {Formats.count(summary.as_of_dates)} as-of dates every 14 days from "
            f"{Formats.date(summary.first_as_of)} to {Formats.date(summary.last_as_of)}. At each date every model "
            f"sees only data up to that date and forecasts the next {summary.horizon_days} trading days. The "
            "backtester stops any run where training data passes the as-of date.",
            "Models: Chronos-2, a pretrained time series model used zero-shot with degree days as known future "
            "inputs; gradient boosted trees on recent price changes; Greykite trend and seasonality; and a naive "
            "baseline that repeats the last price. Each model's best configuration comes from a grid search "
            "tracked in MLflow.",
            "Promotion: a model replaces naive only when it lowers MAE by at least 1%. Chronos-2 cleared that bar "
            f"and runs in production as the registered champion{self.version(versions, ForecastModels.CHAMPION)}. "
            f"Gradient boosting{self.version(versions, ForecastModels.CHALLENGER)} runs beside it in staging as "
            "the challenger.",
            "Chronos-2 reports a 10th and 90th percentile with each forecast, which make the 80% band. The other "
            "models give a single number.",
        ]

    def caveats(
        self, summary: ForecastSummary, leaderboard: pd.DataFrame, metadata: dict, missing_band: list
    ) -> list[str]:
        short = leaderboard[leaderboard["horizon_bucket"] == "days 1 to 5"].set_index("model")["mae"]
        long = leaderboard[leaderboard["horizon_bucket"] == "days 16 to 30"].set_index("model")["mae"]
        champion, baseline = ForecastModels.CHAMPION, ForecastModels.BASELINE
        items = [
            f"The edge is modest. Chronos-2 lowers MAE by {Formats.percent(summary.improvement, 2)} against "
            f"naive. Over days 1 to 5 naive is slightly better ({Formats.decimal(short.get(baseline))} against "
            f"{Formats.decimal(short.get(champion))}); the gap opens on days 16 to 30 "
            f"({Formats.decimal(long.get(champion))} against {Formats.decimal(long.get(baseline))}).",
            f"The band is too narrow. Actuals fell inside the 80% band {Formats.percent(summary.coverage)} of the "
            f"time over {Formats.count(summary.coverage_dates)} as-of dates, so read it as a guide, not a "
            "guarantee.",
            "Weather. Backtests used observed weather for all 30 days. Live runs use the Open-Meteo weather "
            "forecast for forecast days 1 to 10, and 10 year average degree days by day of year, smoothed over "
            "15 days, for days 11 to 30. Expect live accuracy on later days to sit below the backtest.",
            "This forecasts a price, the front-month daily high, not natural gas demand or volume.",
        ]
        if missing_band:
            dates = ", ".join(Formats.date(date) for date in missing_band)
            subject = "One as-of date" if len(missing_band) == 1 else f"{Formats.count(len(missing_band))} as-of dates"
            verb = "has" if len(missing_band) == 1 else "have"
            items.append(
                f"{subject} ({dates}) {verb} no band, because the rerun that adds intervals did not match the logged "
                "forecast there. The point forecasts are kept."
            )
        if metadata.get("built_at"):
            built_at = Formats.date_time(metadata["built_at"].replace(" UTC", ""))
            items.append(f"This page reads a snapshot taken {built_at}. Rebuilding it picks up new runs and actuals.")
        return items
