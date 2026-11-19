"""The four summary cards across the top of the explorer."""

from dash import html

from analytics.CoverageSummary import CoverageSummary
from components.ExplorerIds import ExplorerIds
from config.Formats import Formats


class SummaryCards:
    """Build the four clickable cards. Each card opens the group it describes."""

    def build(self, summary: CoverageSummary, current_key: str) -> list:
        cards = [
            (
                "all_topics",
                "Articles in view",
                Formats.count(summary.total_rows),
                f"{Formats.count(summary.rows_with_text)} with usable text",
                "accent",
            ),
            (
                "assigned",
                "Assigned to topics",
                Formats.count(summary.assigned_rows),
                f"{Formats.count(summary.topic_count)} topics \u00b7 "
                f"{Formats.percent(summary.assigned_share)} of articles with text",
                "teal",
            ),
            (
                "unassigned",
                "Unassigned",
                Formats.count(summary.unassigned_rows),
                f"{Formats.percent(summary.unassigned_share)} \u00b7 one off or vague stories (topic -1)",
                "muted",
            ),
            (
                "missing",
                "Missing text",
                Formats.count(summary.missing_rows),
                f"{Formats.percent(summary.missing_share)} of all rows \u00b7 blank headline",
                "coral",
            ),
        ]
        return [
            self.card(key, title, value, detail, tone, key == current_key) for key, title, value, detail, tone in cards
        ]

    @staticmethod
    def card(key: str, title: str, value: str, detail: str, tone: str, is_active: bool):
        class_name = f"summary-card tone-{tone}" + (" is-active" if is_active else "")
        return html.Button(
            [
                html.Div(title, className="summary-card-title"),
                html.Div(value, className="summary-card-value"),
                html.Div(detail, className="summary-card-detail"),
            ],
            id={"type": ExplorerIds.SUMMARY_CARD, "key": key},
            className=class_name,
            n_clicks=0,
            title=f"Open {title.lower()}",
        )
