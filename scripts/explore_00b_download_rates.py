"""
Exploratory phase: download 10y yield (^TNX) and the MOVE index for bond-aware
regime signals (direction B), capped at 2019-12-31. ^TNX goes back to 1986 and
is also used for the long-history sample (direction A). Raw snapshot is written
once and not overwritten.

Run: .venv/bin/python scripts/explore_00b_download_rates.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "explore_rates_1986_2019.csv"
TICKERS = ["^TNX", "^MOVE"]


def main() -> None:
    if OUT.exists():
        print(f"{OUT.name} already exists; raw snapshots are never re-pulled.")
        return
    raw = yf.download(TICKERS, start="1986-01-01", end="2020-01-01", auto_adjust=False,
                      progress=False)["Close"]
    assert raw.index.max() <= pd.Timestamp("2019-12-31")
    raw.to_csv(OUT)
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    with open(ROOT / "data" / "raw" / "MANIFEST.txt", "a") as f:
        f.write(f"{OUT.name}  sha256={sha}  tickers={','.join(TICKERS)}  "
                f"range={raw.index.min().date()}..{raw.index.max().date()}\n")
    print(raw.apply(lambda c: (str(c.first_valid_index().date()), int(c.notna().sum()))))


if __name__ == "__main__":
    main()
