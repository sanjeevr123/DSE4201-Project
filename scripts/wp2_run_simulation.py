"""
WP2: simulation power study driver.

Runs, for each DGP calibration ("stylised" and "calibrated") and each of the
4 scenarios (S0-S3):
  - 200 replications at alpha=0.05
  - 100 replications at alpha=0.025
Then, for the stylised DGP's S1 scenario only, additional replications at
5- and 15-year test lengths (the 10-year point reuses the main run, since
the default test length already is 10 years / 2520 days), for the
power-vs-test-length analysis.

Each (dgp, scenario, alpha[, T]) combination is checkpointed to its own
JSONL file under output/sim_checkpoints/ as replications complete, so a
crash loses at most the in-flight batch, and re-running this script resumes
from wherever it left off rather than re-simulating completed replications.

Run with:
    .venv/bin/python scripts/wp2_run_simulation.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.config import get_config
from src.wp2_simulation import aggregate_scenario, run_replications, scenario_names

TRADING_DAYS_PER_YEAR = 252


def main(n_jobs: int = -1) -> None:
    cfg = get_config()["wp2"]
    n_full_05 = cfg["full_reps_alpha_05"]
    n_full_025 = cfg["full_reps_alpha_025"]
    burn_in = cfg["burn_in"]
    default_test_days = cfg["test_days"]

    summary = {}
    t0 = time.time()

    for dgp_name in ["stylised", "calibrated"]:
        summary[dgp_name] = {}
        for scen in scenario_names():
            ts = time.time()
            res_05 = run_replications(dgp_name, scen, 0.05, n_full_05, n_jobs=n_jobs)
            res_025 = run_replications(dgp_name, scen, 0.025, n_full_025, n_jobs=n_jobs)
            summary[dgp_name][scen] = {
                "alpha_0.05": aggregate_scenario(res_05),
                "alpha_0.025": aggregate_scenario(res_025),
            }
            print(f"[{dgp_name}] {scen}: {n_full_05}+{n_full_025} reps in "
                  f"{time.time()-ts:.0f}s (D<B power @5%: "
                  f"{summary[dgp_name][scen]['alpha_0.05']['D_lt_B']['power']:.2%})")

    # Power vs test length, stylised DGP, S1 scenario, alpha=0.05 only.
    length_scen = cfg["power_vs_length_scenario"]
    length_results = {}
    for years in cfg["power_vs_length_years"]:
        test_days = years * TRADING_DAYS_PER_YEAR
        ts = time.time()
        if test_days == default_test_days:
            res = run_replications("stylised", length_scen, 0.05, n_full_05, n_jobs=n_jobs)
        else:
            res = run_replications("stylised", length_scen, 0.05, n_full_05,
                                    T=burn_in + test_days, n_jobs=n_jobs)
        length_results[years] = aggregate_scenario(res)
        print(f"[power-vs-length] {years}y ({test_days}d): {n_full_05} reps in "
              f"{time.time()-ts:.0f}s (D<B power: {length_results[years]['D_lt_B']['power']:.2%})")

    summary["power_vs_length"] = {"scenario": length_scen, "by_years": length_results}
    summary["total_runtime_seconds"] = time.time() - t0

    out_path = REPO_ROOT / "output" / "tables" / "wp2_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=float)
    print(f"\nSaved WP2 summary to {out_path} (total {summary['total_runtime_seconds']:.0f}s)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-jobs", type=int, default=-1,
                         help="Parallel worker count for joblib (default: all cores).")
    args = parser.parse_args()
    main(n_jobs=args.n_jobs)
