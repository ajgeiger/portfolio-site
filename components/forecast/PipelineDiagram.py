"""A five step diagram of how a forecast travels from raw data to this page."""

from dash import html


class PipelineDiagram:
    """Rounded step cards joined by small arrows. Steps wrap on narrow screens."""

    STEPS = (
        ("Data refresh", "Reload the last 30 days of prices, weather and EIA storage, so late corrections land."),
        ("Scoring", "Refit the champion and challenger through the as-of date and forecast 30 trading days."),
        ("Actuals backfill", "Copy every forecast whose target date has a settled price, with its error."),
        ("Monitoring", "Rebuild MAE, MAPE, WAPE and bias by stage and horizon, overall and over 20 dates."),
        ("Dashboard", "Snapshot the tables into small files that this page reads. No model runs here."),
    )

    def build(self) -> html.Div:
        items = []
        for index, (title, text) in enumerate(self.STEPS, start=1):
            if index > 1:
                items.append(html.Div("\u2192", className="pipeline-arrow", **{"aria-hidden": "true"}))
            items.append(
                html.Div(
                    [html.Div(f"Step {index}", className="pipeline-step"), html.H4(title), html.P(text)],
                    className="pipeline-card",
                )
            )
        return html.Div(items, className="pipeline")
