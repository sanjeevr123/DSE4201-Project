"""
WP2 simulation power study: can the pilot design detect the correlation-
breakdown effect at all, given ~10 years of daily data?

Each replication simulates a full walk-forward backtest from the DGP in
src/dgp.py, scores it, and records per-model loss/hit/Kupiec plus the D-B
and Oracle_D-Oracle_B Diebold-Mariano tests. Replications are run in
parallel with joblib and checkpointed to a JSONL file as each one completes,
so a crash mid-run does not lose completed replications, and a re-run skips
any replication already recorded.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
from joblib import Parallel, delayed

from src.config import get_config
from src.dgp import get_dgp_params, simulate
from src.engine import walk_forward, score

REPO_ROOT = Path(__file__).resolve().parents[1]
W = np.ones(3) / 3

EXTRA_PAIRS = (
    ("Oracle_D", "Oracle_B"),
    ("B", "EWMA_MV"), ("D", "EWMA_MV"),
    ("B", "EWMA"), ("D", "EWMA"),
    ("D", "HS"),
)


def scenario_names() -> list[str]:
    return list(get_config()["wp2"]["scenarios"].keys())


def _rep_seed(scenario: str, rep: int, dgp_name: str, seed_base: int) -> int:
    scen_idx = scenario_names().index(scenario)
    dgp_offset = 0 if dgp_name == "stylised" else 500_000
    return seed_base + dgp_offset + 10_000 * scen_idx + rep


def one_rep(dgp_name: str, scenario: str, rep: int, alpha: float,
            T: Optional[int] = None, seed_base: int = 0) -> dict:
    cfg = get_config()
    wp2 = cfg["wp2"]
    T = T or (wp2["burn_in"] + wp2["test_days"])
    burn_in = wp2["burn_in"]

    params = get_dgp_params(dgp_name)
    stress_corr_pairs = wp2["scenarios"][scenario]
    from src.dgp import corr_matrix
    stress_corr = corr_matrix(*stress_corr_pairs)

    seed = _rep_seed(scenario, rep, dgp_name, seed_base)
    rng = np.random.default_rng(seed)
    R, S, pred, true_covs = simulate(params, stress_corr, T, rng)

    res = walk_forward(R, W, start=burn_in, window=burn_in, alpha=alpha,
                        true_pred=pred, true_covs=true_covs, seed=rep)
    from src.engine import DEFAULT_DM_PAIRS
    sc = score(res, alpha, pairs=DEFAULT_DM_PAIRS + EXTRA_PAIRS)

    s_true = S[res["idx"]]
    regime_acc = float(np.mean((res["stress_prob"] > 0.5) == s_true))
    stress_share = float(s_true.mean())

    return dict(
        dgp=dgp_name, scen=scenario, rep=rep, alpha=alpha, T=T,
        loss=sc["loss"], hit=sc["hit"], kupiec_p=sc["kupiec_p"],
        dm={k: list(v) for k, v in sc["dm"].items()},
        regime_acc=regime_acc, stress_share=stress_share,
    )


def checkpoint_path(dgp_name: str, scenario: str, alpha: float, T: Optional[int] = None) -> Path:
    cfg = get_config()
    ckdir = REPO_ROOT / cfg["wp2"]["checkpoint_dir"]
    ckdir.mkdir(parents=True, exist_ok=True)
    suffix = f"_T{T}" if T is not None else ""
    return ckdir / f"{dgp_name}_{scenario}_alpha{alpha}{suffix}.jsonl"


def load_checkpoint(path: Path) -> list[dict]:
    if not path.exists():
        return []
    results = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def run_replications(dgp_name: str, scenario: str, alpha: float, n_reps: int,
                      T: Optional[int] = None, seed_base: int = 0,
                      n_jobs: int = -1) -> list[dict]:
    """Run replications 0..n_reps-1, resuming from any already-checkpointed
    replications, writing each new result to the checkpoint file as soon as
    it completes."""
    path = checkpoint_path(dgp_name, scenario, alpha, T)
    existing = load_checkpoint(path)
    done_reps = {r["rep"] for r in existing}
    todo = [r for r in range(n_reps) if r not in done_reps]

    if todo:
        gen = Parallel(n_jobs=n_jobs, return_as="generator")(
            delayed(one_rep)(dgp_name, scenario, r, alpha, T, seed_base) for r in todo
        )
        with open(path, "a") as f:
            for result in gen:
                f.write(json.dumps(result, default=float) + "\n")
                f.flush()

    return load_checkpoint(path)


def binomial_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Normal-approximation binomial confidence interval for a proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    se = np.sqrt(p * (1 - p) / n)
    return (max(0.0, p - z * se), min(1.0, p + z * se))


def aggregate_scenario(results: list[dict], dm_alpha: float = 0.05) -> dict:
    """Aggregate one scenario's replications into the WP2 report metrics."""
    n = len(results)
    z_crit = 1.6448536269514722  # one-sided 5% normal critical value

    def one_sided_power(pair_key: str) -> dict:
        ts = [r["dm"][pair_key][0] for r in results if pair_key in r["dm"]]
        n_valid = len(ts)
        rejects_favoring_first = sum(1 for t in ts if t < -z_crit)
        wrong_sign = sum(1 for t in ts if t > z_crit)
        power_lo, power_hi = binomial_ci(rejects_favoring_first, n_valid)
        return {
            "n": n_valid,
            "power": rejects_favoring_first / n_valid if n_valid else float("nan"),
            "power_ci95": [power_lo, power_hi],
            "wrong_sign_rate": wrong_sign / n_valid if n_valid else float("nan"),
        }

    models = list(results[0]["loss"].keys()) if results else []
    mean_loss = {m: float(np.mean([r["loss"][m] for r in results])) for m in models}
    mean_hit = {m: float(np.mean([r["hit"][m] for r in results])) for m in models}
    kupiec_rejection_rate = {
        m: float(np.mean([r["kupiec_p"][m] < 0.05 for r in results])) for m in models
    }

    d_minus_b = [r["loss"]["D"] - r["loss"]["B"] for r in results if "D" in r["loss"] and "B" in r["loss"]]
    mean_fz0_diff_D_B = float(np.mean(d_minus_b)) if d_minus_b else float("nan")
    se_fz0_diff_D_B = float(np.std(d_minus_b, ddof=1) / np.sqrt(len(d_minus_b))) if len(d_minus_b) > 1 else float("nan")

    beats_benchmark = {}
    for regime_model in ["A", "B", "C", "D"]:
        for benchmark in ["GARCHt", "EWMA_MV"]:
            key = f"{regime_model}-{benchmark}"
            if key in results[0]["dm"]:
                beats_benchmark[key] = one_sided_power(key)["power"]

    return {
        "n_reps": n,
        "D_lt_B": one_sided_power("D-B"),
        "oracle_D_lt_B": one_sided_power("Oracle_D-Oracle_B") if results and "Oracle_D-Oracle_B" in results[0]["dm"] else None,
        "mean_fz0_diff_D_minus_B": mean_fz0_diff_D_B,
        "se_fz0_diff_D_minus_B": se_fz0_diff_D_B,
        "regime_classification_accuracy": float(np.mean([r["regime_acc"] for r in results])) if results else float("nan"),
        "mean_stress_share": float(np.mean([r["stress_share"] for r in results])) if results else float("nan"),
        "mean_hit_rate": mean_hit,
        "mean_fz0_loss": mean_loss,
        "kupiec_rejection_rate": kupiec_rejection_rate,
        "beats_benchmark_power": beats_benchmark,
    }
