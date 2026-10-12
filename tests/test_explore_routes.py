"""Tests for src/explore_routes.py (Kendall matrix, pair variant, t-mixture, no look-ahead of margins)."""
import numpy as np
from scipy import stats

from src.engine import t_var_es, mix_var_es
from src.explore_routes import (garch_filter, make_variants_fn, mix_var_es_t, nearest_corr,
                                pair_variant, weighted_kendall_corr)


def _gauss(n=4000, rho=0.5, seed=0):
    rng = np.random.default_rng(seed)
    C = np.array([[1, rho, -0.3], [rho, 1, 0.1], [-0.3, 0.1, 1.0]])
    return rng.standard_normal((n, 3)) @ np.linalg.cholesky(C).T, C


def test_kendall_recovers_correlation():
    X, C = _gauss(3000)
    R = weighted_kendall_corr(X, np.ones(len(X)))
    assert np.max(np.abs(R - C)) < 0.05
    assert np.all(np.linalg.eigvalsh(R) > 0)


def test_kendall_is_robust_to_outliers():
    X, C = _gauss(1500)
    Xo = X.copy()
    Xo[:10, 0] = 50.0       # gross outliers in asset 0
    Xo[:10, 1] = -50.0
    sample = np.corrcoef(Xo, rowvar=False)[0, 1]
    kend = weighted_kendall_corr(Xo, np.ones(len(Xo)))[0, 1]
    assert abs(kend - C[0, 1]) < 0.1 < abs(sample - C[0, 1])


def test_kendall_weights_concentrate_on_subsample():
    X, _ = _gauss(2000)
    X2 = np.vstack([X, X[:, [0, 1, 2]] * np.array([1, -1, 1])])   # second half: asset-1 sign flipped
    w = np.r_[np.ones(2000), 1e-9 * np.ones(2000)]
    R = weighted_kendall_corr(X2, w)
    R_first = weighted_kendall_corr(X, np.ones(2000))
    assert np.max(np.abs(R - R_first)) < 1e-3


def test_nearest_corr_repairs_indefinite():
    R = np.array([[1, 0.9, -0.9], [0.9, 1, 0.9], [-0.9, 0.9, 1.0]])   # not PSD
    assert np.linalg.eigvalsh(R).min() < 0
    F = nearest_corr(R)
    assert np.linalg.eigvalsh(F).min() > 0 and np.allclose(np.diag(F), 1)


def test_pair_variant_only_changes_that_pair():
    Rp = np.array([[1, -0.3, 0.1], [-0.3, 1, 0.2], [0.1, 0.2, 1.0]])
    Rk = np.array([[1, 0.3, 0.5], [0.3, 1, -0.4], [0.5, -0.4, 1.0]])
    V = pair_variant(Rp, Rk, (0, 1))
    assert np.isclose(V[0, 1], 0.3)
    assert np.isclose(V[0, 2], Rp[0, 2]) and np.isclose(V[1, 2], Rp[1, 2])


def test_variants_D_P_equals_B_when_regimes_identical():
    X, _ = _gauss(1500)
    gamma = np.c_[np.full(len(X), 0.5), np.full(len(X), 0.5)]    # both regimes = whole sample
    covs, _ = make_variants_fn((0, 1))(X, gamma)
    for k in range(2):
        assert np.allclose(covs["D_P"][k], covs["B"][k], atol=1e-8)
        assert np.allclose(covs["D"][k], covs["B"][k], atol=1e-8)


def test_t_mixture_single_component_matches_t_var_es():
    for nu in (4.0, 8.0):
        q, es = mix_var_es_t(np.array([1.0]), np.array([0.001]), np.array([0.012]), nu, 0.025)
        q0, es0 = t_var_es(0.001, 0.012, nu, 0.025)
        assert np.isclose(q, q0, rtol=1e-8) and np.isclose(es, es0, rtol=1e-8)


def test_t_mixture_matches_monte_carlo():
    rng = np.random.default_rng(1)
    p, mu, s, nu, a = np.array([0.7, 0.3]), np.array([0.0005, -0.002]), np.array([0.008, 0.02]), 6.0, 0.05
    n = 2_000_000
    st = rng.random(n) < p[1]
    x = np.where(st, mu[1] + s[1] * np.sqrt((nu - 2) / nu) * rng.standard_t(nu, n),
                 mu[0] + s[0] * np.sqrt((nu - 2) / nu) * rng.standard_t(nu, n))
    q, es = mix_var_es_t(p, mu, s, nu, a)
    qm = np.quantile(x, a)
    assert abs(q - qm) < 5e-4 and abs(es - x[x <= qm].mean()) < 1e-3


def test_garch_filter_uses_only_past():
    rng = np.random.default_rng(2)
    X = rng.standard_normal((300, 2)) * 0.01
    params = (np.zeros(2), np.full(2, 0.05), np.full(2, 0.08), np.full(2, 0.9))
    init = np.full(2, 1.0)
    _, s_a = garch_filter(X, params, init)
    X2 = X.copy(); X2[-1] *= 10          # change only the last day
    _, s_b = garch_filter(X2, params, init)
    assert np.allclose(s_a[:-1], s_b[:-1])         # variances for days <= last are unaffected
    assert not np.allclose(s_a[-1], s_b[-1])       # the next-day variance does react
