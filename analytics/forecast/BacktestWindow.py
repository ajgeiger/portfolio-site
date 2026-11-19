"""One backtest as-of date: the price history before it, each model's forecast and the actuals."""

import pandas as pd


class BacktestWindow:
    """Slice the backtest and price tables for a single as-of date."""

    HISTORY_DAYS = 60

    def __init__(self, backtest: pd.DataFrame, prices: pd.DataFrame):
        self.backtest = backtest
        self.prices = prices.sort_values("date").reset_index(drop=True)

    def as_of_dates(self) -> list[pd.Timestamp]:
        return sorted(pd.to_datetime(self.backtest["as_of_date"].unique()))

    def default_as_of(self) -> pd.Timestamp | None:
        """The latest as-of date with an interval, so the first view shows the band."""
        with_band = self.backtest.dropna(subset=["lower"])
        source = with_band if len(with_band) else self.backtest
        return None if source.empty else pd.Timestamp(source["as_of_date"].max())

    def dates_without_band(self, model: str) -> list[pd.Timestamp]:
        """As-of dates where this model has forecasts but no interval."""
        rows = self.backtest[self.backtest["model"] == model]
        has_band = rows.groupby("as_of_date")["lower"].apply(lambda values: values.notna().any())
        return sorted(pd.Timestamp(date) for date in has_band[~has_band].index)

    def history(self, as_of: pd.Timestamp, days: int = HISTORY_DAYS) -> pd.DataFrame:
        """The last trading days up to and including the as-of date."""
        return self.prices[self.prices["date"] <= pd.Timestamp(as_of)].tail(days)

    def forecast(self, as_of: pd.Timestamp, model: str) -> pd.DataFrame:
        rows = self.backtest[(self.backtest["as_of_date"] == pd.Timestamp(as_of)) & (self.backtest["model"] == model)]
        return rows.sort_values("horizon_day").reset_index(drop=True)

    def actuals(self, as_of: pd.Timestamp) -> pd.DataFrame:
        """The realized price on each target date of this as-of date."""
        rows = self.backtest[self.backtest["as_of_date"] == pd.Timestamp(as_of)]
        return rows.drop_duplicates("target_date").sort_values("target_date")[["target_date", "actual"]]
