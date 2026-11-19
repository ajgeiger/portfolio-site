"""A pair of back to back time periods used to spot rising topics."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ComparisonWindow:
    """A recent period and the equally long period just before it."""

    key: str
    label: str
    length: pd.Timedelta
