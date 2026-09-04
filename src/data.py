"""
Data acquisition, loading, validation, and preprocessing utilities.

Important research rule:
Raw downloaded data must be preserved unchanged.

Cleaning and transformation should produce separate processed files.

Pilot data-source provenance:
- Source: Yahoo Finance, accessed through the `yfinance` Python package.
- `yfinance` is an independent, community-maintained interface to Yahoo
  Finance's public web data. It is NOT an official Yahoo Finance API.
- This is a provisional pilot data source for early-stage learning and
  pipeline development. Final thesis data-source validation (and, if
  necessary, cross-checking against another credible source) is a later
  task and has not been done here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = REPO_ROOT / "data" / "processed"
METADATA_DIR = REPO_ROOT / "data" / "metadata"


def download_raw_pilot_data(
    tickers: Iterable[str],
    start: str,
    end: str,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Download raw historical OHLCV and corporate-action data from Yahoo
    Finance via `yfinance`.

    Inputs:
        tickers: iterable of ticker symbols, e.g. ["SPY", "IEF", "GLD"].
        start: inclusive start date "YYYY-MM-DD".
        end: end date passed to yfinance; note the underlying API may
            treat this as exclusive, so the actual last returned date
            should always be verified rather than assumed.
        interval: sampling frequency; "1d" for daily observations.

    Output:
        Raw DataFrame with MultiIndex columns (field, ticker), containing
        Open/High/Low/Close/Adj Close/Volume plus corporate actions
        (Dividends, Stock Splits, Capital Gains where applicable).

    Assumptions:
        auto_adjust=False is used explicitly so that Close and Adj Close
        remain distinct columns, per the pilot data-acquisition
        specification. actions=True requests dividend/split/capital-gain
        data where available.
    """
    df = yf.download(
        tickers=list(tickers),
        start=start,
        end=end,
        interval=interval,
        auto_adjust=False,
        actions=True,
        progress=False,
        group_by="column",
    )
    if df is None or df.empty:
        raise RuntimeError(
            "yfinance returned no data for the requested tickers/date "
            "range. Stopping rather than silently continuing with an "
            "empty dataset — check network connectivity and ticker "
            "validity before retrying."
        )
    return df


def flatten_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten yfinance's MultiIndex (field, ticker) columns into single
    'Field_Ticker' string columns so the raw snapshot can be stored as an
    unambiguous flat CSV without losing information.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [f"{field}_{ticker}" for field, ticker in df.columns]
    return df


def save_raw_snapshot(df: pd.DataFrame, filename: str) -> Path:
    """Save a flattened raw DataFrame to data/raw/ as an immutable snapshot."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DATA_DIR / filename
    df.to_csv(path, index=True, index_label="Date")
    return path


def load_raw_snapshot(filename: str) -> pd.DataFrame:
    """Load a previously saved raw snapshot from data/raw/ without modification."""
    path = RAW_DATA_DIR / filename
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    return df


def validate_raw_prices(
    df: pd.DataFrame,
    tickers: Iterable[str],
    price_field: str = "Adj Close",
) -> dict:
    """
    Run explicit, non-destructive validation checks on the raw price panel.

    Reports, per ticker: coverage (first/last date, number of
    observations), missingness, and non-positive prices. Also reports
    duplicate dates and whether the index is sorted. Does NOT drop,
    fill, or otherwise alter any data — it only inspects and reports.

    Output: a nested dict report suitable for json.dump into a metadata
    or validation-report file.
    """
    report: dict = {"per_ticker": {}}
    for ticker in tickers:
        col = f"{price_field}_{ticker}"
        series = df[col]
        non_na = series.dropna()
        report["per_ticker"][ticker] = {
            "first_valid_date": str(series.first_valid_index()),
            "last_valid_date": str(series.last_valid_index()),
            "n_rows_in_panel": int(series.shape[0]),
            "n_missing": int(series.isna().sum()),
            "n_nonpositive_prices": int((non_na <= 0).sum()),
        }

    report["n_duplicate_dates"] = int(df.index.duplicated().sum())
    report["is_index_monotonic_increasing"] = bool(df.index.is_monotonic_increasing)
    report["panel_first_date"] = str(df.index.min())
    report["panel_last_date"] = str(df.index.max())
    report["panel_n_rows"] = int(df.shape[0])
    return report


def build_adjusted_price_panel(df: pd.DataFrame, tickers: Iterable[str]) -> pd.DataFrame:
    """
    Extract 'Adj Close' columns for each ticker from the flattened raw
    panel into a tidy Date x Ticker adjusted-price DataFrame.

    Does not drop, align, fill, or otherwise alter any values — any NaNs
    present in the raw Adj Close columns are preserved as-is. Alignment
    to a common-date index (if needed for the portfolio calculation) is
    a separate, explicitly documented step performed by the caller.
    """
    tickers = list(tickers)
    panel = pd.DataFrame({ticker: df[f"Adj Close_{ticker}"] for ticker in tickers})
    panel.index.name = "Date"
    return panel
