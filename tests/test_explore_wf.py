"""No-look-ahead and sanity tests for the generalised exploratory walk-forward
(src/explore_wf.py): perturbing returns/signals strictly after day t_cut must not
change any forecast made for days <= t_cut, for every regime provider and for
the DCC-GARCH / GARCH-t / EWMA / HS benchmarks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.explore_wf import (
    HMMProvider,
    RuleProvider,
    fit_dcc,
    run_benchmarks,
    run_regime_models,
)

START, T, T_CUT = 1260, 1260 + 130, 1260 + 60
ALPHAS = (0.05,)


def _data(rng):
    S = np.zeros(T, dtype=int)
    for t in range(1, T):
        S[t] = 1 - S[t - 1] if rng.random() < (0.02 if S[t - 1] == 0 else 0.06) else S[t - 1]
    vols = np.where(S[:, None] == 0, [0.006, 0.003, 0.007], [0.018, 0.005, 0.014])
    R = rng.normal(0, 1, (T, 3)) * vols
    vix = 12 + 25 * S + rng.normal(0, 2, T)
    return R, vix


def _providers(R, vix):
    spy = R[:, 0]
    rv = pd.Series(spy).rolling(21).std().values
    cr = pd.Series(R[:, 0]).rolling(63).corr(pd.Series(R[:, 1])).values
    return [
        HMMProvider("h2", spy, K=2),
        HMMProvider("h3", spy, K=3),
        HMMProvider("hv", np.c_[spy * 100, np.log(np.clip(vix, 5, None))], K=2),
        RuleProvider("vix", vix, thr=20.0),
        RuleProvider("rv", rv, q=0.75),
        RuleProvider("cr", cr, q=2 / 3),
    ]


def _same(a, b, cut):
    return np.allclose(a[:cut], b[:cut], equal_nan=True)


def test_regime_providers_have_no_lookahead():
    rng = np.random.default_rng(1)
    R, vix = _data(rng)
    w = np.ones(3) / 3
    R2, vix2 = R.copy(), vix.copy()
    R2[T_CUT + 1:] += 0.4
    vix2[T_CUT + 1:] += 40
    for p1, p2 in zip(_providers(R, vix), _providers(R2, vix2)):
        a = run_regime_models(R, w, p1, ALPHAS, START)
        b = run_regime_models(R2, w, p2, ALPHAS, START)
        for m in ("A", "B", "C", "D"):
            assert _same(a["V"][0.05][m], b["V"][0.05][m], T_CUT + 1), f"{p1.name}/{m} VaR leak"
            assert _same(a["E"][0.05][m], b["E"][0.05][m], T_CUT + 1), f"{p1.name}/{m} ES leak"
        assert _same(a["stress_prob"], b["stress_prob"], T_CUT + 1), f"{p1.name} stress leak"


def test_benchmarks_have_no_lookahead():
    rng = np.random.default_rng(2)
    R, _ = _data(rng)
    w = np.ones(3) / 3
    R2 = R.copy()
    R2[T_CUT + 1:] += 0.4
    a = run_benchmarks(R, w, ALPHAS, START)
    b = run_benchmarks(R2, w, ALPHAS, START)
    for m in a["V"][0.05]:
        assert _same(a["V"][0.05][m], b["V"][0.05][m], T_CUT + 1), f"{m} VaR leak"
        assert _same(a["E"][0.05][m], b["E"][0.05][m], T_CUT + 1), f"{m} ES leak"


def test_dcc_recovers_constant_correlation_and_forecasts_are_finite():
    rng = np.random.default_rng(3)
    C = np.array([[1, .6, 0], [.6, 1, 0], [0, 0, 1.0]])
    X = rng.normal(0, 1, (1260, 3)) @ np.linalg.cholesky(C).T * 0.01
    d = fit_dcc(X, np.ones(3) / 3)
    assert d["a"] + d["b"] < 0.9995
    assert abs(d["Qbar"][0, 1] - 0.6) < 0.08
    assert np.all(np.isfinite(d["sig2"])) and 2.2 <= d["nu"] <= 60


def test_rule_provider_state_probs_valid():
    rng = np.random.default_rng(4)
    sig = rng.normal(size=1500)
    p = RuleProvider("r", sig, q=0.75)
    gamma, preds = p.step(slice(0, 1260), slice(1260, 1281))
    assert np.allclose(gamma.sum(1), 1) and np.allclose(preds.sum(1), 1)
    assert (preds >= 0).all()
