"""Read the natural gas forecast snapshot written by ForecastSnapshotBuilder."""

import json
from pathlib import Path

import pandas as pd

from config.Settings import Settings
from data.forecast.ForecastSnapshotBuilder import ForecastSnapshotBuilder


class ForecastCache:
    """Serve the snapshot tables. A missing file gives an empty table, so the page still renders.

    Dates stay as YYYY-MM-DD text in the files and become pandas timestamps here.
    """

    DATE_COLUMNS = ("as_of_date", "target_date", "date", "first_as_of_date", "last_as_of_date", "trial_started")

    def __init__(self, settings: Settings | None = None, folder: Path | None = None):
        self.settings = settings or Settings()
        self.folder = Path(folder or self.settings.natgas_cache_folder)
        self._tables = {}

    @property
    def available(self) -> bool:
        """True when the snapshot holds backtest results."""
        return (self.folder / ForecastSnapshotBuilder.BACKTEST_FILE).exists() and not self.backtest().empty

    def backtest(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.BACKTEST_FILE, ForecastSnapshotBuilder.BACKTEST_COLUMNS)

    def prices(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.PRICES_FILE, ["date", "high"])

    def predictions(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.PREDICTIONS_FILE, ForecastSnapshotBuilder.PREDICTION_COLUMNS)

    def actuals(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.ACTUALS_FILE, ForecastSnapshotBuilder.ACTUAL_COLUMNS)

    def accuracy(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.ACCURACY_FILE, [])

    def rolling_accuracy(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.ROLLING_FILE, [])

    def standings(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.STANDINGS_FILE, ForecastSnapshotBuilder.STANDING_COLUMNS)

    def events(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.EVENTS_FILE, ForecastSnapshotBuilder.EVENT_COLUMNS)

    def trials(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.TRIALS_FILE, ForecastSnapshotBuilder.TRIAL_COLUMNS)

    def promotions(self) -> pd.DataFrame:
        return self.table(ForecastSnapshotBuilder.PROMOTIONS_FILE, ForecastSnapshotBuilder.PROMOTION_COLUMNS)

    def metadata(self) -> dict:
        path = self.folder / ForecastSnapshotBuilder.METADATA_FILE
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def table(self, file_name: str, columns: list[str]) -> pd.DataFrame:
        if file_name not in self._tables:
            path = self.folder / file_name
            frame = pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=columns)
            for column in self.DATE_COLUMNS:
                if column in frame.columns:
                    frame[column] = pd.to_datetime(frame[column])
            if "run_timestamp" in frame.columns:
                frame["run_timestamp"] = pd.to_datetime(frame["run_timestamp"], utc=True)
            self._tables[file_name] = frame
        return self._tables[file_name]
