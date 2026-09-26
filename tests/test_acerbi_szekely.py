"""WP1 correctness test: the Acerbi-Szekely Z2 statistic (src.engine.acerbi_szekely_z2)
is approximately 0 under a correctly specified model."""
from __future__ import annotations

import numpy as np
from scipy import stats

from src.engine import acerbi_szekely_z2


def test_z2_approximately_zero_under_correct_model():
    rng = np.random.default_rng(0)
    n = 50_000
    mu, sigma, alpha = 0.0, 0.02, 0.05

    y = rng.normal(mu, sigma, n)
    z = stats.norm.ppf(alpha)
    v = np.full(n, mu + sigma * z)
    e = np.full(n, mu - sigma * stats.norm.pdf(z) / alpha)

    z2 = acerbi_szekely_z2(y, v, e, alpha)

    # Z2's asymptotic null variance is O(1), so with n=50k a generous but
    # non-trivial tolerance avoids flakiness while still catching a broken
    # implementation (which would be off by an order of magnitude or more).
    assert abs(z2) < 0.15


def test_z2_flags_understated_es():
    rng = np.random.default_rng(1)
    n = 50_000
    mu, sigma, alpha = 0.0, 0.02, 0.05

    y = rng.normal(mu, sigma, n)
    z = stats.norm.ppf(alpha)
    v = np.full(n, mu + sigma * z)
    e_understated = np.full(n, (mu - sigma * stats.norm.pdf(z) / alpha) * 0.3)

    z2 = acerbi_szekely_z2(y, v, e_understated, alpha)

    assert abs(z2) > 0.5
