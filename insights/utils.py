import json
import os
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "config.json"


@lru_cache(maxsize=1)
def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def invalidate_config_cache():
    load_config.cache_clear()
