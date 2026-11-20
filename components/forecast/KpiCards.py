"""The headline error measures at the top of the forecast page."""

from dash import html

from analytics.forecast.ForecastSummary import ForecastSummary
from config.ForecastModels import ForecastModels
from config.Formats import Formats


class KpiCards:
    """Four cards for the leading model over all 30 backtest days: MAE, MAPE, WAPE and bias, each beside naive."""

    def build(self, summary: ForecastSummary) -> html.Div:
        champion = ForecastModels.name(ForecastModels.CHAMPION)
        cards = [
            (
                "MAE",
                Formats.error("mae", summary.champion_mae),
                f"{champion} \u00b7 naive {Formats.error('mae', summary.baseline_mae)}",
                "accent",
            ),
            (
                "MAPE",
                Formats.error("mape", summary.champion_mape),
                f"{champion} \u00b7 naive {Formats.error('mape', summary.baseline_mape)}",
                "teal",
            ),
            (
                "WAPE",
                Formats.error("wape", summary.champion_wape),
                f"{champion} \u00b7 naive {Formats.error('wape', summary.baseline_wape)}",
                "amber",
            ),
            (
                "Bias",
                Formats.error("bias", summary.champion_bias),
                f"{champion} \u00b7 forecast minus actual \u00b7 naive {Formats.error('bias', summary.baseline_bias)}",
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
