"""Count articles over time for the current selection."""

import pandas as pd


class TopicTrend:
    """Bucket articles by publish time into hourly, daily or weekly counts.

    The chart window ends at the last load. It starts window_days earlier, or
    later when almost every article is newer than that: the start moves up to
    the day where the earliest covered_share of articles begin, so a corpus
    collected over one day is not squeezed into the right edge of a week.
    A date filter always sets the window directly. Articles outside the window, such as old
    pages a feed picked up again, are counted and reported instead of being
    drawn, so a few stray dates cannot squash the chart.
    """

    FREQUENCIES = {"hour": "h", "day": "D", "week": "W-MON"}

    def __init__(self, last_load_time: pd.Timestamp, window_days: int = 7, published=None, covered_share: float = 0.99):
        self.last_load_time = pd.Timestamp(last_load_time)
        self.window_days = window_days
        self.default_start = self.last_load_time - pd.Timedelta(days=window_days)
        if published is not None:
            dates = pd.Series(published).dropna()
            dates = dates[(dates >= self.default_start) & (dates <= self.last_load_time)]
            if len(dates):
                busy_start = dates.quantile(1 - covered_share).floor("D")
                self.default_start = max(self.default_start, busy_start)

    def window(self, start_date: str | None = None, end_date: str | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Return the start and end of the chart window in UTC."""
        end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1) if end_date else self.last_load_time
        if start_date:
            start = pd.Timestamp(start_date, tz="UTC")
        elif end_date:
            start = end - pd.Timedelta(days=self.window_days)
        else:
            start = self.default_start
        return start, end

    @staticmethod
    def default_granularity(start: pd.Timestamp, end: pd.Timestamp) -> str:
        """Hourly up to a week, daily up to three months, weekly beyond that."""
        span = end - start
        if span <= pd.Timedelta(days=7):
            return "hour"
        if span <= pd.Timedelta(days=92):
            return "day"
        return "week"

    def counts(
        self, articles: pd.DataFrame, granularity: str, start: pd.Timestamp, end: pd.Timestamp
    ) -> tuple[pd.DataFrame, int]:
        """Return (a table of period and count, number of articles outside the window).

        Every period in the window appears, with zero when nothing was published.
        """
        frequency = self.FREQUENCIES[granularity]
        published = articles["published_at"].dropna()
        inside = published[(published >= start) & (published <= end)]
        outside = int(len(articles) - len(inside))

        if granularity == "week":
            periods = inside.dt.tz_localize(None).dt.to_period(frequency).dt.start_time.dt.tz_localize("UTC")
            first = start.tz_localize(None).to_period(frequency).start_time.tz_localize("UTC")
        else:
            periods = inside.dt.floor(frequency)
            first = start.floor(frequency)
        step = pd.Timedelta(weeks=1) if granularity == "week" else pd.Timedelta(1, unit=frequency)
        full_range = pd.date_range(first, end, freq=step)
        counted = periods.value_counts().reindex(full_range, fill_value=0).sort_index()
        table = pd.DataFrame({"period": counted.index, "count": counted.to_numpy()})
        return table, outside
