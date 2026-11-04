"""
Static-covariance ladder rungs with controlled mean treatment and Student-t components
(docs/decisions_log.md, "Ladder / equal-mean control").

The earlier contrast "GARCH margins vs static regime covariance" (RSC vs D) also changed the mean:
static arms used regime-specific means, GARCH arms one constant mean. Here the static arms (A, B, D)
are re-run with the mean held fixed across regimes ("pooled") or set to zero ("zero"), so that
the only difference to the GARCH-margin arms is how volatility is modelled. "regime" reproduces the
original Gaussian B/D bit for bit (validation in scripts/explore_13_ladder.py).

Exploration only: everything stays <= 2019-12-31. Same no-look-ahead discipline as src/explore_wf.py.
"""
from __future__ import annotations

import numpy as np

from src.engine import mix_var_es
from src.explore_routes import mix_var_es_t
from src.explore_wf import build_variants_k, fit_t_df

MEAN_MODES = ("regime", "pooled", "zero")
DISTS = ("N", "t")


def mean_arrays(mode: str, means_k: list[np.ndarray], pooled_mean: np.ndarray) -> list[np.ndarray]:
    """Per-state asset mean vectors under a mean treatment."""
    K = len(means_k)
    if mode == "regime":
        return list(means_k)
    if mode == "pooled":
        return [pooled_mean] * K
    if mode == "zero":
        return [np.zeros_like(pooled_mean)] * K
    raise ValueError(mode)


def ladder_names(models=("A", "B", "D"), mean_modes=MEAN_MODES) -> list[str]:
    """Forecast keys 'MODEL|MEANMODE|DIST'. A is pooled by construction, so it has no 'regime' mode."""
    out = []
    for m in models:
        for mode in mean_modes:
            if m == "A" and mode == "regime":
                continue
            out += [f"{m}|{mode}|{d}" for d in DISTS]
    return out


def _in_window_nu(rp: np.ndarray, gamma: np.ndarray, sd: np.ndarray, mu: np.ndarray) -> float:
    """df of a unit-variance Student-t fitted to portfolio returns standardised by the in-window
    regime-probability-weighted mixture mean and sd (smoothed probabilities, window data only)."""
    m = gamma @ mu
    v = gamma @ sd ** 2 + gamma @ mu ** 2 - m ** 2
    return fit_t_df((rp - m) / np.sqrt(v))


def run_static_ladder(R: np.ndarray, w: np.ndarray, provider, alphas, start: int, window: int = 1260,
                      refit: int = 21, models=("A", "B", "D"), mean_modes=MEAN_MODES) -> dict:
    """Walk-forward static-covariance forecasts for every (model, mean mode, distribution).
    Returns {"V": {alpha: {key: array(T)}}, "E": ..., "stress_prob", "nu": {key: {t0: df}}}."""
    T = R.shape[0]
    rp = R @ w
    keys = ladder_names(models, mean_modes)
    V = {a: {k: np.full(T, np.nan) for k in keys} for a in alphas}
    E = {a: {k: np.full(T, np.nan) for k in keys} for a in alphas}
    stress = np.full(T, np.nan)
    nus = {k: {} for k in keys if k.endswith("|t")}
    for t0 in range(start, T, refit):
        t1 = min(t0 + refit, T)
        win, blk = slice(t0 - window, t0), slice(t0, t1)
        gamma, preds = provider.step(win, blk)
        covs, means = build_variants_k(R[win], gamma)
        pooled = means["A"][0]
        for m in models:
            sd = np.array([np.sqrt(w @ S @ w) for S in covs[m]])
            for mode in mean_modes:
                if m == "A" and mode == "regime":
                    continue
                mu = np.array([w @ x for x in mean_arrays(mode, means[m], pooled)])
                nu = _in_window_nu(rp[win], gamma, sd, mu)
                nus[f"{m}|{mode}|t"][t0] = nu
                for i, t in enumerate(range(t0, t1)):
                    p = preds[i]
                    stress[t] = p[-1]
                    for a in alphas:
                        V[a][f"{m}|{mode}|N"][t], E[a][f"{m}|{mode}|N"][t] = mix_var_es(p, mu, sd, a)
                        V[a][f"{m}|{mode}|t"][t], E[a][f"{m}|{mode}|t"][t] = mix_var_es_t(p, mu, sd, nu, a)
    return {"V": V, "E": E, "stress_prob": stress, "nu": nus}
