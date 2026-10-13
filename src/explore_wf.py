"""
Generalised walk-forward VaR/ES backtest for the exploratory phase.

Differences from src/engine.py::walk_forward (which is left untouched):
  * the regime signal is pluggable (any HMM, K states, any causal rule) and
    need not be one of the portfolio's assets;
  * K >= 2 states in the A/B/C/D covariance ablation;
  * several alpha levels are computed in one pass;
  * adds DCC-GARCH benchmarks (DCC_N: Gaussian, DCC_t: Student-t) -- the smooth
    time-varying-correlation alternative to regime-switching correlations;
  * drops EWMA_MV (algebraically identical to EWMA for a fixed-weight
    portfolio, docs/decisions_log.md).

Same no-look-ahead discipline as the pilot: the forecast for day t uses only
information through t-1. Regime thresholds / HMM parameters are estimated on
the trailing window only. Exploration-only: everything stays <= 2019-12-31.
"""
from __future__ import annotations

import numpy as np
from hmmlearn.hmm import GaussianHMM
from scipy import optimize, stats

from src.engine import (
    fit_garch_t,
    fit_hmm,
    corr_from_cov,
    mix_var_es,
    t_var_es,
    weighted_cov,
)


# ------------------------------------------------------------ K-state variants
def build_variants_k(R: np.ndarray, gamma: np.ndarray) -> tuple[dict, dict]:
    """A/B/C/D covariance ablation for K states (K=2 reduces to engine.build_variants)."""
    K = gamma.shape[1]
    S_pool, mu_pool = weighted_cov(R, np.ones(len(R)))
    C_pool, d_pool = corr_from_cov(S_pool)
    covs = {"A": [S_pool] * K}
    means = {"A": [mu_pool] * K}
    Sk, Mk = zip(*[weighted_cov(R, gamma[:, k] + 1e-12) for k in range(K)])
    B, C, D = [], [], []
    for k in range(K):
        Ck, dk = corr_from_cov(Sk[k])
        B.append(np.outer(dk, dk) * C_pool)
        C.append(np.outer(d_pool, d_pool) * Ck)
        D.append(Sk[k])
    covs["B"], covs["C"], covs["D"] = B, C, D
    means["B"] = means["C"] = means["D"] = list(Mk)
    return covs, means


# ------------------------------------------------------------ regime providers
def _finite(m: GaussianHMM) -> bool:
    return all(np.all(np.isfinite(a)) for a in (m.startprob_, m.transmat_, m.means_, m.covars_))


def fit_hmm_k(x: np.ndarray, K: int, prev: GaussianHMM | None = None, seed: int = 0,
              n_init: int = 3) -> GaussianHMM:
    """K-state full-covariance Gaussian HMM on (T x d) features (pre-scaled to ~unit
    variance by the caller). States ordered by variance of feature 0 (ascending).
    Warm-starts from `prev` when given, falling back to a cold start on failure."""
    m = None
    if prev is not None:
        try:
            m = GaussianHMM(K, covariance_type="full", n_iter=50, tol=1e-4, init_params="",
                            params="stmc")
            m.startprob_ = prev.startprob_.copy()
            m.transmat_ = prev.transmat_.copy()
            m.means_ = prev.means_.copy()
            m.covars_ = prev.covars_.copy()
            m.fit(x)
            if not _finite(m):
                m = None
        except Exception:
            m = None
    if m is None:
        best, best_ll = None, -np.inf
        for s in range(n_init):
            try:
                c = GaussianHMM(K, covariance_type="full", n_iter=100, tol=1e-4,
                                random_state=seed + s)
                c.fit(x)
                ll = c.score(x)
            except Exception:
                continue
            if _finite(c) and ll > best_ll:
                best, best_ll = c, ll
        m = best
    order = np.argsort(m.covars_[:, 0, 0])
    if not np.array_equal(order, np.arange(K)):
        m.startprob_ = m.startprob_[order]
        m.transmat_ = m.transmat_[np.ix_(order, order)]
        m.means_ = m.means_[order]
        m.covars_ = m.covars_[order]
    return m


def forward_preds(m: GaussianHMM, Xb: np.ndarray, filt_end: np.ndarray) -> np.ndarray:
    """One-step-ahead predictive state probabilities for each day of block Xb.

    preds[0] = filt_end @ P (uses nothing in the block); preds[i] uses Xb[:i]
    only. The block's last observation is never used (it would be needed only
    for the day after the block).
    """
    P = m.transmat_
    logB = m._compute_log_likelihood(Xb)
    Bm = np.exp(logB - logB.max(axis=1, keepdims=True))
    prior = filt_end @ P
    out = [prior]
    for i in range(len(Xb) - 1):
        post = prior * Bm[i]
        s = post.sum()
        post = post / s if s > 0 else prior
        prior = post @ P
        out.append(prior)
    return np.array(out)


class HMMProvider:
    """HMM regime provider. X: (T x d) causal feature matrix. K states.

    For (d=1, K=2) this reuses the pilot's fit_hmm so the baseline reproduces
    the pilot's regime estimates exactly.
    """

    def __init__(self, name: str, X: np.ndarray, K: int = 2, seed: int = 0):
        self.name, self.X, self.K, self.seed = name, np.asarray(X, float), K, seed
        if self.X.ndim == 1:
            self.X = self.X.reshape(-1, 1)
        self.prev = None
        self.scale = None          # fixed, causal: std of the first window's features
        self.pilot_path = (self.X.shape[1] == 1 and K == 2)
        self.stress_pred: dict[int, np.ndarray] = {}

    def step(self, win: slice, blk: slice) -> tuple[np.ndarray, np.ndarray]:
        x = self.X[win]
        if self.pilot_path:
            m = fit_hmm(x[:, 0], prev=self.prev, seed=self.seed)
            gamma = m.predict_proba(x)
            filt_end = gamma[-1]
            from src.engine import filtered_probs
            _, pb = filtered_probs(m, self.X[blk, 0], filt_end)
            preds = np.vstack([filt_end @ m.transmat_, pb[:-1]])
        else:
            if self.scale is None:
                self.scale = x.std(axis=0)
            xs, xb = x / self.scale, self.X[blk] / self.scale
            m = fit_hmm_k(xs, self.K, prev=self.prev, seed=self.seed)
            gamma = m.predict_proba(xs)
            preds = forward_preds(m, xb, gamma[-1])
        self.prev = m
        return gamma, preds


class RuleProvider:
    """Causal threshold-rule regime: stress when signal >= thr, thr either fixed or the
    q-quantile of the trailing window. Hard 0/1 in-window weights; the predictive
    probability for day t is onehot(state_{t-1}) @ P_hat, P_hat estimated on the window
    (Laplace-smoothed)."""

    def __init__(self, name: str, signal: np.ndarray, thr: float | None = None,
                 q: float | None = None):
        assert (thr is None) != (q is None)
        self.name, self.sig, self.thr, self.q, self.K = name, np.asarray(signal, float), thr, q, 2
        self.n_degenerate = 0

    def step(self, win: slice, blk: slice) -> tuple[np.ndarray, np.ndarray]:
        sw = self.sig[win]
        thr = self.thr if self.thr is not None else float(np.nanquantile(sw, self.q))
        ind = np.nan_to_num(sw, nan=-np.inf) >= thr
        s = ind.astype(int)
        if min(s.sum(), len(s) - s.sum()) < 30:
            self.n_degenerate += 1
        gamma = np.c_[1 - s, s].astype(float)
        cnt = np.ones((2, 2)) * 0.5
        for a, b in zip(s[:-1], s[1:]):
            cnt[a, b] += 1
        P = cnt / cnt.sum(axis=1, keepdims=True)
        sb = (np.nan_to_num(self.sig[blk], nan=-np.inf) >= thr).astype(int)
        prev_state = np.r_[s[-1], sb[:-1]]          # state observed at t-1 for each block day t
        preds = P[prev_state]
        return gamma, preds


# ------------------------------------------------------------ regime-model run
def run_regime_models(R: np.ndarray, w: np.ndarray, provider, alphas, start: int,
                      window: int = 1260, refit: int = 21, models=("A", "B", "C", "D"),
                      variants_fn=None) -> dict:
    """Walk-forward A/B/C/D forecasts for one regime provider. Returns
    {alpha: {model: (V, E)}} arrays of length T (NaN before `start`), plus stress_prob.
    `variants_fn(R_window, gamma) -> (covs, means)` may replace build_variants_k (used by
    src/explore_routes.py for the Kendall-matrix and single-pair variants)."""
    T = R.shape[0]
    V = {a: {m: np.full(T, np.nan) for m in models} for a in alphas}
    E = {a: {m: np.full(T, np.nan) for m in models} for a in alphas}
    stress = np.full(T, np.nan)
    for t0 in range(start, T, refit):
        t1 = min(t0 + refit, T)
        win, blk = slice(t0 - window, t0), slice(t0, t1)
        gamma, preds = provider.step(win, blk)
        covs, means = (variants_fn or build_variants_k)(R[win], gamma)
        sds = {k: np.array([np.sqrt(w @ covs[k][j] @ w) for j in range(len(covs[k]))]) for k in models}
        mus = {k: np.array([w @ means[k][j] for j in range(len(means[k]))]) for k in models}
        for i, t in enumerate(range(t0, t1)):
            p = preds[i]
            stress[t] = p[-1]
            for a in alphas:
                for k in models:
                    V[a][k][t], E[a][k][t] = mix_var_es(p, mus[k], sds[k], a)
    return {"V": V, "E": E, "stress_prob": stress}


# ------------------------------------------------------------ DCC-GARCH
def _dcc_filter(z: np.ndarray, a: float, b: float, Qbar: np.ndarray):
    """Run the DCC(1,1) recursion over standardised residuals z (W x N).
    Returns (Rs (W x N x N) correlation used for each t, Q_next)."""
    W, N = z.shape
    Q = Qbar.copy()
    Rs = np.empty((W, N, N))
    c = 1 - a - b
    for t in range(W):
        d = 1.0 / np.sqrt(np.diag(Q))
        Rs[t] = Q * np.outer(d, d)
        Q = c * Qbar + a * np.outer(z[t], z[t]) + b * Q
    return Rs, Q


def _dcc_negll(params, z, Qbar):
    a, b = params
    if a < 0 or b < 0 or a + b >= 0.9995:
        return 1e10
    Rs, _ = _dcc_filter(z, a, b, Qbar)
    sign, logdet = np.linalg.slogdet(Rs)
    quad = np.einsum("ti,tij,tj->t", z, np.linalg.inv(Rs), z) - np.einsum("ti,ti->t", z, z)
    return 0.5 * float(np.sum(logdet + quad))


def fit_dcc(Rw: np.ndarray, w: np.ndarray, prev_ab=None) -> dict:
    """Fit univariate Gaussian-QML GARCH(1,1) margins + DCC(1,1) on a window of
    returns (W x N, return units). Returns everything needed to forecast the next day
    and to update recursively afterwards."""
    from arch import arch_model
    W, N = Rw.shape
    mu, omega, alpha, beta = np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N)
    eps = np.zeros((W, N))
    sig = np.zeros((W, N))
    for i in range(N):
        r = arch_model(100 * Rw[:, i], mean="Constant", vol="GARCH", p=1, q=1,
                       dist="normal").fit(disp="off", show_warning=False)
        p = r.params
        mu[i], omega[i], alpha[i], beta[i] = p["mu"], p["omega"], p["alpha[1]"], p["beta[1]"]
        sig[:, i] = r.conditional_volatility
        eps[:, i] = 100 * Rw[:, i] - mu[i]
    z = eps / sig
    Qbar = np.cov(z, rowvar=False)
    dq = 1.0 / np.sqrt(np.diag(Qbar))
    Qbar = Qbar * np.outer(dq, dq)
    x0 = prev_ab if prev_ab is not None else (0.03, 0.94)
    res = optimize.minimize(_dcc_negll, x0, args=(z, Qbar), method="Nelder-Mead",
                            options={"xatol": 1e-4, "fatol": 1e-4, "maxiter": 120})
    a, b = res.x
    if not (a >= 0 and b >= 0 and a + b < 0.9995):
        a, b = 0.0, 0.0
    Rs, Q_next = _dcc_filter(z, a, b, Qbar)
    sig2_next = omega + alpha * eps[-1] ** 2 + beta * sig[-1] ** 2
    # standardised portfolio residuals (for the t-df fit)
    D = sig * (1 / 100)
    cov_t = Rs * (D[:, :, None] * D[:, None, :])
    sd_p = np.sqrt(np.einsum("i,tij,j->t", w, cov_t, w))
    u = (Rw @ w - mu @ w / 100) / sd_p
    nu = fit_t_df(u)
    return dict(mu=mu, omega=omega, alpha=alpha, beta=beta, a=a, b=b, Qbar=Qbar,
                Q=Q_next, sig2=sig2_next, nu=nu)


def fit_t_df(u: np.ndarray) -> float:
    """MLE of the df of a unit-variance Student-t on standardised residuals u."""
    def nll(nu):
        k = np.sqrt(nu / (nu - 2))
        return -np.sum(np.log(k) + stats.t.logpdf(u * k, nu))
    r = optimize.minimize_scalar(nll, bounds=(2.2, 60.0), method="bounded")
    return float(r.x)


# ------------------------------------------------------------ benchmark run
def run_benchmarks(R: np.ndarray, w: np.ndarray, alphas, start: int, window: int = 1260,
                   refit: int = 21, garch_refit: int = 63, dcc_refit: int = 63,
                   hs_window: int = 500, lam: float = 0.94, dcc: bool = True) -> dict:
    """HS, EWMA, GARCH-t (all on the portfolio return, as in the pilot) and DCC_N / DCC_t."""
    T, N = R.shape
    rp = R @ w
    names = ["HS", "EWMA", "GARCHt"] + (["DCC_N", "DCC_t"] if dcc else [])
    V = {a: {m: np.full(T, np.nan) for m in names} for a in alphas}
    E = {a: {m: np.full(T, np.nan) for m in names} for a in alphas}

    ew = np.var(rp[start - window:start])
    for t in range(start - window, start):
        ew = lam * ew + (1 - lam) * rp[t] ** 2

    g, gvar, d, prev_ab = None, None, None, None
    for t0 in range(start, T, refit):
        t1 = min(t0 + refit, T)
        if (t0 - start) % garch_refit == 0:
            g = fit_garch_t(rp[t0 - window:t0])
            gvar = g["omega"] + g["alpha"] * g["last_eps"] ** 2 + g["beta"] * g["last_var"]
        if dcc and (t0 - start) % dcc_refit == 0:
            d = fit_dcc(R[t0 - window:t0], w, prev_ab)
            prev_ab = (d["a"], d["b"])
            sig2, Q = d["sig2"].copy(), d["Q"].copy()
        for t in range(t0, t1):
            for a in alphas:
                h = rp[t - hs_window:t]
                q = np.quantile(h, a)
                V[a]["HS"][t], E[a]["HS"][t] = q, h[h <= q].mean()
                s = np.sqrt(ew)
                za = stats.norm.ppf(a)
                V[a]["EWMA"][t] = s * za
                E[a]["EWMA"][t] = -s * stats.norm.pdf(za) / a
                V[a]["GARCHt"][t], E[a]["GARCHt"][t] = t_var_es(
                    g["mu"], np.sqrt(gvar) / 100, g["nu"], a)
            if dcc:
                dq = 1.0 / np.sqrt(np.diag(Q))
                Rt = Q * np.outer(dq, dq)
                sd_i = np.sqrt(sig2) / 100
                sd_p = float(np.sqrt(w @ (Rt * np.outer(sd_i, sd_i)) @ w))
                mu_p = float(w @ d["mu"]) / 100
                for a in alphas:
                    za = stats.norm.ppf(a)
                    V[a]["DCC_N"][t], E[a]["DCC_N"][t] = mu_p + sd_p * za, mu_p - sd_p * stats.norm.pdf(za) / a
                    V[a]["DCC_t"][t], E[a]["DCC_t"][t] = t_var_es(mu_p, sd_p, d["nu"], a)
                # update after observing day t
                eps = 100 * R[t] - d["mu"]
                zt = eps / np.sqrt(sig2)
                c = 1 - d["a"] - d["b"]
                Q = c * d["Qbar"] + d["a"] * np.outer(zt, zt) + d["b"] * Q
                sig2 = d["omega"] + d["alpha"] * eps ** 2 + d["beta"] * sig2
            ew = lam * ew + (1 - lam) * rp[t] ** 2
            eps_p = 100 * rp[t] - g["mu"] * 100
            gvar = g["omega"] + g["alpha"] * eps_p ** 2 + g["beta"] * gvar
    return {"V": V, "E": E}
