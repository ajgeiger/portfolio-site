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
        """The latest backtest as-of date."""
        return None if self.backtest.empty else pd.Timestamp(self.backtest["as_of_date"].max())

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
