"""Readable number and date formats used across the app."""

import pandas as pd


class Formats:
    """Format numbers the same way everywhere."""

    @staticmethod
    def count(value: int | float) -> str:
        return f"{int(value):,}"

    @staticmethod
    def amount(value: int, noun: str) -> str:
        """A count with its noun, such as "1 article" or "2,045 articles"."""
        return f"{int(value):,} {noun}{'' if int(value) == 1 else 's'}"

    @staticmethod
    def percent(share: float, digits: int = 1) -> str:
        if 0 < share < 0.001:
            return "<0.1%"
        return f"{share * 100:.{digits}f}%"

    @staticmethod
    def decimal(value: float, digits: int = 4) -> str:
        """A plain number with fixed decimals, such as an error in dollars per MMBtu."""
        if value is None or pd.isna(value):
            return "n/a"
        return f"{value:.{digits}f}"

    @staticmethod
    def signed(value: float, digits: int = 4) -> str:
        """A number with its sign, such as a bias."""
        if value is None or pd.isna(value):
            return "n/a"
        return f"{'+' if value >= 0 else '-'}{abs(value):.{digits}f}"

    @staticmethod
    def points(change: float) -> str:
        sign = "+" if change >= 0 else "-"
        return f"{sign}{abs(change):.1f} pts"

    @staticmethod
    def date_time(value) -> str:
        if value is None or pd.isna(value):
            return "Unknown date"
        return pd.Timestamp(value).strftime("%b %d, %Y %H:%M UTC")

    @staticmethod
    def date(value) -> str:
        if value is None or pd.isna(value):
            return "Unknown date"
        return pd.Timestamp(value).strftime("%b %d, %Y")
