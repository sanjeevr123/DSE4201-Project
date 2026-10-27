"""Tests for src/explore_ladder.py (mean-mode control, regime-mode reproduction, no look-ahead)."""
import numpy as np
from scipy import stats

from src.explore_ladder import ladder_names, mean_arrays, run_static_ladder
from src.explore_wf import RuleProvider, run_regime_models


def _data(T=700, seed=1):
    rng = np.random.default_rng(seed)
    sig = np.where((np.arange(T) // 150) % 2 == 0, 0.007, 0.018)
    X = rng.standard_normal((T, 3)) * sig[:, None] * np.array([1.0, 0.4, 0.9]) + 0.0003
    return X, sig


def test_mean_arrays():
    mk = [np.array([0.1, 0.2]), np.array([-0.3, 0.4])]
    pooled = np.array([0.0, 0.1])
    assert all(np.array_equal(a, b) for a, b in zip(mean_arrays("regime", mk, pooled), mk))
    assert all(np.array_equal(a, pooled) for a in mean_arrays("pooled", mk, pooled))
    assert all(not a.any() for a in mean_arrays("zero", mk, pooled))


def test_ladder_names_have_no_regime_mean_for_pooled_model():
    names = ladder_names()
    assert "A|regime|N" not in names and "B|regime|N" in names and "D|zero|t" in names


def test_regime_mode_reproduces_original_gaussian_bd():
    X, sig = _data()
    w = np.ones(3) / 3
    prov = lambda: RuleProvider("rv", sig, q=0.75)
    ref = run_regime_models(X, w, prov(), (0.05,), 400, window=300, refit=21, models=("A", "B", "D"))
    new = run_static_ladder(X, w, prov(), (0.05,), 400, window=300, refit=21)
    for m in ("B", "D"):
        assert np.allclose(new["V"][0.05][f"{m}|regime|N"][400:], ref["V"][0.05][m][400:], atol=1e-10)
        assert np.allclose(new["E"][0.05][f"{m}|regime|N"][400:], ref["E"][0.05][m][400:], atol=1e-10)


def test_pooled_mean_makes_regime_means_irrelevant():
    """With one pooled mean in both regimes and a common covariance, B|pooled and A|pooled coincide in
    location; with zero mean the Gaussian VaR is exactly -z_alpha * sd for a single-covariance model."""
    X, sig = _data()
    w = np.ones(3) / 3
    r = run_static_ladder(X, w, RuleProvider("rv", sig, q=0.75), (0.05,), 400, window=300, refit=21)
    v0 = r["V"][0.05]["A|zero|N"][400:]
    assert np.all(v0 < 0)
    # A has one covariance in both states: zero-mean VaR is a pure normal quantile
    # the covariance is refit every 21 days, so the first block (days 400-420) uses window [100, 400)
    sd = np.std(X[100:400] @ w, ddof=1)
    assert np.allclose(v0[:21], stats.norm.ppf(0.05) * sd, rtol=2e-3)
    assert np.allclose(v0[:21], v0[0])


def test_no_lookahead_future_returns_do_not_change_forecasts():
    X, sig = _data()
    w = np.ones(3) / 3
    a = run_static_ladder(X, w, RuleProvider("rv", sig, q=0.75), (0.05,), 400, window=300, refit=21)
    X2 = X.copy()
    X2[600:] *= 5.0             # perturb returns from day 600; forecasts before it must be unchanged
    b = run_static_ladder(X2, w, RuleProvider("rv", sig, q=0.75), (0.05,), 400, window=300, refit=21)
    for k in ("B|pooled|t", "D|zero|N"):
        assert np.allclose(a["V"][0.05][k][400:600], b["V"][0.05][k][400:600], atol=1e-12)
