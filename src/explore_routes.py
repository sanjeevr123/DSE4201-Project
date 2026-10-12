"""
Routes for the dependence-measure comparison (docs: output/FURTHER_EXPLORATION_RESEARCH.md, Section 2).

Route M  - a robust joint estimate of the correlation matrix for all assets: the Kendall's-tau
           rank-correlation matrix, R = sin(pi * tau / 2) (Lindskog, McNeil & Schmock), repaired to a
           valid correlation matrix if needed. Regime probabilities enter as pair weights w_i * w_j.
Route P  - ordinary (sample) correlation, but only ONE pre-chosen pair's correlation switches with the
           regime; every other correlation stays pooled.

Two layers:
  Layer 1  static within-regime covariance, the pilot's A-D framework (regime vols x correlation variant):
           B (pooled corr), D (all pairs switch), B_M / D_M (Kendall), D_P (one pair switches).
  Layer 2  GARCH(1,1) margins + a constant (CCC) or regime-switching (RSC) correlation of the
           GARCH-standardised residuals (Pelletier 2006 style). Same margins in every arm, so only the
           correlation treatment differs. Gaussian (_N) and Student-t (_t) innovations.

Exploration only: everything stays <= 2019-12-31. No look-ahead: the forecast for day t uses data
through t-1 only (margins re-filtered with parameters fitted on the trailing window).
"""
from __future__ import annotations

import numpy as np
from scipy import optimize, stats

from src.engine import corr_from_cov, mix_var_es, weighted_cov
from src.explore_wf import fit_t_df

EPS_EIG = 1e-8


# ------------------------------------------------------------------ estimators
def nearest_corr(R: np.ndarray, eps: float = EPS_EIG) -> np.ndarray:
    """Clip eigenvalues at eps and rescale to a unit diagonal (a valid correlation matrix)."""
    R = (R + R.T) / 2
    vals, vecs = np.linalg.eigh(R)
    if vals.min() >= eps:
        return R
    R2 = (vecs * np.clip(vals, eps, None)) @ vecs.T
    d = 1.0 / np.sqrt(np.diag(R2))
    R2 = R2 * np.outer(d, d)
    np.fill_diagonal(R2, 1.0)
    return R2


def weighted_kendall_corr(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted Kendall's-tau correlation matrix, sin(pi*tau/2), PSD-repaired.

    tau_ij = sum_{s!=t} w_s w_t sgn(x_si - x_ti) sgn(x_sj - x_tj) / sum_{s!=t} w_s w_t,
    so with equal weights this is the usual (tau-a) Kendall's tau.
    """
    T, N = X.shape
    wn = np.asarray(w, float) / np.sum(w)
    denom = 1.0 - np.sum(wn ** 2)
    S = [np.sign(X[:, i][:, None] - X[:, i][None, :]).astype(np.float32) for i in range(N)]
    tau = np.eye(N)
    for i in range(N):
        for j in range(i + 1, N):
            q = float(wn @ ((S[i] * S[j]) @ wn))
            tau[i, j] = tau[j, i] = q / denom
    R = np.sin(np.pi * tau / 2)
    np.fill_diagonal(R, 1.0)
    return nearest_corr(R)


def pair_variant(R_pool: np.ndarray, R_regime: np.ndarray, pair: tuple[int, int]) -> np.ndarray:
    """Pooled correlation matrix with only the (i, j) entry taken from the regime-specific matrix."""
    i, j = pair
    R = R_pool.copy()
    R[i, j] = R[j, i] = R_regime[i, j]
    return nearest_corr(R)


def weighted_corr(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    S, _ = weighted_cov(X, w)
    C, _ = corr_from_cov(S)
    return C


# ------------------------------------------------------------------ layer 1
def make_variants_fn(pair: tuple[int, int] = (0, 1)):
    """Variants for run_regime_models: B, D (pilot's definitions), B_M, D_M (Kendall), D_P (one pair)."""
    def fn(R: np.ndarray, gamma: np.ndarray) -> tuple[dict, dict]:
        K = gamma.shape[1]
        S_pool, _ = weighted_cov(R, np.ones(len(R)))
        C_pool, _ = corr_from_cov(S_pool)
        Cm_pool = weighted_kendall_corr(R, np.ones(len(R)))
        Sk, Mk = zip(*[weighted_cov(R, gamma[:, k] + 1e-12) for k in range(K)])
        covs = {m: [] for m in ("B", "D", "B_M", "D_M", "D_P")}
        for k in range(K):
            Ck, dk = corr_from_cov(Sk[k])
            Cmk = weighted_kendall_corr(R, gamma[:, k] + 1e-12)
            outer = np.outer(dk, dk)
            covs["B"].append(outer * C_pool)
            covs["D"].append(Sk[k])
            covs["B_M"].append(outer * Cm_pool)
            covs["D_M"].append(outer * Cmk)
            covs["D_P"].append(outer * pair_variant(C_pool, Ck, pair))
        means = {m: list(Mk) for m in covs}
        return covs, means
    return fn


# ------------------------------------------------------------------ mixtures
def mix_var_es_t(p: np.ndarray, mu: np.ndarray, s: np.ndarray, nu: float, alpha: float):
    """Mixture of unit-variance-standardised Student-t components (sd s, mean mu): VaR and ES
    as return quantiles. Reduces to engine.t_var_es for one component."""
    p, mu, s = np.asarray(p, float), np.asarray(mu, float), np.asarray(s, float)
    sc = s * np.sqrt((nu - 2) / nu)
    f = lambda q: np.sum(p * stats.t.cdf((q - mu) / sc, nu)) - alpha
    lo, hi = np.min(mu) - 60 * s.max(), np.max(mu) + 60 * s.max()
    q = optimize.brentq(f, lo, hi, xtol=1e-12)
    z = (q - mu) / sc
    part = mu * stats.t.cdf(z, nu) - sc * stats.t.pdf(z, nu) * (nu + z ** 2) / (nu - 1)
    return q, float(np.sum(p * part) / alpha)


# ------------------------------------------------------------------ layer 2
def fit_margins(Rw: np.ndarray):
    """Gaussian-QML GARCH(1,1) with constant mean per asset on a window (return units)."""
    from arch import arch_model
    N = Rw.shape[1]
    mu, om, al, be = np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N)
    for i in range(N):
        r = arch_model(100 * Rw[:, i], mean="Constant", vol="GARCH", p=1, q=1,
                       dist="normal").fit(disp="off", show_warning=False)
        p = r.params
        mu[i], om[i], al[i], be[i] = p["mu"], p["omega"], p["alpha[1]"], p["beta[1]"]
    return mu, om, al, be


def garch_filter(Rw: np.ndarray, params, init=None):
    """Re-filter a window with fixed GARCH parameters. Returns (eps, sig2) with sig2 of length W+1
    (sig2[W] is the one-step-ahead variance). Percent units."""
    mu, om, al, be = params
    eps = 100 * Rw - mu
    W, N = eps.shape
    sig2 = np.empty((W + 1, N))
    sig2[0] = eps.var(axis=0) if init is None else init   # window sample variance (window is all past data)
    for t in range(W):
        sig2[t + 1] = om + al * eps[t] ** 2 + be * sig2[t]
    return eps, sig2


RS_MODELS = ("CCC_S", "CCC_M", "RSC_S", "RSC_M", "RSC_P")


def run_rs_corr(R: np.ndarray, w: np.ndarray, provider, alphas, start: int, window: int = 1260,
                refit: int = 21, margin_refit: int = 63, pair: tuple[int, int] = (0, 1)) -> dict:
    """Layer 2 walk-forward. Models (each with _N and _t): CCC_S / CCC_M (pooled sample / Kendall
    correlation of GARCH residuals), RSC_S / RSC_M (regime-specific), RSC_P (only `pair` switches)."""
    T, N = R.shape
    rp = R @ w
    names = [f"{m}_{d}" for m in RS_MODELS for d in ("N", "t")]
    V = {a: {m: np.full(T, np.nan) for m in names} for a in alphas}
    E = {a: {m: np.full(T, np.nan) for m in names} for a in alphas}
    stress = np.full(T, np.nan)
    nus = {}
    params = None
    for t0 in range(start, T, refit):
        t1 = min(t0 + refit, T)
        win, blk = slice(t0 - window, t0), slice(t0, t1)
        if params is None or (t0 - start) % margin_refit == 0:
            try:
                params = fit_margins(R[win])
            except Exception:
                if params is None:
                    raise
        eps, sig2 = garch_filter(R[win], params)
        z = eps / np.sqrt(sig2[:-1])
        s2 = sig2[-1].copy()
        gamma, preds = provider.step(win, blk)
        K = gamma.shape[1]
        ones = np.ones(len(z))
        Rs_pool, Rm_pool = weighted_corr(z, ones), weighted_kendall_corr(z, ones)
        Rs_k = [weighted_corr(z, gamma[:, k] + 1e-12) for k in range(K)]
        Rm_k = [weighted_kendall_corr(z, gamma[:, k] + 1e-12) for k in range(K)]
        Rp_k = [pair_variant(Rs_pool, Rs_k[k], pair) for k in range(K)]
        sets = {"CCC_S": [Rs_pool], "CCC_M": [Rm_pool], "RSC_S": Rs_k, "RSC_M": Rm_k, "RSC_P": Rp_k}
        mu_p = float(w @ params[0]) / 100
        A_in = (np.sqrt(sig2[:-1]) / 100) * w
        sd_in = np.sqrt(np.einsum("ti,ij,tj->t", A_in, Rs_pool, A_in))
        nu = fit_t_df((rp[win] - mu_p) / sd_in)
        nus[t0] = nu
        for i, t in enumerate(range(t0, t1)):
            p = preds[i]
            stress[t] = p[-1]
            A = (np.sqrt(s2) / 100) * w
            for m, Rlist in sets.items():
                sd = np.array([np.sqrt(A @ Rk @ A) for Rk in Rlist])
                pm = np.array([1.0]) if len(Rlist) == 1 else p
                mu_arr = np.full(len(sd), mu_p)
                for a in alphas:
                    V[a][f"{m}_N"][t], E[a][f"{m}_N"][t] = mix_var_es(pm, mu_arr, sd, a)
                    V[a][f"{m}_t"][t], E[a][f"{m}_t"][t] = mix_var_es_t(pm, mu_arr, sd, nu, a)
            e_t = 100 * R[t] - params[0]
            s2 = params[1] + params[2] * e_t ** 2 + params[3] * s2
    return {"V": V, "E": E, "stress_prob": stress, "nu": nus}
