"""WP1 correctness tests for the mean-aware normal-mixture VaR/ES (src.engine.mix_var_es)."""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from src.config import get_config
from src.engine import mix_var_es

MC_DRAWS = get_config()["wp1_tests"]["mc_draws"]
MC_TOL = get_config()["wp1_tests"]["mc_tolerance"]


@pytest.mark.parametrize("alpha", [0.05, 0.025])
@pytest.mark.parametrize(
    "p,mu,s",
    [
        (np.array([0.7, 0.3]), np.array([0.0, 0.0]), np.array([0.01, 0.03])),
        (np.array([0.5, 0.5]), np.array([0.0005, -0.002]), np.array([0.008, 0.02])),
        (np.array([0.2, 0.8]), np.array([-0.001, 0.0015]), np.array([0.015, 0.006])),
    ],
)
def test_mixture_var_es_matches_monte_carlo(p, mu, s, alpha):
    rng = np.random.default_rng(0)
    component = rng.choice(len(p), size=MC_DRAWS, p=p)
    draws = rng.normal(mu[component], s[component])

    q, es = mix_var_es(p, mu, s, alpha)

    mc_var = np.quantile(draws, alpha)
    mc_es = draws[draws <= mc_var].mean()

    assert q == pytest.approx(mc_var, rel=MC_TOL, abs=1e-3)
    assert es == pytest.approx(mc_es, rel=MC_TOL, abs=1e-3)


@pytest.mark.parametrize("alpha", [0.05, 0.025, 0.01])
@pytest.mark.parametrize("mu_common", [0.0, 0.001, -0.0007])
def test_mixture_identical_components_reproduces_normal(alpha, mu_common):
    p = np.array([0.5, 0.5])
    mu = np.array([mu_common, mu_common])
    s = np.array([0.015, 0.015])

    q, es = mix_var_es(p, mu, s, alpha)

    z = stats.norm.ppf(alpha)
    q_true = mu_common + s[0] * z
    es_true = mu_common - s[0] * stats.norm.pdf(z) / alpha

    assert q == pytest.approx(q_true, abs=1e-10)
    assert es == pytest.approx(es_true, abs=1e-10)
