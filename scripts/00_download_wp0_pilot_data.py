"""
WP0 step: acquire and archive the pilot's SPY/IEF/GLD raw price data.

Downloads once, from 2004-11-18 (per docs/PILOT_PROMPT.md's data rules) to
today, saves an immutable raw snapshot to data/raw/ with the download date
in the filename, records a SHA-256 hash in data/raw/MANIFEST.txt, and runs
the WP0 data audit (missing dates, zero/duplicate prices, 8-sigma returns,
dividend days, IEF spot-check).

If a snapshot for this start date is already recorded in the manifest, the
download is skipped entirely — raw data is downloaded once and the archived
file is always read thereafter.

This is a DIFFERENT dataset from data/raw/pilot_etf_yahoo_2010_2025.csv
(produced by scripts/01_download_raw_data.py for the earlier, separate
2010-2025 Day-1 EDA pipeline) — different date range, different filename,
does not touch or replace that file.

Run with:
    .venv/bin/python scripts/00_download_wp0_pilot_data.py
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import yfinance

from src.audit import audit_raw_prices, audit_report_to_markdown
from src.config import get_config
from src.data import (
    METADATA_DIR,
    append_manifest_entry,
    compute_sha256,
    download_raw_pilot_data,
    flatten_raw_columns,
    raw_snapshot_exists_for_range,
    save_raw_snapshot,
)


def main() -> None:
    cfg = get_config()
    tickers = cfg["data"]["tickers"]
    start = cfg["data"]["download_start"]
    end = date.today().isoformat()

    existing = raw_snapshot_exists_for_range(start)
    if existing is not None:
        print(f"Archived snapshot already exists for start={start}: "
              f"data/raw/{existing} — skipping download, per data-rules "
              f"'never re-download; always read the archived file'.")
        return

    print(f"Downloading {tickers} from Yahoo Finance via yfinance "
          f"{yfinance.__version__} ({start} to {end}) ...")
    raw_df = download_raw_pilot_data(tickers=tickers, start=start, end=end, interval="1d")
    flat_df = flatten_raw_columns(raw_df)

    download_date = date.today().isoformat()
    filename = f"spy_ief_gld_raw_{download_date}.csv"
    raw_path = save_raw_snapshot(flat_df, filename)
    print(f"Saved raw snapshot: {raw_path} ({flat_df.shape[0]} rows, "
          f"{flat_df.shape[1]} columns)")

    sha256 = compute_sha256(raw_path)
    actual_start = str(flat_df.index.min().date())
    actual_end = str(flat_df.index.max().date())
    append_manifest_entry(
        filename=filename,
        sha256=sha256,
        download_date=download_date,
        tickers=tickers,
        start=start,
        end=actual_end,
        n_rows=flat_df.shape[0],
    )
    print(f"Recorded manifest entry (sha256={sha256[:12]}...) in "
          f"data/raw/MANIFEST.txt")

    report = audit_raw_prices(
        flat_df,
        tickers=tickers,
        start=actual_start,
        end=actual_end,
        sigma_threshold=cfg["audit"]["sigma_threshold"],
        dividend_tol=cfg["audit"]["dividend_diff_tol"],
        ief_spot_check_n=cfg["audit"]["ief_spot_check_n"],
    )
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    audit_json_path = METADATA_DIR / "wp0_data_audit_report.json"
    audit_md_path = METADATA_DIR / "wp0_data_audit_report.md"
    with open(audit_json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    audit_md_path.write_text(audit_report_to_markdown(report))
    print(f"Saved data audit report: {audit_json_path}, {audit_md_path}")

    metadata = {
        "source_name": "Yahoo Finance",
        "access_method": "yfinance.download()",
        "package_version": yfinance.__version__,
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tickers": tickers,
        "requested_start_date": start,
        "requested_end_date": end,
        "actual_first_date": actual_start,
        "actual_last_date": actual_end,
        "raw_file": filename,
        "sha256": sha256,
        "auto_adjust_setting": False,
    }
    metadata_path = METADATA_DIR / "wp0_download_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"Saved download metadata: {metadata_path}")


if __name__ == "__main__":
    main()
