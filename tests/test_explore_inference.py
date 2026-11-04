"""Tests for the Giacomini-White conditional predictive-ability test."""
import numpy as np

from src.engine import dm_test
from src.explore_inference import gw_test


def test_gw_has_roughly_correct_size_under_the_null():
    rng = np.random.default_rng(0)
    rej = 0
    for _ in range(400):
        x = rng.standard_normal(1500)
        d = rng.standard_normal(1500)
        H = np.c_[np.ones(1500), np.r_[0.0, x[:-1]]]
        rej += gw_test(d, H)["p"] < 0.05
    assert 0.02 < rej / 400 < 0.09


def test_gw_detects_a_conditional_effect_that_dm_misses():
    rng = np.random.default_rng(1)
    T = 3000
    x = rng.standard_normal(T)
    d = 0.4 * np.r_[0.0, x[:-1]] + rng.standard_normal(T)          # mean zero, but depends on x_{t-1}
    H = np.c_[np.ones(T), np.r_[0.0, x[:-1]]]
    out = gw_test(d, H)
    assert out["p"] < 1e-6 and abs(out["coef"][1] - 0.4) < 0.1
    assert dm_test(d, np.zeros(T))[1] > 0.01                        # unconditional DM sees nothing


def test_gw_with_constant_instrument_matches_dm():
    rng = np.random.default_rng(2)
    d = rng.standard_normal(2000) + 0.05
    g = gw_test(d, np.ones((2000, 1)))
    t, p = dm_test(d, np.zeros(2000))
    assert abs(g["p"] - p) < 0.02 and abs(g["stat"] - t ** 2) < 0.2
