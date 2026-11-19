"""Build the cache tables from the Headline Radar outputs.

Usage:
    python build_cache.py

Set HEADLINE_RADAR_PATH if the Headline Radar folder is not next to this repository.
"""

import json

from config.Settings import Settings
from data.CacheBuilder import CacheBuilder

if __name__ == "__main__":
    settings = Settings()
    print(f"Reading fitted outputs from {settings.headline_radar_folder}")
    metadata = CacheBuilder(settings).build()
    print(json.dumps(metadata, indent=2))
    print(f"Cache written to {settings.cache_folder}")
