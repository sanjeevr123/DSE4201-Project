"""
Pilot engine: regime-dependent covariance ablation for portfolio VaR/ES.

This is a reviewed-and-fixed copy of starter/pilot_core.py (see docs/decision_log.md
for the review). Two changes vs. the starter prototype:

1. mix_var_es and build_variants now carry the regime-conditional mean through
   to the VaR/ES calculation, instead of silently assuming zero mean. The
   starter version discarded `mu` from weighted_cov() before it reached
   mix_var_es(). Left uncorrected, this understates left-tail risk in any
   regime with non-negligible drift (e.g. a stress state with a large
   negative mean), and made the A/B/C/D/Oracle comparisons inconsistent with
   GARCH-t and HS, which are mean-aware.
2. A multivariate-EWMA benchmark (EWMA_MV) is added alongside the existing
   univariate EWMA, per the pilot spec: "multivariate EWMA (full covariance,
   lambda=0.94) vs univariate EWMA of the portfolio. This is the smooth,
   non-regime analogue of D vs B."

Models (all share the SAME 2-state HMM fitted on the equity return only):
  A  pooled covariance (single normal)
  B  regime-dependent volatilities, common (pooled) correlation
  C  common (pooled) volatilities, regime-dependent correlation
  D  regime-dependent volatilities AND correlations
Benchmarks:
  HS       historical simulation (500 days)
  EWMA     RiskMetrics lambda=0.94 on the portfolio return, zero-mean normal
  EWMA_MV  RiskMetrics lambda=0.94 on the full asset covariance, zero-mean normal
  GARCHt   GARCH(1,1) Student-t on the portfolio return
Scoring: FZ0 joint VaR/ES loss (Patton, Ziegel & Chen 2019), hit rates,
Kupiec unconditional coverage, Christoffersen independence, Acerbi-Szekely Z2,
Diebold-Mariano with Newey-West HAC errors.
"""
from __future__ import annotations

import logging
import warnings
from typing import Iterable, Optional

import numpy as np
from hmmlearn.hmm import GaussianHMM
from scipy import optimize, stats

warnings.filterwarnings("ignore")
logging.getLogger("hmmlearn").setLevel(logging.ERROR)


# ----------------------------------------------------------------- HMM
def fit_hmm(x: np.ndarray, prev: Optional[GaussianHMM] = None, seed: int = 0) -> GaussianHMM:
    """Fit a 2-state Gaussian HMM on a 1-D series. State 0 = calm (lower variance).

    If `prev` is given, the new fit warm-starts from its fitted parameters
    (startprob_, transmat_, means_, covars_) with a shorter EM run, matching
    the rolling-refit design in walk_forward(). Otherwise a fresh cold start
    is used with wider, separated initial variances for the two states.
    """
    X = x.reshape(-1, 1)
    if prev is None:
        m = GaussianHMM(2, covariance_type="diag", n_iter=100, tol=1e-4,
                         random_state=seed, init_params="", params="stmc")
        v = np.var(x)
        m.startprob_ = np.array([0.5, 0.5])
        m.transmat_ = np.array([[0.98, 0.02], [0.05, 0.95]])
        m.means_ = np.array([[np.mean(x)], [np.mean(x)]])
        m.covars_ = np.array([[0.5 * v], [2.5 * v]])
    else:
        m = GaussianHMM(2, covariance_type="diag", n_iter=50, tol=1e-4,
                         init_params="", params="stmc")
        m.startprob_ = prev.startprob_.copy()
        m.transmat_ = prev.transmat_.copy()
        m.means_ = prev.means_.copy()
        m.covars_ = prev.covars_.reshape(2, 1).copy()
    m.fit(X)
    # order states: 0 = low variance
    order = np.argsort(m.covars_.ravel())
    if order[0] != 0:
        m.startprob_ = m.startprob_[order]
        m.transmat_ = m.transmat_[np.ix_(order, order)]
        m.means_ = m.means_[order]
        m.covars_ = m.covars_.reshape(2, 1)[order]
    return m


def filtered_probs(m: GaussianHMM, x: np.ndarray, p0: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Forward filter with fixed params.

    Returns filtered P(S_t | x_1..t) and one-step predictive P(S_{t+1} | x_1..t)
    for each t. Only ever uses x_1..t to produce outputs at t, and p0 to seed
    the first step — no information beyond t leaks into filt[t] or pred[t].
    """
    P = m.transmat_
    mu = m.means_.ravel()
    sd = np.sqrt(m.covars_.ravel())
    filt = np.empty((len(x), 2))
    pred = np.empty((len(x), 2))
    prior = p0 @ P
    for t, xt in enumerate(x):
        lik = stats.norm.pdf(xt, mu, sd)
        post = prior * lik
        s = post.sum()
        post = post / s if s > 0 else prior
        filt[t] = post
        prior = post @ P
        pred[t] = prior
    return filt, pred


# ------------------------------------------------- regime covariances
def weighted_cov(R: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Weighted (MLE, population-normalized) mean and covariance of R under weights w."""
    w = w / w.sum()
    mu = w @ R
    Z = R - mu
    return (Z * w[:, None]).T @ Z, mu


def corr_from_cov(S: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = np.sqrt(np.diag(S))
    return S / np.outer(d, d), d


def build_variants(R: np.ndarray, gamma: np.ndarray) -> tuple[dict, dict]:
    """Build the four covariance-ablation variants A/B/C/D, and their means.

    R: window returns (T x N). gamma: state probabilities (T x 2).

    Returns (covs, means):
      covs[variant]  -> [cov_state0, cov_state1] (A has identical states)
      means[variant] -> [mu_state0, mu_state1], each an N-vector

    The mean is not part of the vol/correlation ablation, so B, C and D all
    use the same regime-conditional mean (the weighted mean under gamma[:,k]);
    A, being the fully-pooled "no regime" model, uses the pooled mean in both
    states, consistent with it not using regime information at all.
    """
    S_pool, mu_pool = weighted_cov(R, np.ones(len(R)))
    C_pool, d_pool = corr_from_cov(S_pool)
    covs = {"A": [S_pool, S_pool]}
    means = {"A": [mu_pool, mu_pool]}

    Sk, Mk = zip(*[weighted_cov(R, gamma[:, k] + 1e-12) for k in range(2)])
    B, C, D = [], [], []
    for k in range(2):
        Ck, dk = corr_from_cov(Sk[k])
        B.append(np.outer(dk, dk) * C_pool)
        C.append(np.outer(d_pool, d_pool) * Ck)
        D.append(Sk[k])
    covs["B"], covs["C"], covs["D"] = B, C, D
    means["B"] = means["C"] = means["D"] = list(Mk)
    return covs, means


# ------------------------------------------------ mixture VaR / ES
def mix_var_es(p: np.ndarray, mu: np.ndarray, s: np.ndarray, alpha: float) -> tuple[float, float]:
    """Normal-mixture VaR/ES. Returns (VaR, ES) as return quantiles (negative numbers).

    p: state/component probabilities. mu: component means. s: component sds.
    Solves for q such that sum_k p_k * Phi((q-mu_k)/s_k) = alpha, then computes
    ES = (1/alpha) * sum_k p_k * (mu_k * Phi(z_k) - s_k * phi(z_k)), z_k = (q-mu_k)/s_k.
    With mu == 0 this reduces exactly to the zero-mean formula.
    """
    f = lambda q: np.sum(p * stats.norm.cdf((q - mu) / s)) - alpha
    lo = np.min(mu) - 20 * s.max()
    hi = np.max(mu) + 20 * s.max()
    q = optimize.brentq(f, lo, hi, xtol=1e-12)
    z = (q - mu) / s
    es = np.sum(p * (mu * stats.norm.cdf(z) - s * stats.norm.pdf(z))) / alpha
    return q, es


# ------------------------------------------------------------ scoring
def fz0(y: np.ndarray, v: np.ndarray, e: np.ndarray, alpha: float) -> np.ndarray:
    """FZ0 loss (Patton, Ziegel & Chen 2019). v, e negative. Lower is better."""
    hit = (y <= v).astype(float)
    return -hit * (v - y) / (alpha * e) + v / e + np.log(-e) - 1.0


def dm_test(l1: np.ndarray, l2: np.ndarray, lags: Optional[int] = None) -> tuple[float, float]:
    """Diebold-Mariano on d = l1 - l2 with Newey-West HAC. Negative t => model 1 better."""
    d = l1 - l2
    T = len(d)
    if lags is None:
        lags = int(np.floor(4 * (T / 100) ** (2 / 9)))
    dc = d - d.mean()
    gamma0 = dc @ dc / T
    lrv = gamma0
    for L in range(1, lags + 1):
        g = dc[L:] @ dc[:-L] / T
        lrv += 2 * (1 - L / (lags + 1)) * g
    t = d.mean() / np.sqrt(lrv / T)
    return t, 2 * (1 - stats.norm.cdf(abs(t)))


def kupiec(hits: np.ndarray, alpha: float) -> float:
    """Kupiec unconditional-coverage test. Returns a p-value."""
    n, x = len(hits), hits.sum()
    ph = x / n
    if x == 0:
        lr = -2 * n * np.log(1 - alpha)
    elif x == n:
        lr = -2 * n * np.log(alpha)
    else:
        lr = -2 * ((n - x) * np.log(1 - alpha) + x * np.log(alpha)
                   - (n - x) * np.log(1 - ph) - x * np.log(ph))
    return 1 - stats.chi2.cdf(lr, 1)


def christoffersen_ind(hits: np.ndarray) -> float:
    """Christoffersen independence test on a 0/1 hit sequence. Returns a p-value.

    Promoted from starter/pilot_real_data.py (previously a private helper local
    to that script) into the shared engine, since independence of VaR
    exceptions is one of the scoring tools named in the pilot spec.
    """
    h = hits.astype(int)
    n00 = np.sum((h[:-1] == 0) & (h[1:] == 0))
    n01 = np.sum((h[:-1] == 0) & (h[1:] == 1))
    n10 = np.sum((h[:-1] == 1) & (h[1:] == 0))
    n11 = np.sum((h[:-1] == 1) & (h[1:] == 1))
    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)

    def ll(a, b, pr):
        pr = min(max(pr, 1e-12), 1 - 1e-12)
        return a * np.log(1 - pr) + b * np.log(pr)

    lr = -2 * (ll(n00 + n10, n01 + n11, p) - ll(n00, n01, p01) - ll(n10, n11, p11))
    return 1 - stats.chi2.cdf(lr, 1)


def acerbi_szekely_z2(y: np.ndarray, v: np.ndarray, e: np.ndarray, alpha: float) -> float:
    """Acerbi-Szekely (2014) unconditional ES test statistic Z2.

    Z2 = (1 / (T*alpha)) * sum_t [ hit_t * y_t / e_t ] - 1, where
    hit_t = 1{y_t <= v_t} and e_t is the (negative) ES forecast. Under a
    correctly specified model E[hit_t * y_t] = alpha * e_t, so the sum
    averages to 1 and Z2 averages to 0; large |Z2| indicates ES
    misspecification. v, e are return quantiles (negative numbers), matching
    the convention used throughout this module.
    """
    T = len(y)
    hit = (y <= v).astype(float)
    return float(np.sum(hit * y / e) / (T * alpha) - 1.0)


# ------------------------------------------------------------ GARCH-t
def fit_garch_t(x: np.ndarray) -> dict:
    from arch import arch_model
    am = arch_model(100 * x, mean="Constant", vol="GARCH", p=1, q=1, dist="t")
    r = am.fit(disp="off", show_warning=False)
    p = r.params
    last_var = r.conditional_volatility[-1] ** 2
    last_eps = (100 * x[-1] - p["mu"])
    return dict(mu=p["mu"] / 100, omega=p["omega"], alpha=p["alpha[1]"],
                beta=p["beta[1]"], nu=p["nu"], last_var=last_var,
                last_eps=last_eps)


def t_var_es(mu: float, sigma: float, nu: float, alpha: float) -> tuple[float, float]:
    """Standardised-t (unit variance) VaR/ES, as return quantiles."""
    scale = sigma * np.sqrt((nu - 2) / nu)
    q = stats.t.ppf(alpha, nu)
    es_std = -(stats.t.pdf(q, nu) / alpha) * (nu + q ** 2) / (nu - 1)
    return mu + scale * q, mu + scale * es_std


# ---------------------------------------------------------- multivariate EWMA
def mv_ewma_update(cov: np.ndarray, r: np.ndarray, lam: float) -> np.ndarray:
    """One RiskMetrics-style multivariate EWMA covariance update (zero-mean).

    cov: current N x N covariance estimate. r: realized N-vector return for
    the day just observed. lam: decay factor (0.94 default per spec).
    """
    return lam * cov + (1 - lam) * np.outer(r, r)


# ------------------------------------------------------ walk-forward
def walk_forward(R: np.ndarray, w: np.ndarray, eq_col: int = 0, start: int = 1260,
                  window: int = 1260, refit: int = 21, alpha: float = 0.05,
                  garch_refit: int = 63, hs_window: int = 500, lam: float = 0.94,
                  true_pred: Optional[np.ndarray] = None,
                  true_covs: Optional[dict] = None, seed: int = 0) -> dict:
    """Walk-forward one-day-ahead VaR/ES backtest across all models.

    R: full return matrix (T x N). Forecast days are start..T-1.
    true_pred/true_covs (optional): oracle regime predictive probs & covariances,
    for the simulation study's Oracle_B / Oracle_D models (assumed zero-mean,
    matching the zero-mean DGP in the simulation harness).

    No look-ahead: day t's forecast is built only from data through day t-1
    (the HMM window R[t0-window:t0], and preds derived by propagating the
    filtered state forward one step at a time through the refit block,
    `preds = vstack([prior, pred_block[:-1]])`, so pred_block's own last
    entry — which would use day t1-1's return — is never used to forecast
    day t1-1 itself).
    """
    T, N = R.shape
    rp = R @ w
    models = ["A", "B", "C", "D", "HS", "EWMA", "EWMA_MV", "GARCHt"]
    if true_pred is not None:
        models += ["Oracle_B", "Oracle_D"]
    V = {m: np.full(T, np.nan) for m in models}
    E = {m: np.full(T, np.nan) for m in models}
    stress_prob = np.full(T, np.nan)

    hmm = None

    # univariate EWMA initial variance
    ew = np.var(rp[start - window:start])
    for t in range(start - window, start):
        ew = lam * ew + (1 - lam) * rp[t] ** 2

    # multivariate EWMA initial covariance
    ew_cov = np.cov(R[start - window:start], rowvar=False)
    for t in range(start - window, start):
        ew_cov = mv_ewma_update(ew_cov, R[t], lam)

    g = None
    for t0 in range(start, T, refit):
        t1 = min(t0 + refit, T)
        win = slice(t0 - window, t0)
        x = R[win, eq_col]
        hmm = fit_hmm(x, prev=hmm, seed=seed)
        gamma = hmm.predict_proba(x.reshape(-1, 1))
        covs, means = build_variants(R[win], gamma)
        sds = {k: np.array([np.sqrt(w @ covs[k][j] @ w) for j in range(2)])
               for k in covs}
        mus = {k: np.array([w @ means[k][j] for j in range(2)]) for k in means}
        # predictive prob for day t0 from the end of the window
        filt_end = gamma[-1]
        prior = filt_end @ hmm.transmat_
        # filtered path through the block
        _, pred_block = filtered_probs(hmm, R[t0:t1, eq_col], filt_end)
        preds = np.vstack([prior, pred_block[:-1]])

        if (t0 - start) % garch_refit == 0:
            g = fit_garch_t(rp[t0 - window:t0])
            gvar = g["omega"] + g["alpha"] * g["last_eps"] ** 2 + g["beta"] * g["last_var"]

        for i, t in enumerate(range(t0, t1)):
            p = preds[i]
            stress_prob[t] = p[1]
            for k in ["A", "B", "C", "D"]:
                V[k][t], E[k][t] = mix_var_es(p, mus[k], sds[k], alpha)
            # HS
            h = rp[t - hs_window:t]
            q = np.quantile(h, alpha)
            V["HS"][t], E["HS"][t] = q, h[h <= q].mean()
            # univariate EWMA (zero-mean, RiskMetrics)
            s = np.sqrt(ew)
            V["EWMA"][t] = s * stats.norm.ppf(alpha)
            E["EWMA"][t] = -s * stats.norm.pdf(stats.norm.ppf(alpha)) / alpha
            # multivariate EWMA (zero-mean, full covariance, portfolio-projected)
            s_mv = np.sqrt(w @ ew_cov @ w)
            V["EWMA_MV"][t] = s_mv * stats.norm.ppf(alpha)
            E["EWMA_MV"][t] = -s_mv * stats.norm.pdf(stats.norm.ppf(alpha)) / alpha
            # GARCH-t
            V["GARCHt"][t], E["GARCHt"][t] = t_var_es(
                g["mu"], np.sqrt(gvar) / 100, g["nu"], alpha)
            # oracle (zero-mean, matching the simulation study's zero-mean DGP)
            if true_pred is not None:
                zero_mu = np.zeros(2)
                for name, cv in [("Oracle_B", true_covs["B"]), ("Oracle_D", true_covs["D"])]:
                    so = np.array([np.sqrt(w @ cv[j] @ w) for j in range(2)])
                    V[name][t], E[name][t] = mix_var_es(true_pred[t], zero_mu, so, alpha)
            # updates after observing day t
            ew = lam * ew + (1 - lam) * rp[t] ** 2
            ew_cov = mv_ewma_update(ew_cov, R[t], lam)
            eps = 100 * rp[t] - g["mu"] * 100
            gvar = g["omega"] + g["alpha"] * eps ** 2 + g["beta"] * gvar

    idx = np.arange(start, T)
    return dict(y=rp[idx], V={m: V[m][idx] for m in models},
                E={m: E[m][idx] for m in models}, stress_prob=stress_prob[idx],
                idx=idx)


DEFAULT_DM_PAIRS = (
    ("D", "B"), ("C", "A"), ("B", "A"), ("D", "A"),
    ("B", "GARCHt"), ("D", "GARCHt"), ("B", "EWMA_MV"), ("D", "EWMA_MV"),
)


def score(res: dict, alpha: float, pairs: Iterable[tuple[str, str]] = DEFAULT_DM_PAIRS) -> dict:
    """Score a walk_forward() result: FZ0 loss, hit rate, Kupiec p-value, DM tests."""
    y = res["y"]
    out = {"loss": {}, "hit": {}, "kupiec_p": {}, "dm": {}}
    L = {}
    for m in res["V"]:
        L[m] = fz0(y, res["V"][m], res["E"][m], alpha)
        hits = (y <= res["V"][m]).astype(float)
        out["loss"][m] = L[m].mean()
        out["hit"][m] = hits.mean()
        out["kupiec_p"][m] = kupiec(hits, alpha)
    for a, b in pairs:
        if a in L and b in L:
            out["dm"][f"{a}-{b}"] = dm_test(L[a], L[b])
    out["L"] = L
    return out
