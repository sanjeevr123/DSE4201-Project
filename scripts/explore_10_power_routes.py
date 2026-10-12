"""
Exploratory step 10 (plan step 2B): power / size of the Route M and Route P tests, using the pilot's WP2
data-generating process (src/dgp.py: 2-state Markov-switching multivariate Student-t, stylised calibration,
scenarios S0 null, S1 moderate, S2 strong, S3 flight-to-quality) and the SAME simulated datasets (same seeds)
as the pilot's WP2 run.

Layer 1 (static within-regime covariance) only: the DGP has regime-switching volatilities and correlations but
no GARCH dynamics, so the GARCH-margin layer is not a meaningful comparison here.

  .venv/bin/python scripts/explore_10_power_routes.py --validate     # D-B t-stat vs the pilot's checkpoint
  .venv/bin/python scripts/explore_10_power_routes.py [N_REPS]       # default 200 reps/scenario, resumable

Output: output/explore/routes/power/<scenario>.jsonl (one line per replication).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import get_config  # noqa: E402
from src.dgp import corr_matrix, get_dgp_params, simulate  # noqa: E402
from src.engine import dm_test, fz0  # noqa: E402
from src.explore_routes import make_variants_fn  # noqa: E402
from src.explore_wf import HMMProvider, run_regime_models  # noqa: E402
from src.wp2_simulation import _rep_seed, scenario_names  # noqa: E402

OUT = ROOT / "output" / "explore" / "routes" / "power"
W3 = np.ones(3) / 3
ALPHAS = (0.05, 0.025)
MODELS = ("B", "D", "B_M", "D_M", "D_P")
PAIRS = {"D-B": ("D", "B"), "DM-B": ("D_M", "B"), "DP-B": ("D_P", "B"), "DM-BM": ("D_M", "B_M"),
         "DM-D": ("D_M", "D"), "DP-D": ("D_P", "D"), "DM-DP": ("D_M", "D_P")}


def one_rep(scenario: str, rep: int, seed_base: int = 0) -> dict:
    wp2 = get_config()["wp2"]
    burn_in, T = wp2["burn_in"], wp2["burn_in"] + wp2["test_days"]
    params = get_dgp_params("stylised")
    stress_corr = corr_matrix(*wp2["scenarios"][scenario])
    rng = np.random.default_rng(_rep_seed(scenario, rep, "stylised", seed_base))
    R, S, pred, true_covs = simulate(params, stress_corr, T, rng)
    prov = HMMProvider("HMM_EQ2", R[:, 0], K=2, seed=rep)          # same HMM as the pilot (fit_hmm path)
    res = run_regime_models(R, W3, prov, ALPHAS, burn_in, window=burn_in, refit=21, models=MODELS,
                            variants_fn=make_variants_fn((0, 1)))
    y = R[burn_in:, :] @ W3
    out = {"scenario": scenario, "rep": rep}
    for a in ALPHAS:
        L = {m: fz0(y, res["V"][a][m][burn_in:], res["E"][a][m][burn_in:], a) for m in MODELS}
        out[str(a)] = {"loss": {m: float(L[m].mean()) for m in MODELS},
                       "dm": {k: [float(v) for v in dm_test(L[f], L[s])] for k, (f, s) in PAIRS.items()}}
    return out


def run(n_reps: int, n_jobs: int = -1):
    OUT.mkdir(parents=True, exist_ok=True)
    for scen in scenario_names():
        path = OUT / f"{scen}.jsonl"
        done = set()
        if path.exists():
            done = {json.loads(l)["rep"] for l in open(path) if l.strip()}
        todo = [r for r in range(n_reps) if r not in done]
        if not todo:
            continue
        gen = Parallel(n_jobs=n_jobs, return_as="generator")(delayed(one_rep)(scen, r) for r in todo)
        with open(path, "a") as f:
            for res in gen:
                f.write(json.dumps(res) + "\n")
                f.flush()
        print(f"{scen}: {len(todo)} new reps", flush=True)


def validate(n=3):
    ck = ROOT / "output" / "sim_checkpoints"
    ok = True
    for scen in ("S0_vol_only", "S1_moderate_breakdown"):
        pilot = {}
        for line in open(ck / f"stylised_{scen}_alpha0.05.jsonl"):
            r = json.loads(line)
            pilot[r["rep"]] = r
        for rep in range(n):
            mine = one_rep(scen, rep)["0.05"]
            t_new, t_old = mine["dm"]["D-B"][0], pilot[rep]["dm"]["D-B"][0]
            l_new, l_old = mine["loss"]["D"] - mine["loss"]["B"], pilot[rep]["loss"]["D"] - pilot[rep]["loss"]["B"]
            ok &= abs(t_new - t_old) < 1e-6 and abs(l_new - l_old) < 1e-9
            print(f"  {scen} rep {rep}: D-B t new={t_new:+.6f} pilot={t_old:+.6f}; loss diff new={l_new:+.3e} pilot={l_old:+.3e}")
    print("VALIDATION", "PASSED" if ok else "FAILED")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--validate":
        validate()
    else:
        run(int(a[0]) if a else 200)
