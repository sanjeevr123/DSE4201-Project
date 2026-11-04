"""
Check of the two Yahoo downloads against each other (docs/THESIS_PLAN.md 1.4, 2.E): the file the hold-out run uses
(data/raw/spy_ief_gld_raw_2026-09-26.csv) and the exploration download (data/raw/explore_etfs_2004_2019.csv). Daily simple returns
of SPY, IEF and GLD from adjusted closes, compared through 2019-12-31 only. Both are the same vendor (Yahoo Finance via yfinance), so
this is a consistency check between two pulls, not a second source. The raw file is truncated at 2019-12-31 before any return is
computed.

  .venv/bin/python scripts/confirm_03_vendor_check.py
Output: output/confirm/vendor_check.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from confirm_00_run import OUT, TICKERS, load, sha256_file  # noqa: E402

EXPLORE = ROOT / "data" / "raw" / "explore_etfs_2004_2019.csv"
RAW = ROOT / "data" / "raw" / "spy_ief_gld_raw_2026-09-26.csv"


def main():
    a = load("2019-12-31")                                              # hold-out file, truncated before computing
    px = pd.read_csv(EXPLORE, index_col=0, parse_dates=True)[TICKERS].loc[:"2019-12-31"].dropna()
    b = px.pct_change().dropna()
    same_dates = a.index.equals(b.index)
    common = a.index.intersection(b.index)
    d = (a.loc[common] - b.loc[common]).abs()
    out = {"files": {"hold-out source": RAW.name, "exploration": EXPLORE.name},
           "sha256": {RAW.name: sha256_file(RAW), EXPLORE.name: sha256_file(EXPLORE)},
           "n_dates_holdout_source": len(a), "n_dates_exploration": len(b), "same_dates": bool(same_dates),
           "n_common": len(common), "first": str(common[0].date()), "last": str(common[-1].date()),
           "max_abs_return_diff": {t: float(d[t].max()) for t in TICKERS}, "max_abs_return_diff_all": float(d.values.max()),
           "median_abs_return_diff_all": float(np.median(d.values)),
           "portfolio_max_abs_diff": float((a.loc[common].mean(axis=1) - b.loc[common].mean(axis=1)).abs().max()),
           "note": "same vendor (Yahoo Finance via yfinance); two pulls, not a second source"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "vendor_check.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
