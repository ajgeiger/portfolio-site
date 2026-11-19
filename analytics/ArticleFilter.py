"""Apply the date, feed and source filters to the article table."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class ArticleFilter:
    """The filters chosen in the filter bar. Empty values mean no filter.

    Dates are inclusive calendar days in UTC, given as YYYY-MM-DD strings.
    When a date filter is set, articles without a publish date drop out.
    """

    start_date: str | None = None
    end_date: str | None = None
    source_types: tuple[str, ...] = field(default_factory=tuple)
    sources: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_inputs(cls, start_date, end_date, source_types, sources) -> "ArticleFilter":
        """Build a filter from raw Dash input values, which may be None or lists."""
        return cls(
            start_date=str(start_date)[:10] if start_date else None,
            end_date=str(end_date)[:10] if end_date else None,
            source_types=tuple(source_types or ()),
            sources=tuple(sources or ()),
        )

    def is_active(self) -> bool:
        return bool(self.start_date or self.end_date or self.source_types or self.sources)

    def mask(self, articles: pd.DataFrame) -> pd.Series:
        """Return True for every article that passes all filters."""
        keep = pd.Series(True, index=articles.index)
        published = articles["published_at"]
        if self.start_date:
            keep &= published >= pd.Timestamp(self.start_date, tz="UTC")
        if self.end_date:
            keep &= published < pd.Timestamp(self.end_date, tz="UTC") + pd.Timedelta(days=1)
        if self.source_types:
            keep &= articles["source_type"].isin(self.source_types)
        if self.sources:
            keep &= articles["source"].isin(self.sources)
        return keep

    def apply(self, articles: pd.DataFrame) -> pd.DataFrame:
        if not self.is_active():
            return articles
        return articles[self.mask(articles)]
