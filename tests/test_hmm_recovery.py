"""WP1 correctness tests for src.engine.fit_hmm: recovers simulated 2-state
parameters, and its low-variance-first label ordering stays stable across
repeated fits and warm-started rolling refits."""
from __future__ import annotations

import numpy as np
import pytest

from src.engine import fit_hmm

TRUE_TRANSMAT = np.array([[0.98, 0.02], [0.05, 0.95]])
TRUE_MEANS = np.array([0.0003, -0.0005])
TRUE_SDS = np.array([0.006, 0.018])  # calm, stress


def simulate_2state(T: int, rng: np.random.Generator) -> np.ndarray:
    S = np.empty(T, dtype=int)
    S[0] = 0
    for t in range(1, T):
        p_switch = TRUE_TRANSMAT[S[t - 1], 1 - S[t - 1]]
        S[t] = 1 - S[t - 1] if rng.random() < p_switch else S[t - 1]
    x = rng.normal(TRUE_MEANS[S], TRUE_SDS[S])
    return x


def test_hmm_recovers_simulated_2state_params():
    rng = np.random.default_rng(0)
    x = simulate_2state(8000, rng)
    m = fit_hmm(x, seed=0)

    fitted_sds = np.sqrt(m.covars_.ravel())
    fitted_means = m.means_.ravel()

    # State 0 must be the lower-variance state, by construction of fit_hmm.
    assert fitted_sds[0] < fitted_sds[1]

    assert fitted_sds == pytest.approx(TRUE_SDS, rel=0.3)
    assert fitted_means == pytest.approx(TRUE_MEANS, abs=0.001)
    assert np.diag(m.transmat_) == pytest.approx(np.diag(TRUE_TRANSMAT), abs=0.03)


def test_hmm_label_ordering_stable_across_fits_and_seeds():
    for seed in range(5):
        rng = np.random.default_rng(seed)
        x = simulate_2state(3000, rng)
        m = fit_hmm(x, seed=seed)
        sds = np.sqrt(m.covars_.ravel())
        assert sds[0] < sds[1], f"label flip at seed={seed}"


def test_hmm_label_ordering_stable_across_warm_started_refits():
    rng = np.random.default_rng(1)
    x_full = simulate_2state(1260 + 5 * 63, rng)

    hmm = None
    for t0 in range(1260, len(x_full), 63):
        window = x_full[t0 - 1260:t0]
        hmm = fit_hmm(window, prev=hmm, seed=0)
        sds = np.sqrt(hmm.covars_.ravel())
        assert sds[0] < sds[1], f"label flip during warm-started refit at t0={t0}"
