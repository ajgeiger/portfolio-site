"""The latest round of the model tournament: standings per event, event winners and challenger trials."""

import pandas as pd

from analytics.forecast.ForecastAccuracy import ForecastAccuracy
from config.ForecastModels import ForecastModels


class TournamentResults:
    """Read the tournament tables for the most recent as-of date.

    Every family champion competes in three horizon events. A champion qualifies for
    an event when it beats naive there by at least the qualifying margin on the blended
    score, and the qualified champion with the lowest blended MAE wins. When nobody
    qualifies, naive wins. Challengers are scored in trials and cannot win an event.
    """

    MIN_IMPROVEMENT = 0.01
    EVENTS = ForecastAccuracy.BUCKET_ORDER[:-1]

    def __init__(self, standings: pd.DataFrame, events: pd.DataFrame, trials: pd.DataFrame):
        self.all_standings = standings
        self.all_events = events
        self.all_trials = trials

    @property
    def empty(self) -> bool:
        return self.all_events.empty and self.all_standings.empty

    @property
    def as_of_date(self) -> pd.Timestamp | None:
        dates = pd.concat([self.all_events["as_of_date"], self.all_standings["as_of_date"]])
        return None if dates.empty else pd.Timestamp(dates.max())

    def latest(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty or self.as_of_date is None:
            return frame.iloc[0:0]
        return frame[frame["as_of_date"] == self.as_of_date].reset_index(drop=True)

    def events(self) -> pd.DataFrame:
        """The three event winners, in horizon order."""
        return self.latest(self.all_events).sort_values("first_day").reset_index(drop=True)

    def standings(self, bucket: str) -> pd.DataFrame:
        """Every contender for one horizon bucket, best rank first."""
        rows = self.latest(self.all_standings)
        return rows[rows["horizon_bucket"] == bucket].sort_values("rank").reset_index(drop=True)

    def trials(self) -> pd.DataFrame:
        """One row per family, in display order."""
        rows = self.latest(self.all_trials)
        order = {family: index for index, family in enumerate(ForecastModels.ORDER)}
        return rows.sort_values("family", key=lambda families: families.map(order)).reset_index(drop=True)

    def families(self) -> list[str]:
        """The competing model families, without the naive baseline."""
        rows = self.latest(self.all_standings)
        families = rows.loc[rows["role"] != "baseline", "family"].unique()
        return ForecastModels.ordered(families)

    def winner(self, bucket: str) -> pd.Series | None:
        rows = self.events()
        rows = rows[rows["horizon_bucket"] == bucket]
        return None if rows.empty else rows.iloc[0]

    @classmethod
    def status(cls, row: pd.Series) -> str:
        """A short label for one standings row. All days is a ranking, not an event, so it has no winner."""
        if row["horizon_bucket"] not in cls.EVENTS:
            return {"baseline": "Baseline", "challenger": "In trials"}.get(row["role"], "Champion")
        if bool(row["is_winner"]):
            return "Winner"
        if row["role"] == "baseline":
            return "Baseline"
        if row["role"] == "challenger":
            return "In trials"
        if not bool(row["rules_passed"]):
            return "Breaks rules"
        return "Qualified" if bool(row["qualified"]) else "Below the 1% bar"

    def production_days(self) -> int:
        """The most matured production days any contender has, which sets the weight of production in the score."""
        rows = self.latest(self.all_standings)
        return 0 if rows.empty else int(rows["prod_days"].max())
