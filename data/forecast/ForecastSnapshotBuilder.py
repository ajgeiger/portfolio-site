"""Copy the natural gas forecast outputs into small files the website can read."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from config.Settings import Settings


class ForecastSnapshotBuilder:
    """Read the natural-gas-forecasting database and backtest export, then write a snapshot.

    The source is opened read only and nothing is scored or refit. A hosted copy
    of the site cannot see the source database, so the page reads only the
    files written here. Run it again to pick up new predictions and actuals.

    Files written:
        backtest_forecasts.parquet         every backtest forecast with its actual
        prices.parquet                     settled daily front-month highs, the forecast target
        predictions.parquet                every live forecast run, both stages
        forecast_actuals.parquet           live forecasts whose target date has a price
        forecast_accuracy.parquet          the source accuracy view
        forecast_accuracy_rolling.parquet  the source rolling accuracy view
        metadata.json                      row counts, date ranges and the latest run
    """

    BACKTEST_FILE = "backtest_forecasts.parquet"
    PRICES_FILE = "prices.parquet"
    PREDICTIONS_FILE = "predictions.parquet"
    ACTUALS_FILE = "forecast_actuals.parquet"
    ACCURACY_FILE = "forecast_accuracy.parquet"
    ROLLING_FILE = "forecast_accuracy_rolling.parquet"
    METADATA_FILE = "metadata.json"

    BACKTEST_COLUMNS = [
        "as_of_date",
        "target_date",
        "horizon_day",
        "model",
        "model_version",
        "forecast",
        "lower",
        "upper",
        "actual",
    ]
    PREDICTION_COLUMNS = [
        "run_id",
        "run_timestamp",
        "as_of_date",
        "target_date",
        "horizon_day",
        "model",
        "model_version",
        "stage",
        "forecast",
        "lower",
        "upper",
    ]
    ACTUAL_COLUMNS = [
        "run_id",
        "as_of_date",
        "target_date",
        "horizon_day",
        "horizon_bucket",
        "model",
        "model_version",
        "stage",
        "forecast",
        "lower",
        "upper",
        "actual",
        "error",
        "filled_at",
    ]
    SORT_KEYS = ["model", "as_of_date", "horizon_day"]

    # A bar loaded on its own trading day may still be trading, so it waits for the next refresh.
    SETTLED_PRICES = "SELECT date, high FROM prices WHERE date < date(ingested_at) ORDER BY date"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.database_path = Path(self.settings.natgas_database_path)
        self.backtest_path = Path(self.settings.natgas_backtest_path)
        self.folder = Path(self.settings.natgas_cache_folder)

    def missing_sources(self) -> list[Path]:
        """Source files that are not there. The parquet export is optional when the database has the table."""
        return [] if self.database_path.exists() else [self.database_path]

    def build(self) -> dict:
        """Write every snapshot file and return the metadata. Raises FileNotFoundError without a source."""
        missing = self.missing_sources()
        if missing:
            raise FileNotFoundError(f"Forecast source not found: {', '.join(str(path) for path in missing)}")

        with self.connect() as connection:
            backtest = self.read_backtest(connection)
            prices = self.read_query(connection, self.SETTLED_PRICES)
            predictions = self.read_table(connection, "predictions", self.PREDICTION_COLUMNS)
            actuals = self.read_table(connection, "forecast_actuals", self.ACTUAL_COLUMNS)
            accuracy = self.read_query(connection, "SELECT * FROM forecast_accuracy")
            rolling = self.read_query(connection, "SELECT * FROM forecast_accuracy_rolling")

        predictions = predictions.sort_values(["run_timestamp", "stage", "horizon_day"]).reset_index(drop=True)
        actuals = actuals.sort_values(["as_of_date", "stage", "horizon_day"]).reset_index(drop=True)
        metadata = self.build_metadata(backtest, prices, predictions, actuals)

        self.folder.mkdir(parents=True, exist_ok=True)
        tables = {
            self.BACKTEST_FILE: backtest,
            self.PRICES_FILE: prices,
            self.PREDICTIONS_FILE: predictions,
            self.ACTUALS_FILE: actuals,
            self.ACCURACY_FILE: accuracy,
            self.ROLLING_FILE: rolling,
        }
        for file_name, table in tables.items():
            table.to_parquet(self.folder / file_name, index=False)
        (self.folder / self.METADATA_FILE).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata

    def connect(self) -> sqlite3.Connection:
        """Open the database read only, so the snapshot can never change the source."""
        return sqlite3.connect(f"file:{self.database_path.resolve()}?mode=ro", uri=True)

    @staticmethod
    def read_query(connection: sqlite3.Connection, query: str) -> pd.DataFrame:
        return pd.read_sql_query(query, connection)

    def read_table(self, connection: sqlite3.Connection, table: str, columns: list[str]) -> pd.DataFrame:
        return self.read_query(connection, f"SELECT {', '.join(columns)} FROM {table}")

    def read_backtest(self, connection: sqlite3.Connection) -> pd.DataFrame:
        """Prefer the parquet export and check it against the database table when both exist."""
        table = self.read_table(connection, "backtest_forecasts", self.BACKTEST_COLUMNS)
        table = table.sort_values(self.SORT_KEYS).reset_index(drop=True)
        if not self.backtest_path.exists():
            return table
        export = pd.read_parquet(self.backtest_path, columns=self.BACKTEST_COLUMNS)
        export["as_of_date"] = export["as_of_date"].astype(str)
        export["target_date"] = export["target_date"].astype(str)
        export["model_version"] = export["model_version"].astype(str)
        export = export.sort_values(self.SORT_KEYS).reset_index(drop=True)
        if len(table) and len(export) != len(table):
            raise ValueError(f"Backtest export has {len(export)} rows but the database table has {len(table)}.")
        return export

    def build_metadata(
        self, backtest: pd.DataFrame, prices: pd.DataFrame, predictions: pd.DataFrame, actuals: pd.DataFrame
    ) -> dict:
        latest = predictions.iloc[-1] if len(predictions) else None
        return {
            "built_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "source": self.settings.natgas_source_folder.name,
            "backtest_rows": int(len(backtest)),
            "backtest_models": sorted(backtest["model"].unique().tolist()),
            "backtest_as_of_dates": int(backtest["as_of_date"].nunique()),
            "first_as_of_date": str(backtest["as_of_date"].min()) if len(backtest) else None,
            "last_as_of_date": str(backtest["as_of_date"].max()) if len(backtest) else None,
            "first_price_date": str(prices["date"].min()) if len(prices) else None,
            "last_price_date": str(prices["date"].max()) if len(prices) else None,
            "prediction_rows": int(len(predictions)),
            "prediction_runs": int(predictions["run_id"].nunique()),
            "latest_run_id": None if latest is None else str(latest["run_id"]),
            "latest_run_as_of_date": None if latest is None else str(latest["as_of_date"]),
            "latest_run_timestamp_utc": None if latest is None else str(latest["run_timestamp"]),
            "actual_rows": int(len(actuals)),
        }
