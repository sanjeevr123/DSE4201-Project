"""
Exploratory step 3: is a POSITIVE stock-bond correlation regime present in the
development sample at all? Uses long-history Vanguard funds as proxies
(VFINX ~ S&P 500, VUSTX ~ long Treasuries, VFITX ~ intermediate Treasuries)
to look back before ETFs existed. Capped at 2019-12-31.

Run: .venv/bin/python scripts/explore_03_longhistory.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

OUT = Path(__file__).resolve().parents[1] / "output" / "explore"
f = OUT / "longhistory_prices.csv"
if not f.exists():
    px = yf.download(["VFINX", "VUSTX", "VFITX"], start="1986-06-01", end="2020-01-01",
                     auto_adjust=False, progress=False)["Adj Close"]
    px.to_csv(f)
px = pd.read_csv(f, index_col=0, parse_dates=True)
assert px.index.max() <= pd.Timestamp("2019-12-31")
print(px.apply(lambda c: str(c.first_valid_index().date())))
r = px.pct_change().dropna(subset=["VFINX", "VUSTX"])
roll = r["VFINX"].rolling(252).corr(r["VUSTX"])
yr = r["VFINX"].groupby(r.index.year).corr(r["VUSTX"])
print(yr.round(2).to_string())
share_pos = {
    "1987-1999": float((roll["1988":"1999"] > 0).mean()),
    "2000-2009": float((roll["2000":"2009"] > 0).mean()),
    "2010-2019": float((roll["2010":"2019"] > 0).mean()),
}
print("share of days with 252d stock-bond corr > 0:", share_pos)
roll.to_csv(OUT / "longhistory_rolling_corr.csv")
(OUT / "longhistory_summary.json").write_text(json.dumps(
    {"yearly_corr": {int(k): float(v) for k, v in yr.items()}, "share_days_pos": share_pos}, indent=2))
