"""
Step 1 of the pilot pipeline: acquire and preserve raw ETF data.

This script downloads the pilot ETF universe from Yahoo Finance via
`yfinance`, saves an immutable raw snapshot to data/raw/, and writes a
detailed provenance/metadata record to data/metadata/.

This script should be run ONCE to produce the raw snapshot. All later
processing/analysis scripts read the saved snapshot rather than
re-downloading, so the pilot results stay reproducible even if the
live Yahoo Finance data later change.

Run with:
    .venv/bin/python scripts/01_download_raw_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import yfinance

from src.data import (
    METADATA_DIR,
    download_raw_pilot_data,
    flatten_raw_columns,
    save_raw_snapshot,
)

TICKERS = ["SPY", "IEF", "GLD"]
REQUESTED_START = "2010-01-01"
REQUESTED_END = "2026-01-01"  # yfinance end date may be exclusive; verified below
INTERVAL = "1d"

RAW_FILENAME = "pilot_etf_yahoo_2010_2025.csv"
METADATA_FILENAME = "pilot_etf_yahoo_2010_2025_metadata.json"


def main() -> None:
    print(f"Downloading {TICKERS} from Yahoo Finance via yfinance "
          f"{yfinance.__version__} ...")
    retrieval_timestamp = datetime.now(timezone.utc)

    raw_df = download_raw_pilot_data(
        tickers=TICKERS, start=REQUESTED_START, end=REQUESTED_END, interval=INTERVAL
    )
    flat_df = flatten_raw_columns(raw_df)

    raw_path = save_raw_snapshot(flat_df, RAW_FILENAME)
    print(f"Saved raw snapshot: {raw_path} ({flat_df.shape[0]} rows, "
          f"{flat_df.shape[1]} columns)")

    actual_first_date = str(flat_df.index.min().date())
    actual_last_date = str(flat_df.index.max().date())
    n_duplicate_dates = int(flat_df.index.duplicated().sum())

    missing_by_column = {
        col: int(flat_df[col].isna().sum()) for col in flat_df.columns
    }

    metadata = {
        "source_name": "Yahoo Finance",
        "source_url_or_description": (
            "https://finance.yahoo.com/ — public historical market data, "
            "retrieved programmatically via the third-party `yfinance` "
            "Python package (NOT an official Yahoo Finance API)."
        ),
        "retrieval_timestamp": retrieval_timestamp.isoformat(),
        "retrieval_timezone": "UTC",
        "access_method": "yfinance.download()",
        "package": "yfinance",
        "package_version": yfinance.__version__,
        "tickers": TICKERS,
        "requested_start_date": REQUESTED_START,
        "requested_end_date": REQUESTED_END,
        "actual_first_date": actual_first_date,
        "actual_last_date": actual_last_date,
        "frequency": INTERVAL,
        "auto_adjust_setting": False,
        "corporate_actions_setting": True,
        "raw_file_path": str(raw_path.relative_to(REPO_ROOT)),
        "number_of_rows": int(flat_df.shape[0]),
        "number_of_columns": int(flat_df.shape[1]),
        "column_names": list(flat_df.columns),
        "missing_values_by_column": missing_by_column,
        "duplicate_dates": n_duplicate_dates,
        "timezone_information": (
            "Index returned by yfinance for daily US-exchange data is "
            "timezone-naive (calendar trading dates); no intraday "
            "timestamps are involved at the '1d' interval."
        ),
        "notes": (
            "This is a TEMPORARY / PILOT dataset for early-stage learning "
            "and pipeline development. It is not the final thesis "
            "empirical dataset."
        ),
        "known_source_limitations": [
            "Yahoo Finance is used here as a public, convenient pilot "
            "market-data source, not an institutional/official data "
            "vendor.",
            "`yfinance` is an independent, community-maintained interface "
            "to Yahoo Finance's public web data, not an official Yahoo "
            "Finance API; it can break or change behaviour if Yahoo "
            "changes its website/backend.",
            "Adjusted-price and corporate-action fields reflect Yahoo's "
            "own adjustment methodology, which has not been independently "
            "verified against another data provider.",
            "Final research-data source selection and validation against "
            "a second credible source remain a later thesis task.",
        ],
    }

    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = METADATA_DIR / METADATA_FILENAME
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"Saved metadata: {metadata_path}")

    print("\nRequested date range:", REQUESTED_START, "to", REQUESTED_END)
    print("Actual returned range:", actual_first_date, "to", actual_last_date)
    print("Duplicate dates:", n_duplicate_dates)
    print("Any missing values:", any(v > 0 for v in missing_by_column.values()))


if __name__ == "__main__":
    main()
