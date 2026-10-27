"""
Data-generating process with GARCH dynamics for the power study of the GARCH-margin layer
(docs/decisions_log.md, "GARCH-DGP power study"). The pilot DGP (src/dgp.py) has regime-switching volatility
and correlation but constant covariance inside each regime, so it cannot say anything about the power of
models whose margins are GARCH.

Per asset i, with S_t a 2-state Markov chain (same transition matrix as the pilot's stylised DGP):
    r_it = m_{i,S_t} * h_it * z_it ,   h_it^2 = omega_i + a * u_{i,t-1}^2 + b * h_{i,t-1}^2 ,
    u_{i,t-1} = r_{i,t-1} / m_{i,S_{t-1}}      (the regime-scaled return, so GARCH feeds on shocks net of the
                                                 regime's volatility level),
    z_t ~ unit-variance multivariate Student-t (df) with correlation matrix R_{S_t}.
m_{i,calm} = 1 and m_{i,stress} = vol_stress_i / vol_calm_i; omega_i is set so the calm-regime unconditional
volatility of asset i equals vol_calm_i. Scenarios S0-S3 supply the stress correlation, exactly as in the pilot.
GARCH parameters (a, b) are stylised and fixed in config/pilot.yaml (wp2_garch); they are assumptions, not estimates.
"""
from __future__ import annotations

import numpy as np

from src.dgp import DGPParams, cov_matrix


def simulate_garch_rs(params: DGPParams, stress_corr: np.ndarray, T: int, rng: np.random.Generator,
                      a: float = 0.08, b: float = 0.90) -> tuple[np.ndarray, np.ndarray]:
    """Simulate T days. Returns (R, S): T x 3 returns and the true regime labels (0 calm, 1 stress)."""
    P = params.transmat
    S = np.empty(T, dtype=int)
    S[0] = 0
    for t in range(1, T):
        S[t] = rng.random() < P[S[t - 1], 1]
    vol_c, vol_s = np.asarray(params.vol_calm), np.asarray(params.vol_stress)
    mult = np.vstack([np.ones_like(vol_c), vol_s / vol_c])          # (2, N)
    omega = (1 - a - b) * vol_c ** 2
    L = [np.linalg.cholesky(c) for c in (cov_matrix(np.ones(3), params.calm_corr),
                                         cov_matrix(np.ones(3), stress_corr))]
    N = len(vol_c)
    z = rng.standard_normal((T, N))
    g = rng.chisquare(params.df, T) / params.df
    z = z / np.sqrt(g)[:, None] * np.sqrt((params.df - 2) / params.df)
    for k in (0, 1):
        m = S == k
        z[m] = z[m] @ L[k].T
    R = np.empty((T, N))
    h2 = vol_c ** 2
    for t in range(T):
        R[t] = mult[S[t]] * np.sqrt(h2) * z[t]
        u = R[t] / mult[S[t]]
        h2 = omega + a * u ** 2 + b * h2
    return R, S
