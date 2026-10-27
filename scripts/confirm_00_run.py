"""
Confirmatory pipeline (frozen specification: docs/preregistration_confirmatory.md).

  .venv/bin/python scripts/confirm_00_run.py pseudo     # DRY RUN: forecasts 2016-01-01..2019-12-31, data <= 2019-12-31
  .venv/bin/python scripts/confirm_00_run.py holdout    # ONE-SHOT: forecasts 2020-01-01..2025-12-31

'holdout' refuses to run unless (i) the git tag `spec-freeze-v1` exists and (ii) HEAD has no uncommitted changes to
src/, scripts/confirm_*.py or docs/preregistration_confirmatory.md, and it refuses to overwrite an existing output.
The two modes execute exactly the same code path; only the dates differ.

Data: the archived pilot download data/raw/spy_ief_gld_raw_2026-09-26.csv (adjusted close, simple returns). In 'pseudo'
mode the data are truncated at 2019-12-31 BEFORE any computation (nothing later is ever loaded into the models).
Output: output/confirm/<mode>_forecasts.pkl. Run with OMP_NUM_THREADS=1.
"""
from __future__ import annotations

import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.explore_ladder import run_static_ladder  # noqa: E402
from src.explore_routes import run_rs_corr  # noqa: E402
from src.explore_wf import HMMProvider, run_benchmarks  # noqa: E402

RAW = ROOT / "data" / "raw" / "spy_ief_gld_raw_2026-09-26.csv"
OUT = ROOT / "output" / "confirm"
TICKERS = ["SPY", "IEF", "GLD"]
ALPHAS, WINDOW, REFIT = (0.05, 0.025), 1260, 21
PERIODS = {"pseudo": ("2016-01-01", "2019-12-31", "2019-12-31"), "holdout": ("2020-01-01", "2025-12-31", "2025-12-31")}
PAIR = (0, 1)


def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def check_freeze():
    if "spec-freeze-v1" not in _git("tag").split():
        sys.exit("REFUSED: git tag spec-freeze-v1 does not exist (freeze the specification first).")
    tagged = _git("rev-parse", "spec-freeze-v1^{commit}")
    changed = _git("diff", "--name-only", tagged, "--", "src", "scripts/confirm_00_run.py", "scripts/confirm_01_score.py",
                   "docs/preregistration_confirmatory.md")
    dirty = _git("status", "--porcelain", "--", "src", "scripts/confirm_00_run.py", "scripts/confirm_01_score.py",
                 "docs/preregistration_confirmatory.md")
    if changed or dirty:
        sys.exit(f"REFUSED: frozen files differ from tag spec-freeze-v1:\n{changed}\n{dirty}")


def load(last_date: str) -> pd.DataFrame:
    raw = pd.read_csv(RAW, index_col=0, parse_dates=True)
    px = raw[[f"Adj Close_{t}" for t in TICKERS]]
    px.columns = TICKERS
    px = px.loc[:last_date].dropna()
    assert px.index.max() <= pd.Timestamp(last_date), "data past the allowed end date"
    return px.pct_change().dropna()


def main(mode: str):
    first, last_fc, last_data = PERIODS[mode]
    out_path = OUT / f"{mode}_forecasts.pkl"
    if mode == "holdout":
        check_freeze()
    if out_path.exists():
        sys.exit(f"REFUSED: {out_path} already exists (one run per mode; delete deliberately to redo a dry run).")
    t0 = time.time()
    r = load(last_data)
    R, w = r.values, np.ones(3) / 3
    start = int(np.searchsorted(r.index, pd.Timestamp(first)))
    assert start >= WINDOW and r.index[start] >= pd.Timestamp(first)
    mk = lambda: HMMProvider("HMM_SPY2", R[:, 0], K=2)
    cut = lambda d: {a: {m: v[start:] for m, v in d[a].items()} for a in d}
    s = run_static_ladder(R, w, mk(), ALPHAS, start, window=WINDOW, refit=REFIT, models=("A", "B", "D"),
                          mean_modes=("pooled",))
    l2 = run_rs_corr(R, w, mk(), ALPHAS, start, window=WINDOW, refit=REFIT, pair=PAIR)
    bm = run_benchmarks(R, w, ALPHAS, start, window=WINDOW, refit=REFIT, dcc=True)
    res = {"mode": mode, "assets": TICKERS, "dates": r.index[start:], "y": (R @ w)[start:], "returns": R[start:],
           "S": {"V": cut(s["V"]), "E": cut(s["E"]), "stress": s["stress_prob"][start:], "nu": s["nu"]},
           "L2": {"V": cut(l2["V"]), "E": cut(l2["E"]), "stress": l2["stress_prob"][start:], "nu": l2["nu"]},
           "B": {"V": cut(bm["V"]), "E": cut(bm["E"])}, "runtime_s": time.time() - t0,
           "git_head": _git("rev-parse", "HEAD"), "freeze_tag": _git("rev-parse", "spec-freeze-v1^{commit}") or None}
    OUT.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(res, f)
    print(f"{mode}: {len(res['y'])} forecast days {res['dates'][0].date()}..{res['dates'][-1].date()} "
          f"({res['runtime_s']:.0f}s) -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PERIODS:
        sys.exit(__doc__)
    main(sys.argv[1])
