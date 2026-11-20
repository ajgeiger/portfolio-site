"""The headline error measures at the top of the forecast page."""

from dash import html

from analytics.forecast.ForecastSummary import ForecastSummary
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class KpiCards:
    """Four cards for the best model over all 30 backtest days: MAPE, WAPE, MAE and bias, each against naive."""

    def build(self, summary: ForecastSummary) -> html.Div:
        champion = ForecastModels.name(ForecastModels.CHAMPION)
        cards = [
            (
                "MAPE",
                Formats.percent(summary.champion_mape / 100, 2),
                f"{champion} \u00b7 naive {Formats.percent(summary.baseline_mape / 100, 2)}",
                "accent",
            ),
            (
                "WAPE",
                Formats.percent(summary.champion_wape / 100, 2),
                f"{champion} \u00b7 naive {Formats.percent(summary.baseline_wape / 100, 2)}",
                "teal",
            ),
            (
                "MAE",
                Formats.decimal(summary.champion_mae),
                f"{champion} \u00b7 naive {Formats.decimal(summary.baseline_mae)} \u00b7 "
                f"{Formats.percent(summary.improvement, 2)} lower",
                "amber",
            ),
            (
                "Bias",
                Formats.signed(summary.champion_bias),
                f"{champion} \u00b7 forecast minus actual \u00b7 naive {Formats.signed(summary.baseline_bias)}",
                "navy",
            ),
        ]
        return html.Div([self.card(*card) for card in cards], className="kpi-cards")

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
