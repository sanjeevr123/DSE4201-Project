"""
Exploratory step 15: the ladder on the long-history stock/bond sample (VFINX / VUSTX, 50/50, forecasts 1992-2019),
as the pre-declared replication of the margin-effect test on an independent pre-ETF period
(docs/decisions_log.md, "Replication on the 1992-2009 fund sample"). Data through 2019-12-31 only.

Run: OMP_NUM_THREADS=1 .venv/bin/python scripts/explore_15_longhistory_ladder.py
Output: output/explore/ladder/L1_longhist.pkl (static ladder 'S', default layer 2 'L2', zero-mean layer 2 'L2Z').
"""
from __future__ import annotations

import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.explore import EXPLORE_END  # noqa: E402
from src.explore_ladder import run_static_ladder  # noqa: E402
from src.explore_routes import run_rs_corr  # noqa: E402
from explore_05_backtests import ALPHAS, REFIT, WINDOW, build_providers  # noqa: E402

FIRST_FORECAST = "1992-01-01"


def main():
    t0 = time.time()
    px = pd.read_csv(ROOT / "output" / "explore" / "longhistory_prices.csv", index_col=0, parse_dates=True)
    assert px.index.max() <= EXPLORE_END
    r = px[["VFINX", "VUSTX"]].pct_change().dropna()
    R, w = r.values, np.array([0.5, 0.5])
    start = max(int(np.searchsorted(r.index, pd.Timestamp(FIRST_FORECAST))), WINDOW)
    mk = lambda: build_providers(R[:, 0], R[:, 1], np.full(len(R), np.nan), ["HMM_SPY2"])["HMM_SPY2"]
    cut = lambda d: {a: {m: v[start:] for m, v in d[a].items()} for a in d}
    out = {"universe": "L1_longhist", "assets": ["VFINX", "VUSTX"], "dates": r.index[start:], "y": (R @ w)[start:]}
    s = run_static_ladder(R, w, mk(), ALPHAS, start, window=WINDOW, refit=REFIT)
    out["S"] = {"V": cut(s["V"]), "E": cut(s["E"]), "stress": s["stress_prob"][start:], "nu": s["nu"]}
    print(f"static ladder done ({time.time() - t0:.0f}s)", flush=True)
    for key, zm in (("L2", False), ("L2Z", True)):
        r2 = run_rs_corr(R, w, mk(), ALPHAS, start, window=WINDOW, refit=REFIT, zero_mean=zm)
        out[key] = {"V": cut(r2["V"]), "E": cut(r2["E"]), "nu": r2["nu"]}
        print(f"layer 2 {key} done ({time.time() - t0:.0f}s)", flush=True)
    out["runtime_s"] = time.time() - t0
    with open(ROOT / "output" / "explore" / "ladder" / "L1_longhist.pkl", "wb") as f:
        pickle.dump(out, f)
    print(f"L1_longhist: {out['runtime_s']:.0f}s, {len(out['y'])} forecast days "
          f"({out['dates'][0].date()}..{out['dates'][-1].date()})")


if __name__ == "__main__":
    main()
