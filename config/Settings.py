"""Paths and defaults for the portfolio app."""

import os
from dataclasses import dataclass, field
from pathlib import Path

REPOSITORY_FOLDER = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    """Every setting the app needs, with defaults that work on a fresh clone.

    HEADLINE_RADAR_PATH points at a Headline Radar checkout. By default the app
    looks for a sibling folder named headline-radar next to this repository.
    CHATBOT_API_URL is the rag-chatbot service behind the Ask page, and
    CHATBOT_API_KEY its optional key. The key only ever comes from the environment.
    NATGAS_FORECASTING_PATH points at a natural-gas-forecasting checkout, read
    only by build_forecast_cache.py. NATGAS_CACHE is where its snapshot lives.
    """

    headline_radar_folder: Path = field(
        default_factory=lambda: Path(os.environ.get("HEADLINE_RADAR_PATH", REPOSITORY_FOLDER.parent / "headline-radar"))
    )
    cache_folder: Path = field(
        default_factory=lambda: Path(os.environ.get("TOPIC_EXPLORER_CACHE", REPOSITORY_FOLDER / "cache"))
    )
    natgas_source_folder: Path = field(
        default_factory=lambda: Path(
            os.environ.get("NATGAS_FORECASTING_PATH", REPOSITORY_FOLDER.parent / "natural-gas-forecasting")
        )
    )
    natgas_cache_folder: Path = field(
        default_factory=lambda: Path(os.environ.get("NATGAS_CACHE", REPOSITORY_FOLDER / "cache" / "natgas"))
    )
    host: str = field(default_factory=lambda: os.environ.get("HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8050")))
    chatbot_api_url: str = field(default_factory=lambda: os.environ.get("CHATBOT_API_URL", "http://127.0.0.1:8070"))
    chatbot_api_key: str = field(default_factory=lambda: os.environ.get("CHATBOT_API_KEY", ""), repr=False)
    chatbot_timeout_seconds: float = field(default_factory=lambda: float(os.environ.get("CHATBOT_TIMEOUT", "45")))
    default_branches: int = 6
    branch_choices: tuple[int, ...] = (4, 6, 8, 10, 12)
    random_state: int = 42

    @property
    def document_topics_path(self) -> Path:
        return self.headline_radar_folder / "outputs" / "document_topics.csv"

    @property
    def topic_info_path(self) -> Path:
        return self.headline_radar_folder / "outputs" / "topic_info.csv"

    @property
    def fit_diagnostics_path(self) -> Path:
        return self.headline_radar_folder / "outputs" / "fit_diagnostics.csv"

    @property
    def model_path(self) -> Path:
        return self.headline_radar_folder / "data" / "topic_model" / "topic_model.joblib"

    @property
    def database_path(self) -> Path:
        return self.headline_radar_folder / "data" / "headline_radar.db"

    @property
    def natgas_database_path(self) -> Path:
        return self.natgas_source_folder / "data" / "natgas.db"

    @property
    def natgas_backtest_path(self) -> Path:
        return self.natgas_source_folder / "outputs" / "backtest_forecasts.parquet"
