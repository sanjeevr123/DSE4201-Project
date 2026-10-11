"""
Exploratory phase: download candidate ETFs + VIX, capped at 2019-12-31.

2020-2025 is the confirmatory hold-out and is deliberately NEVER downloaded
here (see docs/decisions_log.md, "Exploratory vs confirmatory split").
Raw snapshot is written once and not overwritten.

Run: .venv/bin/python scripts/explore_00_download.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "explore_etfs_2004_2019.csv"
TICKERS = ["SPY", "IEF", "TLT", "GLD", "HYG", "LQD", "EEM", "EFA", "VNQ", "DBC",
           "XLU", "XLK", "XLF", "XLE", "^VIX"]
START, END_EXCLUSIVE = "2004-11-18", "2020-01-01"


def main() -> None:
    if OUT.exists():
        print(f"{OUT.name} already exists; raw snapshots are never re-pulled.")
        return
    raw = yf.download(TICKERS, start=START, end=END_EXCLUSIVE, auto_adjust=False,
                      progress=False)
    adj = raw["Adj Close"].copy()
    assert adj.index.max() <= __import__("pandas").Timestamp("2019-12-31")
    adj.to_csv(OUT)
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    with open(ROOT / "data" / "raw" / "MANIFEST.txt", "a") as f:
        f.write(f"{OUT.name}  sha256={sha}  tickers={','.join(TICKERS)}  "
                f"range={adj.index.min().date()}..{adj.index.max().date()}\n")
    print(adj.notna().apply(lambda c: (c.idxmax().date(), c.sum())).T if False else
          adj.apply(lambda c: (str(c.first_valid_index().date()), int(c.notna().sum()))))


if __name__ == "__main__":
    main()
