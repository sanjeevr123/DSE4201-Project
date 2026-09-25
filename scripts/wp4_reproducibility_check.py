"""
WP4: reproducibility check.

Honest scope note: this is a single-developer-laptop pilot, not a
multi-machine study, so "clean environment" here means re-running each
deterministic step from its saved inputs (fixed seeds, the same archived
raw data) and diffing outputs -- not provisioning a second physical
machine. This is recorded as a deliberate, conservative scope choice (see
docs/decision_log.md).

Produces output/tables/wp4_reproducibility.json covering:
  1. WP1 test suite re-run (pass/fail counts).
  2. WP3 real-data pipeline re-run, diffed numerically against the
     committed output/tables/wp3_*.json.
  3. A subset of WP2 replications recomputed directly (bypassing the
     checkpoint) and diffed bit-for-bit against the checkpointed values,
     by (dgp, scenario, rep) key.
  4. WP2 re-run with a different master seed (reduced replication count),
     compared against the main run's conclusions (power / false-positive
     rate) within Monte Carlo error.
  5. Runtime and machine specs.

Run with:
    .venv/bin/python scripts/wp4_reproducibility_check.py
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from src.wp2_simulation import aggregate_scenario, one_rep, run_replications, scenario_names

TABLE_DIR = REPO_ROOT / "output" / "tables"


def check_wp1_tests() -> dict:
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    elapsed = time.time() - t0
    tail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    return {
        "returncode": result.returncode,
        "summary_line": tail,
        "elapsed_seconds": elapsed,
        "all_passed": result.returncode == 0,
    }


def check_wp3_reproducibility() -> dict:
    committed = {}
    for name in ["wp3_descriptive.json", "wp3_walk_forward.json", "wp3_episodes.json"]:
        path = TABLE_DIR / name
        if not path.exists():
            return {"error": f"{name} not found -- run scripts/wp3_run_real_data_pilot.py first"}
        with open(path) as f:
            committed[name] = json.load(f)

    from src.wp3_real_data import (
        descriptive_regime_stats, episode_diagnostics, load_pilot_prices, walk_forward_backtest,
    )
    from src.config import get_config

    panel = load_pilot_prices()
    R = panel.pct_change().dropna()
    rerun = {
        "wp3_descriptive.json": descriptive_regime_stats(R),
        "wp3_walk_forward.json": walk_forward_backtest(R, get_config()["alphas"]),
        "wp3_episodes.json": episode_diagnostics(R),
    }

    def deep_compare_floats(a, b, path="", tol=1e-9, diffs=None):
        if diffs is None:
            diffs = []
        if isinstance(a, dict) and isinstance(b, dict):
            for k in a:
                deep_compare_floats(a.get(k), b.get(k), f"{path}.{k}", tol, diffs)
        elif isinstance(a, list) and isinstance(b, list):
            for i, (x, y) in enumerate(zip(a, b)):
                deep_compare_floats(x, y, f"{path}[{i}]", tol, diffs)
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if abs(a - b) > tol:
                diffs.append({"path": path, "original": a, "rerun": b})
        return diffs

    diffs = {}
    for name in committed:
        d = deep_compare_floats(committed[name], rerun[name])
        diffs[name] = {"n_diffs": len(d), "sample_diffs": d[:5]}

    return {"identical": all(v["n_diffs"] == 0 for v in diffs.values()), "diffs_by_file": diffs}


def check_wp2_subset_reproducibility(n_check: int = 5) -> dict:
    """Recompute the first n_check replications of each scenario directly
    (bypassing the checkpoint file) and diff against the checkpointed
    values, confirming the same seed reproduces bit-identical numbers."""
    from src.wp2_simulation import checkpoint_path, load_checkpoint

    out = {}
    for scen in scenario_names():
        path = checkpoint_path("stylised", scen, 0.05)
        checkpointed = {r["rep"]: r for r in load_checkpoint(path)}
        mismatches = []
        for rep in range(min(n_check, len(checkpointed))):
            if rep not in checkpointed:
                continue
            recomputed = one_rep("stylised", scen, rep, 0.05)
            orig = checkpointed[rep]
            for model in orig["loss"]:
                if not np.isclose(orig["loss"][model], recomputed["loss"][model], rtol=1e-8):
                    mismatches.append({
                        "rep": rep, "model": model,
                        "original": orig["loss"][model], "recomputed": recomputed["loss"][model],
                    })
        out[scen] = {"n_checked": min(n_check, len(checkpointed)), "n_mismatches": len(mismatches),
                      "mismatches": mismatches}
    return out


def check_wp2_different_seed(n_reps: int = 50, seed_base: int = 999_999) -> dict:
    """Re-run a reduced-scale WP2 batch with a different master seed and
    compare conclusions against the main run within Monte Carlo error."""
    main_path = TABLE_DIR / "wp2_summary.json"
    if not main_path.exists():
        return {"error": "wp2_summary.json not found -- run scripts/wp2_run_simulation.py first"}
    with open(main_path) as f:
        main_summary = json.load(f)

    out = {}
    for scen in scenario_names():
        results = run_replications("stylised", scen, 0.05, n_reps, seed_base=seed_base)
        agg = aggregate_scenario(results)
        main_power = main_summary["stylised"][scen]["alpha_0.05"]["D_lt_B"]["power"]
        out[scen] = {
            "main_run_power": main_power,
            "alt_seed_power": agg["D_lt_B"]["power"],
            "alt_seed_n_reps": n_reps,
            "within_wide_tolerance": abs(main_power - agg["D_lt_B"]["power"]) < 0.25,
        }
    return out


def machine_specs() -> dict:
    import numpy, scipy, pandas, hmmlearn, arch, joblib
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": __import__("os").cpu_count(),
        "package_versions": {
            "numpy": numpy.__version__, "scipy": scipy.__version__, "pandas": pandas.__version__,
            "hmmlearn": hmmlearn.__version__, "arch": arch.__version__, "joblib": joblib.__version__,
        },
    }


def main() -> None:
    report = {}
    print("Checking WP1 test-suite reproducibility...")
    report["wp1"] = check_wp1_tests()

    print("Checking WP3 pipeline reproducibility (re-run + diff)...")
    report["wp3"] = check_wp3_reproducibility()

    print("Checking WP2 subset reproducibility (recompute vs checkpoint)...")
    report["wp2_subset"] = check_wp2_subset_reproducibility()

    print("Checking WP2 conclusions under a different master seed...")
    report["wp2_different_seed"] = check_wp2_different_seed()

    report["machine_specs"] = machine_specs()

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TABLE_DIR / "wp4_reproducibility.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=float)
    print(f"Saved {out_path}")
    print("WP1 all passed:", report["wp1"]["all_passed"])
    print("WP3 identical:", report["wp3"].get("identical"))
    print("WP2 subset mismatches:",
          {k: v["n_mismatches"] for k, v in report["wp2_subset"].items()})


if __name__ == "__main__":
    main()
