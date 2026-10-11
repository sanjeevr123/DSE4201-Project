"""
Exploratory step 5: walk-forward VaR/ES backtests across universes x regime
definitions, with DCC-GARCH benchmarks. Data through 2019-12-31 only.

  .venv/bin/python scripts/explore_05_backtests.py --validate
      reproduce the pilot's baseline (U1, SPY 2-state HMM, 2010-2015) with the
      generalised engine and compare to output/tables/wp3_walk_forward.json
  .venv/bin/python scripts/explore_05_backtests.py [UNIVERSE ...]
      full run (default: all universes), one process per universe

Raw forecasts are saved to output/explore/backtests/<universe>.pkl;
scripts/explore_06_score.py turns them into tables.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.explore import load_explore_returns  # noqa: E402
from src.explore_wf import HMMProvider, RuleProvider, run_benchmarks, run_regime_models  # noqa: E402

OUT = ROOT / "output" / "explore" / "backtests"
ALPHAS = (0.05, 0.025)
WINDOW, REFIT = 1260, 21
FIRST_FORECAST = "2010-01-01"

UNIVERSES = {
    "U1_pilot": ["SPY", "IEF", "GLD"],
    "U3_credit": ["SPY", "IEF", "HYG"],
    "U4_globaleq": ["SPY", "EFA", "EEM"],
    "U5_4asset": ["SPY", "IEF", "GLD", "EEM"],
    "U8_sectors": ["XLU", "XLK", "XLF", "XLE"],
    "U10_riskassets": ["HYG", "EEM", "VNQ", "DBC"],
}


def build_providers(spy, ief, vix, which=None):
    rv = pd.Series(spy).rolling(21).std().values
    corr63 = pd.Series(spy).rolling(63).corr(pd.Series(ief)).values
    P = {
        "HMM_SPY2": HMMProvider("HMM_SPY2", spy, K=2),
        "HMM_SPY3": HMMProvider("HMM_SPY3", spy, K=3),
        "HMM_SPYVIX2": HMMProvider("HMM_SPYVIX2", np.c_[spy * 100, np.log(vix)], K=2),
        "RULE_VIX20": RuleProvider("RULE_VIX20", vix, thr=20.0),
        "RULE_RV75": RuleProvider("RULE_RV75", rv, q=0.75),
        "RULE_CORR": RuleProvider("RULE_CORR", corr63, q=2 / 3),
    }
    return P if which is None else {k: P[k] for k in which}


def run_universe(name: str, providers=None, dcc: bool = True, last_date: str | None = None) -> dict:
    t_start = time.time()
    R_all, vix_all = load_explore_returns()
    cols = UNIVERSES[name]
    df = R_all[cols].dropna()
    spy = R_all["SPY"].reindex(df.index).values
    ief = R_all["IEF"].reindex(df.index).values
    vix = vix_all.reindex(df.index).ffill().values
    if last_date:
        keep = df.index <= pd.Timestamp(last_date)
        df, spy, ief, vix = df[keep], spy[keep], ief[keep], vix[keep]
    R = df.values
    w = np.ones(R.shape[1]) / R.shape[1]
    start = max(int(np.searchsorted(df.index, pd.Timestamp(FIRST_FORECAST))), WINDOW)
    window = min(WINDOW, start)

    bench = run_benchmarks(R, w, ALPHAS, start, window=window, refit=REFIT, dcc=dcc)
    models = {"V": {a: dict(bench["V"][a]) for a in ALPHAS}, "E": {a: dict(bench["E"][a]) for a in ALPHAS}}
    stress = {}
    diag = {}
    for pname, prov in build_providers(spy, ief, vix, providers).items():
        rr = run_regime_models(R, w, prov, ALPHAS, start, window=window, refit=REFIT)
        for a in ALPHAS:
            for m in ("A", "B", "C", "D"):
                key = "A" if m == "A" else f"{pname}/{m}"
                models["V"][a][key], models["E"][a][key] = rr["V"][a][m], rr["E"][a][m]
        stress[pname] = rr["stress_prob"]
        diag[pname] = {"n_degenerate_refits": getattr(prov, "n_degenerate", 0)}
        print(f"  [{name}] {pname} done ({time.time() - t_start:.0f}s)", flush=True)
    idx = np.arange(start, len(R))
    return {"universe": name, "assets": cols, "dates": df.index[idx], "y": (R @ w)[idx],
            "V": {a: {m: v[idx] for m, v in models["V"][a].items()} for a in ALPHAS},
            "E": {a: {m: v[idx] for m, v in models["E"][a].items()} for a in ALPHAS},
            "stress": {k: v[idx] for k, v in stress.items()}, "diag": diag,
            "window": window, "runtime_s": time.time() - t_start}


def _job(name):
    res = run_universe(name)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"{name}.pkl", "wb") as f:
        pickle.dump(res, f)
    print(f"{name}: {res['runtime_s']:.0f}s, {len(res['y'])} forecast days "
          f"({res['dates'][0].date()}..{res['dates'][-1].date()})", flush=True)
    return name


def validate() -> None:
    from src.engine import fz0
    res = run_universe("U1_pilot", providers=["HMM_SPY2"], dcc=False, last_date="2015-12-31")
    pilot = json.load(open(ROOT / "output" / "tables" / "wp3_walk_forward.json"))
    print("\nVALIDATION vs pilot WP3 table (alpha=5%, 2010-2015):")
    ok = True
    for a in ALPHAS:
        tab = pilot[str(a)]["table"]
        y = res["y"]
        pairs = [("A", "A"), ("HMM_SPY2/B", "B"), ("HMM_SPY2/C", "C"), ("HMM_SPY2/D", "D"),
                 ("HS", "HS"), ("EWMA", "EWMA"), ("GARCHt", "GARCHt")]
        for mine, theirs in pairs:
            L = fz0(y, res["V"][a][mine], res["E"][a][mine], a).mean()
            diff = L - tab[theirs]["fz0_loss"]
            ok &= abs(diff) < 1e-4   # separate yfinance downloads differ at ~1e-6
            print(f"  alpha={a:<5} {theirs:7s} new={L:+.6f} pilot={tab[theirs]['fz0_loss']:+.6f} diff={diff:+.1e}")
    print("VALIDATION", "PASSED" if ok else "FAILED")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--validate":
        validate()
    else:
        names = args or list(UNIVERSES)
        with ProcessPoolExecutor(max_workers=min(len(names), 6)) as ex:
            list(ex.map(_job, names))
