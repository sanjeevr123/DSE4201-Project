"""
Exploratory step 13: controlled-ablation ladder with equal-mean / zero-mean controls and Student-t components.
Data through 2019-12-31 only. See docs/decisions_log.md ("Ladder / equal-mean control").

  .venv/bin/python scripts/explore_13_ladder.py --validate
      (1) static 'regime|N' B/D must equal the saved pilot-universe backtest (output/explore/backtests/U1_pilot.pkl);
      (2) layer-2 default (non-zero-mean) must equal the saved routes run (output/explore/routes/U1_routes_HMM_SPY2.pkl)
  .venv/bin/python scripts/explore_13_ladder.py [UNIVERSE ...]
      full run, SPY 2-state HMM; default universes U1_pilot U3_credit U8_sectors U10_riskassets

Output: output/explore/ladder/<universe>.pkl  (static ladder 'S' + zero-mean GARCH-margin arms 'L2Z').
Scored by scripts/explore_14_score_ladder.py. Run with OMP_NUM_THREADS=1.
"""
from __future__ import annotations

import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from explore_05_backtests import ALPHAS, REFIT, WINDOW, build_providers  # noqa: E402
from explore_08_routes import prepare  # noqa: E402
from src.explore_ladder import run_static_ladder  # noqa: E402
from src.explore_routes import run_rs_corr  # noqa: E402

OUT = ROOT / "output" / "explore" / "ladder"
DEFAULT_UNIVERSES = ["U1_pilot", "U3_credit", "U8_sectors", "U10_riskassets"]
PROVIDER = "HMM_SPY2"


def _cut(d, start):
    return {a: {m: v[start:] for m, v in d[a].items()} for a in d}


def run(universe, last_date=None, layer2_default=False):
    t0 = time.time()
    df, spy, ief, vix, tnx, move, start = prepare(universe, last_date)
    R = df.values
    w = np.ones(R.shape[1]) / R.shape[1]
    mk = lambda: build_providers(spy, ief, vix, [PROVIDER], tnx, move)[PROVIDER]
    out = {"universe": universe, "provider": PROVIDER, "assets": list(df.columns),
           "dates": df.index[start:], "y": (R @ w)[start:]}
    s = run_static_ladder(R, w, mk(), ALPHAS, start, window=WINDOW, refit=REFIT)
    out["S"] = {"V": _cut(s["V"], start), "E": _cut(s["E"], start), "stress": s["stress_prob"][start:],
                "nu": s["nu"]}
    print(f"  [{universe}] static ladder done ({time.time() - t0:.0f}s)", flush=True)
    r2 = run_rs_corr(R, w, mk(), ALPHAS, start, window=WINDOW, refit=REFIT, zero_mean=not layer2_default)
    key = "L2" if layer2_default else "L2Z"
    out[key] = {"V": _cut(r2["V"], start), "E": _cut(r2["E"], start), "nu": r2["nu"]}
    print(f"  [{universe}] layer 2 ({'default' if layer2_default else 'zero-mean'}) done ({time.time() - t0:.0f}s)",
          flush=True)
    out["runtime_s"] = time.time() - t0
    return out


def _job(universe):
    res = run(universe)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"{universe}.pkl", "wb") as f:
        pickle.dump(res, f)
    print(f"{universe}: {res['runtime_s']:.0f}s, {len(res['y'])} forecast days", flush=True)


def validate():
    ok = True
    res = run("U1_pilot", last_date="2012-12-31", layer2_default=True)
    n = len(res["y"])
    old = pickle.load(open(ROOT / "output" / "explore" / "backtests" / "U1_pilot.pkl", "rb"))
    rt = pickle.load(open(ROOT / "output" / "explore" / "routes" / "U1_routes_HMM_SPY2.pkl", "rb"))
    for a in ALPHAS:
        for m in ("B", "D"):
            for key in ("V", "E"):
                d = np.max(np.abs(res["S"][key][a][f"{m}|regime|N"] - old[key][a][f"HMM_SPY2/{m}"][:n]))
                ok &= d < 1e-8
                print(f"  static {m} alpha={a} {key}: max|new-saved| = {d:.2e}")
        for m in ("CCC_S_N", "RSC_S_N", "RSC_S_t"):
            for key in ("V", "E"):
                d = np.max(np.abs(res["L2"][key][a][m] - rt["L2"][key][a][m][:n]))
                ok &= d < 1e-8
                print(f"  layer2 {m} alpha={a} {key}: max|new-saved| = {d:.2e}")
    print("VALIDATION", "PASSED" if ok else "FAILED")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--validate":
        validate()
    else:
        unis = args or DEFAULT_UNIVERSES
        with ProcessPoolExecutor(max_workers=len(unis)) as ex:
            list(ex.map(_job, unis))
