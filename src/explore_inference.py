"""
Inference tools for the exploratory phase: Giacomini-White conditional predictive-ability test and a helper
for the SPA / model-confidence-set family tests (arch package).

Giacomini & White (2006): for one-step forecasts, H0: E[d_t | F_{t-1}] = 0 where d_t is the loss difference. With
instruments h_{t-1} (q x 1), Z_t = h_{t-1} d_t and the statistic is T * Zbar' Omega^{-1} Zbar ~ chi2(q), Omega a
Newey-West long-run variance of Z_t. With h = 1 this is the unconditional Diebold-Mariano test (squared).
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def _nw_lrv(Z: np.ndarray, lags: int) -> np.ndarray:
    T = Z.shape[0]
    Zc = Z - Z.mean(axis=0)
    S = Zc.T @ Zc / T
    for L in range(1, lags + 1):
        G = Zc[L:].T @ Zc[:-L] / T
        S += (1 - L / (lags + 1)) * (G + G.T)
    return S


def gw_test(d: np.ndarray, H: np.ndarray, lags: int | None = None) -> dict:
    """Conditional predictive ability. d: (T,) loss differences (negative = first model better);
    H: (T, q) instruments, each row known at t-1 (the caller must lag them). Returns the chi2 statistic,
    its p-value and the OLS coefficients of d on H (sign shows WHEN the first model is better)."""
    d, H = np.asarray(d, float), np.asarray(H, float)
    if H.ndim == 1:
        H = H[:, None]
    T, q = H.shape
    if lags is None:
        lags = int(np.floor(4 * (T / 100) ** (2 / 9)))
    Z = H * d[:, None]
    zbar = Z.mean(axis=0)
    omega = _nw_lrv(Z, lags)
    stat = float(T * zbar @ np.linalg.solve(omega, zbar))
    beta = np.linalg.lstsq(H, d, rcond=None)[0]
    return {"stat": stat, "df": q, "p": float(1 - stats.chi2.cdf(stat, q)), "coef": beta}
