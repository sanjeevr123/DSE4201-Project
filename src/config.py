"""Loader for config/pilot.yaml — the single source of truth for every pilot
parameter and random seed. Downstream code should import get_config() rather
than hard-coding any value that appears in the YAML file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "pilot.yaml"


@lru_cache(maxsize=1)
def get_config(path: Path = CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
