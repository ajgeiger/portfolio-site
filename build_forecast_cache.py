"""Snapshot the natural gas forecast outputs into cache/natgas for the website.

Usage:
    python build_forecast_cache.py

Reads natural-gas-forecasting next to this repository (or NATGAS_FORECASTING_PATH)
read only, and writes small parquet files to cache/natgas (or NATGAS_CACHE).
Run it again after each scoring run to pick up new predictions and actuals.
When the source is not there the existing snapshot is left as it is.
"""

import json
import sys

from config.Settings import Settings
from data.forecast.ForecastSnapshotBuilder import ForecastSnapshotBuilder

if __name__ == "__main__":
    settings = Settings()
    builder = ForecastSnapshotBuilder(settings)
    print(f"Reading forecast outputs from {settings.natgas_source_folder}")
    try:
        metadata = builder.build()
    except FileNotFoundError as error:
        print(f"{error}. The current snapshot in {settings.natgas_cache_folder} was left unchanged.")
        sys.exit(0)
    print(json.dumps(metadata, indent=2))
    print(f"Snapshot written to {settings.natgas_cache_folder}")
