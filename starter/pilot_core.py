"""
Pilot core: regime-dependent covariance ablation for portfolio VaR/ES.

Models (all share the SAME 2-state HMM fitted on the equity return only):
  A  pooled covariance (single normal)
  B  regime-dependent volatilities, common (pooled) correlation
  C  common (pooled) volatilities, regime-dependent correlation
  D  regime-dependent volatilities AND correlations
Benchmarks:
  HS     historical simulation (500 days)
  EWMA   RiskMetrics lambda=0.94 on the portfolio return, normal
  GARCHt GARCH(1,1) Student-t on the portfolio return
Scoring: FZ0 joint VaR/ES loss (Patton, Ziegel & Chen 2019), hit rates,
Diebold-Mariano with Newey-West HAC errors.
"""
import warnings
import numpy as np
from scipy import stats, optimize
from hmmlearn.hmm import GaussianHMM

warnings.filterwarnings("ignore")
import logging; logging.getLogger("hmmlearn").setLevel(logging.ERROR)

# ----------------------------------------------------------------- HMM
def fit_hmm(x, prev=None, seed=0):
    """2-state Gaussian HMM on a 1-D series. State 0 = calm (lower variance)."""
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


def filtered_probs(m, x, p0):
    """Forward filter with fixed params. Returns filtered P(S_t | x_1..t) and
    one-step predictive P(S_{t+1} | x_1..t) for each t."""
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
def weighted_cov(R, w):
    w = w / w.sum()
    mu = w @ R
    Z = R - mu
    return (Z * w[:, None]).T @ Z, mu


def corr_from_cov(S):
    d = np.sqrt(np.diag(S))
    return S / np.outer(d, d), d


def build_variants(R, gamma):
    """R: window returns (T x N). gamma: smoothed state probs (T x 2).
    Returns dict variant -> list of (cov_k) for k=0,1 (A has identical)."""
    S_pool, _ = weighted_cov(R, np.ones(len(R)))
    C_pool, d_pool = corr_from_cov(S_pool)
    out = {"A": [S_pool, S_pool]}
    Sk = [weighted_cov(R, gamma[:, k] + 1e-12)[0] for k in range(2)]
    B, C, D = [], [], []
    for k in range(2):
        Ck, dk = corr_from_cov(Sk[k])
        B.append(np.outer(dk, dk) * C_pool)
        C.append(np.outer(d_pool, d_pool) * Ck)
        D.append(Sk[k])
    out["B"], out["C"], out["D"] = B, C, D
    return out


# ------------------------------------------------ mixture VaR / ES
def mix_var_es(p, s, alpha):
    """Zero-mean normal mixture with weights p, sds s. Returns (VaR, ES) as
    return quantile (negative numbers)."""
    f = lambda q: np.sum(p * stats.norm.cdf(q / s)) - alpha
    lo, hi = -20 * s.max(), 0.0
    q = optimize.brentq(f, lo, hi, xtol=1e-12)
    z = q / s
    es = -np.sum(p * s * stats.norm.pdf(z)) / alpha
    return q, es


# ------------------------------------------------------------ scoring
def fz0(y, v, e, alpha):
    """FZ0 loss (Patton, Ziegel & Chen 2019). v, e negative. Lower is better."""
    hit = (y <= v).astype(float)
    return -hit * (v - y) / (alpha * e) + v / e + np.log(-e) - 1.0


def dm_test(l1, l2, lags=None):
    """DM on d = l1 - l2 with Newey-West HAC. Negative t => model 1 better."""
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


def kupiec(hits, alpha):
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


# ------------------------------------------------------------ GARCH-t
def fit_garch_t(x):
    from arch import arch_model
    am = arch_model(100 * x, mean="Constant", vol="GARCH", p=1, q=1, dist="t")
    r = am.fit(disp="off", show_warning=False)
    p = r.params
    last_var = r.conditional_volatility[-1] ** 2
    last_eps = (100 * x[-1] - p["mu"])
    return dict(mu=p["mu"] / 100, omega=p["omega"], alpha=p["alpha[1]"],
                beta=p["beta[1]"], nu=p["nu"], last_var=last_var,
                last_eps=last_eps)


def t_var_es(mu, sigma, nu, alpha):
    """Standardised-t (unit variance) VaR/ES, as return quantile."""
    scale = sigma * np.sqrt((nu - 2) / nu)
    q = stats.t.ppf(alpha, nu)
    es_std = -(stats.t.pdf(q, nu) / alpha) * (nu + q ** 2) / (nu - 1)
    return mu + scale * q, mu + scale * es_std


# ------------------------------------------------------ walk-forward
def walk_forward(R, w, eq_col=0, start=1260, window=1260, refit=21,
                 alpha=0.05, garch_refit=63, hs_window=500, lam=0.94,
                 true_pred=None, true_covs=None, seed=0):
    """R: full return matrix (T x N). Forecast days start..T-1.
    Returns dict of arrays: y, and per model VaR, ES.
    true_pred/true_covs (optional): oracle regime predictive probs & covs."""
    T, N = R.shape
    rp = R @ w
    models = ["A", "B", "C", "D", "HS", "EWMA", "GARCHt"]
    if true_pred is not None:
        models += ["Oracle_B", "Oracle_D"]
    V = {m: np.full(T, np.nan) for m in models}
    E = {m: np.full(T, np.nan) for m in models}
    stress_prob = np.full(T, np.nan)

    hmm = None
    # EWMA initial variance
    ew = np.var(rp[start - window:start])
    for t in range(start - window, start):
        ew = lam * ew + (1 - lam) * rp[t] ** 2

    g = None
    for t0 in range(start, T, refit):
        t1 = min(t0 + refit, T)
        win = slice(t0 - window, t0)
        x = R[win, eq_col]
        hmm = fit_hmm(x, prev=hmm, seed=seed)
        gamma = hmm.predict_proba(x.reshape(-1, 1))
        covs = build_variants(R[win], gamma)
        sds = {k: np.array([np.sqrt(w @ covs[k][j] @ w) for j in range(2)])
               for k in covs}
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
                V[k][t], E[k][t] = mix_var_es(p, sds[k], alpha)
            # HS
            h = rp[t - hs_window:t]
            q = np.quantile(h, alpha)
            V["HS"][t], E["HS"][t] = q, h[h <= q].mean()
            # EWMA
            s = np.sqrt(ew)
            V["EWMA"][t] = s * stats.norm.ppf(alpha)
            E["EWMA"][t] = -s * stats.norm.pdf(stats.norm.ppf(alpha)) / alpha
            # GARCH-t
            V["GARCHt"][t], E["GARCHt"][t] = t_var_es(
                g["mu"], np.sqrt(gvar) / 100, g["nu"], alpha)
            # oracle
            if true_pred is not None:
                for name, cv in [("Oracle_B", true_covs["B"]), ("Oracle_D", true_covs["D"])]:
                    so = np.array([np.sqrt(w @ cv[j] @ w) for j in range(2)])
                    V[name][t], E[name][t] = mix_var_es(true_pred[t], so, alpha)
            # updates after observing day t
            ew = lam * ew + (1 - lam) * rp[t] ** 2
            eps = 100 * rp[t] - g["mu"] * 100
            gvar = g["omega"] + g["alpha"] * eps ** 2 + g["beta"] * gvar

    idx = np.arange(start, T)
    return dict(y=rp[idx], V={m: V[m][idx] for m in models},
                E={m: E[m][idx] for m in models}, stress_prob=stress_prob[idx],
                idx=idx)


def score(res, alpha, pairs=(("D", "B"), ("C", "A"), ("B", "A"), ("D", "A"),
                             ("B", "GARCHt"), ("D", "GARCHt"))):
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
