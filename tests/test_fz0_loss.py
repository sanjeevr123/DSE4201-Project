"""WP1 correctness test: the FZ0 loss (src.engine.fz0) rewards the true VaR/ES
over a deliberately biased pair, on simulated data."""
from __future__ import annotations

import numpy as np

from src.engine import fz0


def test_fz0_true_params_beat_biased():
    rng = np.random.default_rng(0)
    n = 20_000
    mu, sigma, alpha = 0.0, 0.02, 0.05

    y = rng.normal(mu, sigma, n)

    from scipy import stats
    z = stats.norm.ppf(alpha)
    v_true = np.full(n, mu + sigma * z)
    e_true = np.full(n, mu - sigma * stats.norm.pdf(z) / alpha)

    # Deliberately biased: VaR shifted toward zero (understates risk) and a
    # mismatched (too-small) ES magnitude.
    v_biased = v_true * 0.5
    e_biased = e_true * 0.5

    loss_true = fz0(y, v_true, e_true, alpha).mean()
    loss_biased = fz0(y, v_biased, e_biased, alpha).mean()

    assert loss_true < loss_biased
