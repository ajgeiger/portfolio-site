import hashlib
import json

import pandas as pd
import pytest

from config.Settings import Settings
from data.forecast.ForecastCache import ForecastCache
from data.forecast.ForecastSnapshotBuilder import ForecastSnapshotBuilder
from tests.forecast_tables import write_source


def settings_for(tmp_path, source) -> Settings:
    return Settings(natgas_source_folder=source, natgas_cache_folder=tmp_path / "cache" / "natgas")


def digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_snapshot_writes_every_file_and_metadata(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting")
    settings = settings_for(tmp_path, source)
    metadata = ForecastSnapshotBuilder(settings).build()

    folder = settings.natgas_cache_folder
    for name in ("backtest_forecasts", "prices", "predictions", "forecast_actuals", "forecast_accuracy"):
        assert (folder / f"{name}.parquet").exists()
    saved = json.loads((folder / "metadata.json").read_text())
    assert saved["backtest_rows"] == metadata["backtest_rows"] == 72
    assert metadata["backtest_as_of_dates"] == 3
    assert metadata["backtest_models"] == ["chronos", "gradient_boosting", "greykite", "naive"]
    assert metadata["latest_run_id"] == "run1"
    assert metadata["latest_run_as_of_date"] == "2024-03-15"
    assert metadata["actual_rows"] == 0
    assert "chronos:champion" in metadata["prediction_stages"]
    assert "legacy:champion" in metadata["prediction_stages"]
    assert metadata["tournament_as_of_date"] == "2024-03-15"
    assert metadata["event_rows"] == 3
    assert metadata["promotion_rows"] == 0


def test_snapshot_exports_the_tournament_tables(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting")
    settings = settings_for(tmp_path, source)
    ForecastSnapshotBuilder(settings).build()
    cache = ForecastCache(settings)
    assert len(cache.standings()) == 20
    assert cache.events()["first_day"].tolist() == [1, 6, 16]
    assert cache.trials()["family"].tolist() == ["chronos", "gradient_boosting", "greykite"]
    assert pd.api.types.is_datetime64_any_dtype(cache.trials()["trial_started"])
    assert cache.promotions().empty
    assert list(cache.promotions().columns) == ForecastSnapshotBuilder.PROMOTION_COLUMNS


def test_snapshot_works_with_a_database_from_before_the_tournament(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting", tournament=False)
    settings = settings_for(tmp_path, source)
    metadata = ForecastSnapshotBuilder(settings).build()
    cache = ForecastCache(settings)
    assert metadata["tournament_as_of_date"] is None
    assert cache.standings().empty and cache.events().empty and cache.trials().empty
    assert list(cache.events().columns) == ForecastSnapshotBuilder.EVENT_COLUMNS


def test_snapshot_never_changes_the_source(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting")
    database = source / "data" / "natgas.db"
    before = digest(database)
    ForecastSnapshotBuilder(settings_for(tmp_path, source)).build()
    assert digest(database) == before


def test_snapshot_skips_a_bar_loaded_on_its_own_trading_day(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting")
    settings = settings_for(tmp_path, source)
    ForecastSnapshotBuilder(settings).build()
    prices = ForecastCache(settings).prices()
    assert prices["date"].max() == pd.Timestamp("2024-03-15")
    assert 9.99 not in prices["high"].tolist()


def test_snapshot_fails_cleanly_without_a_source(tmp_path):
    settings = settings_for(tmp_path, tmp_path / "missing")
    builder = ForecastSnapshotBuilder(settings)
    assert builder.missing_sources()
    with pytest.raises(FileNotFoundError):
        builder.build()
    assert not settings.natgas_cache_folder.exists()


def test_snapshot_rejects_an_export_that_disagrees_with_the_database(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting")
    export = source / "outputs" / "backtest_forecasts.parquet"
    pd.read_parquet(export).head(10).to_parquet(export, index=False)
    with pytest.raises(ValueError, match="rows"):
        ForecastSnapshotBuilder(settings_for(tmp_path, source)).build()


def test_snapshot_reads_the_table_when_the_export_is_missing(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting")
    (source / "outputs" / "backtest_forecasts.parquet").unlink()
    metadata = ForecastSnapshotBuilder(settings_for(tmp_path, source)).build()
    assert metadata["backtest_rows"] == 72


def test_cache_reads_dates_and_keeps_matured_actuals(tmp_path):
    source = write_source(tmp_path / "natural-gas-forecasting", actuals=True)
    settings = settings_for(tmp_path, source)
    ForecastSnapshotBuilder(settings).build()
    cache = ForecastCache(settings)
    assert cache.available
    assert pd.api.types.is_datetime64_any_dtype(cache.backtest()["as_of_date"])
    assert str(cache.predictions()["run_timestamp"].dt.tz) == "UTC"
    assert len(cache.actuals()) == 4
    assert set(cache.accuracy()["stage"]) == {"production", "baseline:naive"}


def test_cache_without_a_snapshot_gives_empty_tables(tmp_path):
    cache = ForecastCache(folder=tmp_path / "nothing")
    assert not cache.available
    assert cache.backtest().empty
    assert list(cache.predictions().columns) == ForecastSnapshotBuilder.PREDICTION_COLUMNS
    assert cache.metadata() == {}
    assert cache.standings().empty and cache.trials().empty
