"""
Data audit report for the pilot's raw SPY/IEF/GLD price archive.

Checks required by the pilot spec (docs/PILOT_PROMPT.md, "DATA RULES"):
  * missing dates, zero or duplicate prices;
  * returns beyond 8 standard deviations;
  * dividend days (where adjusted and raw returns differ) per ticker;
  * a spot-check of 3 IEF dividend dates against the raw data.

This module only inspects and reports — it never drops, fills, or otherwise
alters the raw data.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def missing_dates(df: pd.DataFrame, start: str, end: str) -> dict:
    """Business days in [start, end] that are absent from df's index.

    Uses a plain business-day calendar (not a market-holiday calendar), so
    this over-counts genuine market holidays as "missing" — flagged as a
    known conservative simplification rather than silently assuming a
    specific holiday calendar is correct.
    """
    expected = pd.bdate_range(start, end)
    observed = pd.DatetimeIndex(df.index)
    missing = expected.difference(observed)
    return {
        "n_expected_business_days": int(len(expected)),
        "n_observed_days": int(len(observed)),
        "n_missing_business_days": int(len(missing)),
        "missing_dates_sample": [str(d.date()) for d in missing[:20]],
    }


def zero_or_duplicate_prices(df: pd.DataFrame, tickers: Iterable[str], price_field: str = "Adj Close") -> dict:
    """Zero/negative prices, duplicate index dates, and duplicate consecutive
    (stale) price values per ticker."""
    report: dict = {"per_ticker": {}, "n_duplicate_dates": int(df.index.duplicated().sum())}
    for ticker in tickers:
        col = f"{price_field}_{ticker}"
        series = df[col].dropna()
        stale_runs = int((series.diff() == 0).sum())
        report["per_ticker"][ticker] = {
            "n_zero_or_negative": int((series <= 0).sum()),
            "n_stale_consecutive_days": stale_runs,
        }
    return report


def outlier_returns(
    df: pd.DataFrame,
    tickers: Iterable[str],
    price_field: str = "Adj Close",
    sigma_threshold: float = 8.0,
) -> dict:
    """Simple daily returns beyond `sigma_threshold` standard deviations,
    per ticker, computed on the data actually passed in (caller is
    responsible for pre-truncating to the locked-period boundary)."""
    report: dict = {"sigma_threshold": sigma_threshold, "per_ticker": {}}
    for ticker in tickers:
        col = f"{price_field}_{ticker}"
        r = df[col].pct_change().dropna()
        mean, std = r.mean(), r.std()
        mask = (r - mean).abs() > sigma_threshold * std
        flagged = r[mask]
        report["per_ticker"][ticker] = {
            "n_flagged": int(mask.sum()),
            "flagged_dates": [
                {"date": str(idx.date()), "return": float(val)}
                for idx, val in flagged.items()
            ],
        }
    return report


def dividend_days(
    df: pd.DataFrame,
    tickers: Iterable[str],
    tol: float = 1e-6,
) -> dict[str, pd.DatetimeIndex]:
    """Dates where the adjusted return diverges from the raw (Close-based)
    return by more than `tol` — i.e. dividend/split adjustment days.

    Reuses the diff-logic pattern from starter/pilot_real_data.py, promoted
    into a named, per-ticker, testable function.
    """
    out: dict[str, pd.DatetimeIndex] = {}
    for ticker in tickers:
        close_ret = df[f"Close_{ticker}"].pct_change()
        adj_ret = df[f"Adj Close_{ticker}"].pct_change()
        diverges = (adj_ret - close_ret).abs() > tol
        out[ticker] = df.index[diverges.fillna(False)]
    return out


def ief_dividend_spot_check(df: pd.DataFrame, n: int = 3) -> list[dict]:
    """The n IEF dividend dates with the largest adjusted-vs-raw return
    divergence, for manual cross-referencing against a public dividend
    history (e.g. Nasdaq/IEF corporate actions). This step is a manual
    verification aid — the code surfaces the candidate dates, but confirming
    them against an external source is done by a human, not automated here.
    """
    close_ret = df["Close_IEF"].pct_change()
    adj_ret = df["Adj Close_IEF"].pct_change()
    diff = (adj_ret - close_ret).dropna()
    top = diff.reindex(diff.abs().sort_values(ascending=False).index).head(n)
    rows = []
    for date, div in top.items():
        rows.append({
            "date": str(date.date()),
            "close": float(df.loc[date, "Close_IEF"]),
            "adj_close": float(df.loc[date, "Adj Close_IEF"]),
            "adjusted_return": float(adj_ret.loc[date]),
            "raw_return": float(close_ret.loc[date]),
            "implied_dividend_effect": float(div),
        })
    return rows


def audit_raw_prices(
    df: pd.DataFrame,
    tickers: Iterable[str],
    start: str,
    end: str,
    sigma_threshold: float = 8.0,
    dividend_tol: float = 1e-6,
    ief_spot_check_n: int = 3,
) -> dict:
    """Run the full WP0 data-audit report and return a single nested dict,
    suitable for json.dump."""
    tickers = list(tickers)
    div_days = dividend_days(df, tickers, tol=dividend_tol)
    return {
        "date_range_audited": {"start": start, "end": end},
        "missing_dates": missing_dates(df, start, end),
        "zero_or_duplicate_prices": zero_or_duplicate_prices(df, tickers),
        "outlier_returns": outlier_returns(df, tickers, sigma_threshold=sigma_threshold),
        "dividend_days_per_ticker": {
            t: {"n_dividend_days": int(len(idx)), "dates": [str(d.date()) for d in idx]}
            for t, idx in div_days.items()
        },
        "ief_dividend_spot_check": (
            ief_dividend_spot_check(df, n=ief_spot_check_n) if "IEF" in tickers else []
        ),
    }


def audit_report_to_markdown(report: dict) -> str:
    """Render the audit report dict as a short human-readable Markdown summary."""
    lines = ["# WP0 Data Audit Report", ""]
    dr = report["date_range_audited"]
    lines.append(f"Audited range: {dr['start']} to {dr['end']}")
    lines.append("")

    md = report["missing_dates"]
    lines.append("## Missing dates")
    lines.append(
        f"- {md['n_missing_business_days']} missing business days out of "
        f"{md['n_expected_business_days']} expected "
        f"({md['n_observed_days']} observed)."
    )
    if md["missing_dates_sample"]:
        lines.append(f"- Sample: {', '.join(md['missing_dates_sample'])}")
    lines.append("")

    zd = report["zero_or_duplicate_prices"]
    lines.append("## Zero / duplicate / stale prices")
    lines.append(f"- {zd['n_duplicate_dates']} duplicate index dates in the panel.")
    for ticker, stats in zd["per_ticker"].items():
        lines.append(
            f"- {ticker}: {stats['n_zero_or_negative']} zero/negative prices, "
            f"{stats['n_stale_consecutive_days']} stale consecutive-day repeats."
        )
    lines.append("")

    orr = report["outlier_returns"]
    lines.append(f"## Returns beyond {orr['sigma_threshold']} standard deviations")
    for ticker, stats in orr["per_ticker"].items():
        lines.append(f"- {ticker}: {stats['n_flagged']} flagged days.")
        for row in stats["flagged_dates"][:10]:
            lines.append(f"  - {row['date']}: {row['return']:+.4f}")
    lines.append("")

    lines.append("## Dividend days per ticker")
    for ticker, stats in report["dividend_days_per_ticker"].items():
        lines.append(f"- {ticker}: {stats['n_dividend_days']} dividend days.")
    lines.append("")

    lines.append("## IEF dividend spot-check (manually verify against a public source)")
    for row in report["ief_dividend_spot_check"]:
        lines.append(
            f"- {row['date']}: close={row['close']:.4f}, adj_close={row['adj_close']:.4f}, "
            f"adjusted_return={row['adjusted_return']:+.4%}, "
            f"raw_return={row['raw_return']:+.4%}, "
            f"implied_dividend_effect={row['implied_dividend_effect']:+.4%}"
        )
    lines.append("")
    return "\n".join(lines)
