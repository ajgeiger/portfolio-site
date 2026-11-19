"""What the live section shows before any forecast has matured."""

import pandas as pd
from dash import html

from config.Formats import Formats


class PendingState:
    """A calm placeholder that says when the first actual is due."""

    def build(self, first_target: pd.Timestamp | None, forecasts: int) -> html.Div:
        if first_target is None:
            detail = "No live forecasts have been scored yet."
        else:
            detail = (
                f"{Formats.count(forecasts)} live forecasts are waiting for their target dates. "
                f"The first is due on {Formats.date(first_target)}, once that session settles."
            )
        return html.Div(
            [
                html.Div(html.Span(className="pending-dot"), className="pending-icon"),
                html.Div(
                    [
                        html.H4("Actuals pending"),
                        html.P("Actuals fill in as target dates settle. " + detail),
                        html.P(
                            "Once they do, this section compares each stage with the settled price and tracks "
                            "rolling error over the last 20 as-of dates.",
                            className="muted",
                        ),
                    ]
                ),
            ],
            className="pending-state",
        )
