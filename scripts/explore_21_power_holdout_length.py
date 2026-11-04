"""
Exploratory step 21: power / size of every ladder step at the hold-out length (1,508 test days), on the same GARCH-margin
DGP and pipeline as scripts/explore_16_power_garch.py, 500 replications per scenario (declared in docs/decisions_log.md).
Seeds are distinct from the earlier study (+3_000_000). Each line stores t, two-sided p, mean difference and HAC SE per step.

  .venv/bin/python scripts/explore_21_power_holdout_length.py --time             # 2 reps, prints seconds per rep
  .venv/bin/python scripts/explore_21_power_holdout_length.py --workers 5        # 500 reps/scenario, resumable
Output: output/explore/ladder/power_1508/<scenario>.jsonl. Export the single-thread variables first (BLAS must not fan out).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import get_config  # noqa: E402
from src.dgp import corr_matrix, get_dgp_params  # noqa: E402
from src.dgp_garch import simulate_garch_rs  # noqa: E402
from src.engine import dm_test, fz0  # noqa: E402
from src.explore_ladder import run_static_ladder  # noqa: E402
from src.explore_routes import run_rs_corr  # noqa: E402
from src.explore_wf import HMMProvider  # noqa: E402
from src.wp2_simulation import _rep_seed, scenario_names  # noqa: E402

OUT = ROOT / "output" / "explore" / "ladder" / "power_1508"
W3 = np.ones(3) / 3
ALPHAS = (0.05, 0.025)
GARCH_A, GARCH_B = 0.08, 0.90
TEST_DAYS, N_REPS, SEED_OFFSET = 1508, 500, 3_000_000
# step -> (richer, baseline); negative t => richer better
PAIRS = {"regime_vol": ("B|pooled|N", "A|pooled|N"), "static_corr": ("D|pooled|N", "B|pooled|N"),
         "margin_pooledcorr": ("CCC_S_N", "B|pooled|N"), "margin_effect": ("RSC_S_N", "D|pooled|N"),
         "corr_with_margins": ("RSC_S_N", "CCC_S_N"), "corr_with_margins_t": ("RSC_S_t", "CCC_S_t"),
         "pair_with_margins": ("RSC_P_N", "CCC_S_N"), "pair_with_margins_t": ("RSC_P_t", "CCC_S_t")}


def one_rep(scenario: str, rep: int, seed_base: int = 0) -> dict:
    wp2 = get_config()["wp2"]
    burn_in, T = wp2["burn_in"], wp2["burn_in"] + TEST_DAYS
    params = get_dgp_params("stylised")
    stress_corr = corr_matrix(*wp2["scenarios"][scenario])
    rng = np.random.default_rng(_rep_seed(scenario, rep, "stylised", seed_base) + SEED_OFFSET)
    R, S = simulate_garch_rs(params, stress_corr, T, rng, a=GARCH_A, b=GARCH_B)
    mk = lambda: HMMProvider("HMM_EQ2", R[:, 0], K=2, seed=rep)
    s = run_static_ladder(R, W3, mk(), ALPHAS, burn_in, window=burn_in, refit=21, models=("A", "B", "D"),
                          mean_modes=("pooled",))
    l2 = run_rs_corr(R, W3, mk(), ALPHAS, burn_in, window=burn_in, refit=21)
    y = R[burn_in:] @ W3
    out = {"scenario": scenario, "rep": rep, "stress_share": float(S[burn_in:].mean())}
    for a in ALPHAS:
        F = {k: (v[burn_in:], s["E"][a][k][burn_in:]) for k, v in s["V"][a].items()}
        F.update({k: (v[burn_in:], l2["E"][a][k][burn_in:]) for k, v in l2["V"][a].items()})
        L = {k: fz0(y, v, e, a) for k, (v, e) in F.items()}
        dm = {}
        for n, (f, b) in PAIRS.items():
            t, p = dm_test(L[f], L[b])
            d = float((L[f] - L[b]).mean())
            dm[n] = {"t": float(t), "p": float(p), "mean_diff": d, "se": abs(d / t) if t != 0 else float("nan")}
        out[str(a)] = {"loss": {k: float(L[k].mean()) for k in L},
                       "hit": {k: float((y <= F[k][0]).mean()) for k in F}, "dm": dm}
    return out


def run(workers: int, n_reps: int = N_REPS):
    assert 1 <= workers <= 5, "CPU limit: at most 5 workers"
    OUT.mkdir(parents=True, exist_ok=True)
    for scen in scenario_names():
        path = OUT / f"{scen}.jsonl"
        done = set()
        if path.exists():
            for l in open(path):
                try:
                    done.add(json.loads(l)["rep"])
                except (json.JSONDecodeError, KeyError):
                    pass            # a line cut off by an interrupted run: that replication is simply redone
        todo = [r for r in range(n_reps) if r not in done]
        if not todo:
            continue
        gen = Parallel(n_jobs=workers, return_as="generator_unordered")(delayed(one_rep)(scen, r) for r in todo)
        with open(path, "a") as f:
            if path.stat().st_size and path.read_bytes()[-1:] != b"\n":
                f.write("\n")           # terminate a line cut off by an interrupted run
            for res in gen:
                f.write(json.dumps(res) + "\n")
                f.flush()
        print(f"{scen}: {len(todo)} new reps", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--time", action="store_true")
    args = ap.parse_args()
    if args.time:
        t0 = time.time()
        for rep in range(2):
            r = one_rep("S2_strong_breakdown", rep)
            print(rep, f"{time.time() - t0:.0f}s", {k: round(v["t"], 2) for k, v in r["0.05"]["dm"].items()})
    else:
        if args.workers is None:
            ap.error("--workers is required (at most 5)")
        run(args.workers)
