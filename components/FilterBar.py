"""The filter bar: date range, feed type, source and branches per view."""

import pandas as pd
from dash import dcc, html

from components.ExplorerIds import ExplorerIds


class FilterBar:
    """Filters that every card, count and chart on the page responds to."""

    SOURCE_OPTION_LIMIT = 600

    def build(
        self, articles: pd.DataFrame, last_load_time: pd.Timestamp, branch_choices: tuple, default_branches: int
    ) -> html.Div:
        published = articles["published_at"].dropna()
        feed_counts = articles["source_type"].value_counts()
        source_counts = articles["source"].value_counts().head(self.SOURCE_OPTION_LIMIT)
        return html.Div(
            [
                self.field(
                    "Published (UTC)",
                    dcc.DatePickerRange(
                        id=ExplorerIds.DATE_RANGE,
                        min_date_allowed=published.min().date(),
                        max_date_allowed=published.max().date(),
                        initial_visible_month=last_load_time.date(),
                        clearable=True,
                        display_format="MMM D, YYYY",
                        start_date_placeholder_text="All dates",
                        end_date_placeholder_text="Today",
                    ),
                    "filter-dates",
                ),
                self.field(
                    "Feed",
                    dcc.Checklist(
                        id=ExplorerIds.SOURCE_TYPES,
                        options=[
                            {"label": f" {feed.upper()} ({count:,})", "value": feed}
                            for feed, count in feed_counts.items()
                        ],
                        value=[],
                        inline=True,
                        className="feed-checklist",
                    ),
                    "filter-feeds",
                ),
                self.field(
                    f"Source (largest {len(source_counts):,})",
                    dcc.Dropdown(
                        id=ExplorerIds.SOURCES,
                        options=[
                            {"label": f"{source} ({count:,})", "value": source}
                            for source, count in source_counts.items()
                        ],
                        value=[],
                        multi=True,
                        placeholder="All sources",
                    ),
                    "filter-sources",
                ),
                self.field(
                    "Branches per view",
                    dcc.Dropdown(
                        id=ExplorerIds.BRANCHES,
                        options=[{"label": str(choice), "value": choice} for choice in branch_choices],
                        value=default_branches,
                        clearable=False,
                        searchable=False,
                    ),
                    "filter-branches",
                ),
                html.Div(id=ExplorerIds.FILTER_NOTE, className="filter-note"),
            ],
            className="filter-bar",
        )

    @staticmethod
    def field(label: str, control, class_name: str) -> html.Div:
        return html.Div([html.Label(label, className="field-label"), control], className=f"field {class_name}")
