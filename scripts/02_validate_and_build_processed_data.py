"""
Step 2 of the pilot pipeline: validate the raw snapshot and build
processed data (adjusted prices, simple returns, log returns, equal-
weight portfolio returns).

Reads ONLY the preserved raw snapshot in data/raw/ — no re-download.

Run with:
    .venv/bin/python scripts/02_validate_and_build_processed_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from src.data import (
    METADATA_DIR,
    PROCESSED_DATA_DIR,
    build_adjusted_price_panel,
    load_raw_snapshot,
    validate_raw_prices,
)
from src.returns import (
    calculate_equal_weight_portfolio_returns,
    calculate_log_returns,
    calculate_simple_returns,
)

TICKERS = ["SPY", "IEF", "GLD"]
RAW_FILENAME = "pilot_etf_yahoo_2010_2025.csv"
VALIDATION_REPORT_FILENAME = "pilot_etf_yahoo_2010_2025_validation_report.json"


def main() -> None:
    raw_df = load_raw_snapshot(RAW_FILENAME)
    print(f"Loaded raw snapshot: {raw_df.shape[0]} rows, {raw_df.shape[1]} columns")

    # --- Section 11: validate raw data before calculating returns -----
    report = validate_raw_prices(raw_df, TICKERS, price_field="Adj Close")
    print("\n=== Raw data validation report ===")
    print(json.dumps(report, indent=2))

    validation_path = METADATA_DIR / VALIDATION_REPORT_FILENAME
    with open(validation_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nSaved validation report: {validation_path}")

    # Explicit, non-silent integrity assertions. If any of these fail,
    # STOP rather than silently proceeding with compromised data.
    for ticker in TICKERS:
        t = report["per_ticker"][ticker]
        assert t["n_nonpositive_prices"] == 0, (
            f"{ticker} has non-positive Adj Close prices — stopping."
        )
    assert report["n_duplicate_dates"] == 0, "Duplicate dates found — stopping."
    assert report["is_index_monotonic_increasing"], "Dates not sorted — stopping."

    # --- Section 12: adjusted-price dataset ----------------------------
    adj_prices = build_adjusted_price_panel(raw_df, TICKERS)

    n_missing_per_ticker = adj_prices.isna().sum()
    print("\nMissing Adj Close values per ticker (raw, unaligned):")
    print(n_missing_per_ticker)

    # Document the common-date decision explicitly rather than silently
    # inner-joining. Since validation above showed zero missing values
    # and zero duplicate dates for all three tickers, the three series
    # already share an identical date index (same underlying SPY/IEF/GLD
    # NYSE-Arca trading calendar) — no dates are lost by using the panel
    # as-is for the equal-weight portfolio return.
    dates_before = set(adj_prices.index)
    common_dates = adj_prices.dropna(how="any").index
    dates_lost = dates_before - set(common_dates)
    print(f"\nDates that would be lost if requiring all three tickers "
          f"non-missing: {len(dates_lost)}")
    if len(dates_lost) > 0:
        print("NOTE: dates with at least one missing ticker value:")
        print(sorted(dates_lost))

    adj_prices_path = PROCESSED_DATA_DIR / "pilot_adjusted_prices.csv"
    adj_prices.to_csv(adj_prices_path, index=True, index_label="Date")
    print(f"\nSaved adjusted-price panel: {adj_prices_path} "
          f"({adj_prices.shape[0]} rows)")

    # --- Section 13-14: simple and log returns --------------------------
    simple_returns = calculate_simple_returns(adj_prices)
    log_returns = calculate_log_returns(adj_prices)

    simple_returns_path = PROCESSED_DATA_DIR / "pilot_simple_returns.csv"
    log_returns_path = PROCESSED_DATA_DIR / "pilot_log_returns.csv"
    simple_returns.to_csv(simple_returns_path, index=True, index_label="Date")
    log_returns.to_csv(log_returns_path, index=True, index_label="Date")
    print(f"Saved simple returns: {simple_returns_path}")
    print(f"Saved log returns: {log_returns_path}")

    # --- Section 16: equal-weight portfolio (simple) return -------------
    portfolio_returns = calculate_equal_weight_portfolio_returns(
        simple_returns, assets=TICKERS
    )
    portfolio_returns_path = PROCESSED_DATA_DIR / "pilot_portfolio_returns.csv"
    portfolio_returns.to_csv(
        portfolio_returns_path, index=True, index_label="Date", header=["portfolio_return"]
    )
    print(f"Saved equal-weight portfolio returns: {portfolio_returns_path}")

    print(f"\nFirst return date (NaN row from shift, expected): "
          f"{simple_returns.index[0].date()}")
    print(f"Simple returns non-NaN rows: {simple_returns.dropna().shape[0]}")


if __name__ == "__main__":
    main()
