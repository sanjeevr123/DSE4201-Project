"""
Exploratory step 8 (steps 1 and 2 of the plan): GARCH-margin + regime-correlation arm and the
Route M / Route P comparison, on the pilot universe (SPY/IEF/GLD, equal weight), 2010-2019.

  .venv/bin/python scripts/explore_08_routes.py --validate
      reproduces model B and D of the pilot-universe backtest (output/explore/backtests/U1_pilot.pkl)
      with the new layer-1 code path (must agree to ~1e-9 before anything else is trusted)
  .venv/bin/python scripts/explore_08_routes.py --universes U3_credit U8_sectors U10_riskassets
      layer 2 only (SPY HMM), to check the GARCH-margin effect on other universes
  .venv/bin/python scripts/explore_08_routes.py [PROVIDER ...]
      full run; default providers: HMM_SPY2 (declared primary) and RULE_RV75 (sensitivity)

Output: output/explore/routes/U1_routes_<provider>.pkl. Scored by scripts/explore_09_score_routes.py.
Run with OMP_NUM_THREADS=1 when launching several processes.
"""
from __future__ import annotations

import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.explore import load_explore_returns, load_rates  # noqa: E402
from src.explore_routes import make_variants_fn, run_rs_corr  # noqa: E402
from src.explore_wf import run_regime_models  # noqa: E402
from explore_05_backtests import ALPHAS, FIRST_FORECAST, REFIT, UNIVERSES, WINDOW, build_providers  # noqa: E402

OUT = ROOT / "output" / "explore" / "routes"
PAIR = (0, 1)           # SPY-IEF, fixed in advance by theory (docs/decisions_log.md)
L1_MODELS = ("B", "D", "B_M", "D_M", "D_P")


def prepare(universe="U1_pilot", last_date=None):
    R_all, vix_all = load_explore_returns()
    cols = UNIVERSES[universe]
    df = R_all[cols].dropna()
    spy = R_all["SPY"].reindex(df.index).values
    ief = R_all["IEF"].reindex(df.index).values
    vix = vix_all.reindex(df.index).ffill().values
    rates = load_rates().reindex(df.index).ffill()
    tnx, move = rates["^TNX"].values, rates["^MOVE"].values
    if last_date:
        k = (df.index <= pd.Timestamp(last_date))
        df, spy, ief, vix, tnx, move = df[k], spy[k], ief[k], vix[k], tnx[k], move[k]
    start = max(int(np.searchsorted(df.index, pd.Timestamp(FIRST_FORECAST))), WINDOW)
    return df, spy, ief, vix, tnx, move, start


def run(provider_name, universe="U1_pilot", layers=(1, 2), last_date=None):
    t0 = time.time()
    df, spy, ief, vix, tnx, move, start = prepare(universe, last_date)
    R = df.values
    w = np.ones(R.shape[1]) / R.shape[1]
    out = {"universe": universe, "provider": provider_name, "assets": list(df.columns), "pair": PAIR,
           "dates": df.index[start:], "y": (R @ w)[start:]}
    if 1 in layers:
        prov = build_providers(spy, ief, vix, [provider_name], tnx, move)[provider_name]
        r1 = run_regime_models(R, w, prov, ALPHAS, start, window=WINDOW, refit=REFIT,
                               models=L1_MODELS, variants_fn=make_variants_fn(PAIR))
        out["L1"] = {"V": {a: {m: v[start:] for m, v in r1["V"][a].items()} for a in ALPHAS},
                     "E": {a: {m: v[start:] for m, v in r1["E"][a].items()} for a in ALPHAS},
                     "stress": r1["stress_prob"][start:]}
        print(f"  [{provider_name}] layer 1 done ({time.time() - t0:.0f}s)", flush=True)
    if 2 in layers:
        prov = build_providers(spy, ief, vix, [provider_name], tnx, move)[provider_name]
        r2 = run_rs_corr(R, w, prov, ALPHAS, start, window=WINDOW, refit=REFIT, pair=PAIR)
        out["L2"] = {"V": {a: {m: v[start:] for m, v in r2["V"][a].items()} for a in ALPHAS},
                     "E": {a: {m: v[start:] for m, v in r2["E"][a].items()} for a in ALPHAS},
                     "stress": r2["stress_prob"][start:], "nu": r2["nu"]}
        print(f"  [{provider_name}] layer 2 done ({time.time() - t0:.0f}s)", flush=True)
    out["runtime_s"] = time.time() - t0
    return out


def _job(name):
    res = run(name)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"U1_routes_{name}.pkl", "wb") as f:
        pickle.dump(res, f)
    print(f"{name}: {res['runtime_s']:.0f}s, {len(res['y'])} forecast days", flush=True)


def _job_universe(universe):
    """Layer 2 only, SPY HMM provider: the GARCH-margin confound check on another universe.
    (Route M / Route P arms are computed but not scored there: the pair is only meaningful for SPY-IEF.)"""
    res = run("HMM_SPY2", universe=universe, layers=(2,))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"{universe}_routes_HMM_SPY2.pkl", "wb") as f:
        pickle.dump(res, f)
    print(f"{universe}: {res['runtime_s']:.0f}s, {len(res['y'])} forecast days", flush=True)


def validate():
    res = run("HMM_SPY2", layers=(1,), last_date="2012-12-31")
    old = pickle.load(open(ROOT / "output" / "explore" / "backtests" / "U1_pilot.pkl", "rb"))
    n = len(res["y"])
    ok = True
    for a in ALPHAS:
        for m in ("B", "D"):
            for key, new in (("V", res["L1"]["V"][a][m]), ("E", res["L1"]["E"][a][m])):
                ref = old[key][a][f"HMM_SPY2/{m}"][:n]
                d = np.max(np.abs(new - ref))
                ok &= d < 1e-8
                print(f"  alpha={a} {m} {key}: max |new - saved| = {d:.2e}")
    print("VALIDATION", "PASSED" if ok else "FAILED")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--validate":
        validate()
    elif args and args[0] == "--universes":
        unis = args[1:]
        with ProcessPoolExecutor(max_workers=len(unis)) as ex:
            list(ex.map(_job_universe, unis))
    else:
        names = args or ["HMM_SPY2", "RULE_RV75"]
        with ProcessPoolExecutor(max_workers=len(names)) as ex:
            list(ex.map(_job, names))
