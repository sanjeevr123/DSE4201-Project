"""One-command entry point for the pilot pipeline: `python -m src.run_pilot`.

Currently runs the WP0 data-acquisition + audit step. Later work packages
(WP1 correctness tests are run via `pytest tests/`, not this entry point;
WP2/WP3/WP4/WP5) will extend this orchestrator as they are implemented.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    runpy.run_path(
        str(REPO_ROOT / "scripts" / "00_download_wp0_pilot_data.py"),
        run_name="__main__",
    )


if __name__ == "__main__":
    main()
