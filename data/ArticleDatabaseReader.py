"""Read articles from the Headline Radar SQLite database without changing it."""

import sqlite3
from pathlib import Path

import pandas as pd


class ArticleDatabaseReader:
    """Read the articles table in read only mode.

    The connection uses a SQLite URI with mode=ro, so the database can never
    be written. When the write ahead log is empty the file is also opened as
    immutable, which stops SQLite from touching the shared memory file.
    """

    COLUMNS = ["id", "title", "description", "url", "source", "source_type", "published_at", "fetched_at"]

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def read_articles(self) -> pd.DataFrame:
        """Return one row per article with the columns in COLUMNS."""
        if not self.database_path.exists():
            raise FileNotFoundError(f"No database at {self.database_path}")
        query = f"SELECT {', '.join(self.COLUMNS)} FROM articles"
        with sqlite3.connect(self.connection_uri(), uri=True) as connection:
            articles = pd.read_sql_query(query, connection)
        if not articles["id"].is_unique:
            raise ValueError("Article ids in the database must be unique.")
        return articles

    def connection_uri(self) -> str:
        """Build the read only SQLite URI for the database file."""
        uri = f"file:{self.database_path.resolve().as_posix()}?mode=ro"
        log_path = self.database_path.with_name(self.database_path.name + "-wal")
        if not log_path.exists() or log_path.stat().st_size == 0:
            uri += "&immutable=1"
        return uri
