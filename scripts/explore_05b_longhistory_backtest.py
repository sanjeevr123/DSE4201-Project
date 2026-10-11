"""
Exploratory step 5b (direction A): walk-forward VaR/ES backtest on the long-history
stock/bond sample (VFINX / VUSTX, 50/50, forecasts from 1992), which -- unlike the
2010-2019 ETF sample -- contains a positive stock-bond correlation regime
(1988-1999). Data through 2019-12-31 only.

VFINX/VUSTX are mutual funds used as proxies (once-a-day pricing, VUSTX = long
Treasuries); no VIX before 1990, so VIX-based signals are omitted.

Run: .venv/bin/python scripts/explore_05b_longhistory_backtest.py
Output: output/explore/backtests/L1_longhist.pkl (same layout as explore_05 outputs).
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
from src.explore import EXPLORE_END, load_rates  # noqa: E402
from src.explore_wf import run_benchmarks, run_regime_models  # noqa: E402
from explore_05_backtests import ALPHAS, OUT, REFIT, WINDOW, build_providers  # noqa: E402

FIRST_FORECAST = "1992-01-01"
PROVIDERS = ["HMM_SPY2", "HMM_SPY3", "RULE_RV75", "RULE_CORR", "HMM_SPYIEF2",
             "RULE_IEFRV75", "RULE_YLDVOL75"]


def main() -> None:
    t_start = time.time()
    px = pd.read_csv(ROOT / "output" / "explore" / "longhistory_prices.csv",
                     index_col=0, parse_dates=True)
    assert px.index.max() <= EXPLORE_END
    r = px[["VFINX", "VUSTX"]].pct_change().dropna()
    tnx = load_rates()["^TNX"].reindex(r.index).ffill().values
    R = r.values
    w = np.array([0.5, 0.5])
    spy, ief = R[:, 0], R[:, 1]          # stock / bond proxies in the roles of SPY / IEF
    start = max(int(np.searchsorted(r.index, pd.Timestamp(FIRST_FORECAST))), WINDOW)

    bench = run_benchmarks(R, w, ALPHAS, start, window=WINDOW, refit=REFIT, dcc=True)
    models = {"V": {a: dict(bench["V"][a]) for a in ALPHAS}, "E": {a: dict(bench["E"][a]) for a in ALPHAS}}
    stress, diag = {}, {}
    vix_stub = np.full(len(R), np.nan)
    for pname, prov in build_providers(spy, ief, vix_stub, PROVIDERS, tnx, None).items():
        rr = run_regime_models(R, w, prov, ALPHAS, start, window=WINDOW, refit=REFIT)
        for a in ALPHAS:
            for m in ("A", "B", "C", "D"):
                key = "A" if m == "A" else f"{pname}/{m}"
                models["V"][a][key], models["E"][a][key] = rr["V"][a][m], rr["E"][a][m]
        stress[pname] = rr["stress_prob"]
        diag[pname] = {"n_degenerate_refits": getattr(prov, "n_degenerate", 0)}
        print(f"  [L1] {pname} done ({time.time() - t_start:.0f}s)", flush=True)
    idx = np.arange(start, len(R))
    res = {"universe": "L1_longhist", "assets": ["VFINX", "VUSTX"], "dates": r.index[idx], "y": (R @ w)[idx],
           "V": {a: {m: v[idx] for m, v in models["V"][a].items()} for a in ALPHAS},
           "E": {a: {m: v[idx] for m, v in models["E"][a].items()} for a in ALPHAS},
           "stress": {k: v[idx] for k, v in stress.items()}, "diag": diag,
           "window": WINDOW, "runtime_s": time.time() - t_start}
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "L1_longhist.pkl", "wb") as f:
        pickle.dump(res, f)
    print(f"L1_longhist: {res['runtime_s']:.0f}s, {len(res['y'])} forecast days "
          f"({res['dates'][0].date()}..{res['dates'][-1].date()})")


if __name__ == "__main__":
    main()
