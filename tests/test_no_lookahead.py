"""WP1 correctness tests: forecasts at day t must never depend on data after t.

Two levels: a fast primitive-level test on filtered_probs(), and a full
end-to-end test on walk_forward() perturbing returns strictly after t.
"""
from __future__ import annotations

import numpy as np

from src.engine import fit_hmm, filtered_probs, walk_forward


def test_filtered_probs_unchanged_by_future_data():
    rng = np.random.default_rng(0)
    x_full = rng.normal(0, 0.01, 2000)
    m = fit_hmm(x_full[:1260], seed=0)
    p0 = np.array([0.5, 0.5])

    t = 500
    filt_short, pred_short = filtered_probs(m, x_full[:t + 1], p0)
    filt_long, pred_long = filtered_probs(m, x_full[:t + 200], p0)

    assert np.allclose(filt_short, filt_long[:t + 1])
    assert np.allclose(pred_short, pred_long[:t + 1])


def _simulate_3asset(T: int, rng: np.random.Generator) -> np.ndarray:
    S = np.empty(T, dtype=int)
    S[0] = 0
    P = np.array([[0.98, 0.02], [0.05, 0.95]])
    for t in range(1, T):
        S[t] = 1 - S[t - 1] if rng.random() < P[S[t - 1], 1 - S[t - 1]] else S[t - 1]
    vols = np.where(S[:, None] == 0, [0.006, 0.003, 0.007], [0.018, 0.005, 0.014])
    R = rng.normal(0, 1, (T, 3)) * vols
    return R


def test_walk_forward_forecasts_unchanged_by_future_perturbation():
    rng = np.random.default_rng(0)
    T = 1260 + 200
    R = _simulate_3asset(T, rng)
    w = np.ones(3) / 3

    res_base = walk_forward(R, w, start=1260, window=1260, refit=21, alpha=0.05, seed=0)

    t_cut = 1260 + 100
    R_perturbed = R.copy()
    R_perturbed[t_cut + 1:] += 0.5  # large shock (50 vols), strictly after t_cut

    res_perturbed = walk_forward(R_perturbed, w, start=1260, window=1260, refit=21,
                                  alpha=0.05, seed=0)

    # idx runs from `start`; forecasts up to and including t_cut must be identical.
    cutoff_pos = t_cut - res_base["idx"][0] + 1
    for model in res_base["V"]:
        v_base = res_base["V"][model][:cutoff_pos]
        v_pert = res_perturbed["V"][model][:cutoff_pos]
        assert np.allclose(v_base, v_pert, equal_nan=True), f"look-ahead leak in {model} VaR"
        e_base = res_base["E"][model][:cutoff_pos]
        e_pert = res_perturbed["E"][model][:cutoff_pos]
        assert np.allclose(e_base, e_pert, equal_nan=True), f"look-ahead leak in {model} ES"

    assert np.allclose(
        res_base["stress_prob"][:cutoff_pos],
        res_perturbed["stress_prob"][:cutoff_pos],
    )
