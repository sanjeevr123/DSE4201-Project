"""
Exploratory step 16: power / size of every ladder step on a DGP with GARCH margins (src/dgp_garch.py), scenarios
S0-S3, 200 replications per scenario (resumable). Static rungs use the pooled-mean variants; layer 2 uses the
default constant-mean GARCH-margin arms.

  .venv/bin/python scripts/explore_16_power_garch.py --time        # 2 reps, prints seconds per rep
  .venv/bin/python scripts/explore_16_power_garch.py [N_REPS]      # default 200 reps/scenario
Output: output/explore/ladder/power/<scenario>.jsonl. Run with OMP_NUM_THREADS=1.
"""
from __future__ import annotations

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

OUT = ROOT / "output" / "explore" / "ladder" / "power"
W3 = np.ones(3) / 3
ALPHAS = (0.05, 0.025)
GARCH_A, GARCH_B = 0.08, 0.90
# step -> (richer, baseline); negative t => richer better
PAIRS = {"regime_vol": ("B|pooled|N", "A|pooled|N"), "static_corr": ("D|pooled|N", "B|pooled|N"),
         "margin_pooledcorr": ("CCC_S_N", "B|pooled|N"), "margin_effect": ("RSC_S_N", "D|pooled|N"),
         "corr_with_margins": ("RSC_S_N", "CCC_S_N"), "corr_with_margins_t": ("RSC_S_t", "CCC_S_t"),
         "pair_with_margins": ("RSC_P_N", "CCC_S_N"), "pair_with_margins_t": ("RSC_P_t", "CCC_S_t")}


def one_rep(scenario: str, rep: int, seed_base: int = 0) -> dict:
    wp2 = get_config()["wp2"]
    burn_in, T = wp2["burn_in"], wp2["burn_in"] + wp2["test_days"]
    params = get_dgp_params("stylised")
    stress_corr = corr_matrix(*wp2["scenarios"][scenario])
    rng = np.random.default_rng(_rep_seed(scenario, rep, "stylised", seed_base) + 2_000_000)
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
        out[str(a)] = {"loss": {k: float(L[k].mean()) for k in L},
                       "hit": {k: float((y <= F[k][0]).mean()) for k in F},
                       "dm": {n: [float(x) for x in dm_test(L[f], L[b])] for n, (f, b) in PAIRS.items()}}
    return out


def run(n_reps: int):
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
        gen = Parallel(n_jobs=-1, return_as="generator")(delayed(one_rep)(scen, r) for r in todo)
        with open(path, "a") as f:
            if path.stat().st_size and path.read_bytes()[-1:] != b"\n":
                f.write("\n")           # terminate a line cut off by an interrupted run
            for res in gen:
                f.write(json.dumps(res) + "\n")
                f.flush()
        print(f"{scen}: {len(todo)} new reps", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--time":
        t0 = time.time()
        for rep in range(2):
            r = one_rep("S2_strong_breakdown", rep)
            print(rep, f"{time.time() - t0:.0f}s", {k: round(v[0], 2) for k, v in r["0.05"]["dm"].items()})
    else:
        run(int(a[0]) if a else 200)
