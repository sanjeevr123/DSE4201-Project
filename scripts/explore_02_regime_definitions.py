"""
Exploratory step 2: does the way regimes are DEFINED matter? (SPY/IEF/GLD, 2004-2019)

Compares 7 definitions on the pilot universe, descriptively (in-sample
smoothed regime weights; no forecasting, nothing past 2019-12-31):

  HMM_SPY2     baseline: 2-state Gaussian HMM on SPY returns
  HMM_SPY3     3-state HMM on SPY (stress = highest-variance state)
  HMM_MV2      2-state HMM on SPY+IEF+GLD jointly (full covariance)
  HMM_SPYVIX2  2-state HMM on SPY return + standardised log VIX
  RULE_VIX20   stress when VIX >= 20
  RULE_RV75    stress when 21d SPY realised vol is in its top quartile
  RULE_CORR    "regime" = top tercile of 63d SPY-IEF correlation (a CORRELATION-defined regime)

Run: .venv/bin/python scripts/explore_02_regime_definitions.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine import fit_hmm  # noqa: E402
from src.explore import load_explore_returns, regime_decomposition, run_lengths  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output" / "explore"
ASSETS = ["SPY", "IEF", "GLD"]
EPISODES = {
    "GFC 2008-09..2009-03": ("2008-09-15", "2009-03-31"),
    "Euro/flash 2010": ("2010-05-01", "2010-06-30"),
    "US downgrade 2011": ("2011-08-01", "2011-10-31"),
    "Taper tantrum 2013": ("2013-05-01", "2013-09-30"),
    "China Aug 2015": ("2015-08-15", "2015-09-15"),
    "Q4 2018": ("2018-10-01", "2018-12-31"),
}
CALM_CTRL = ("2017-01-01", "2017-12-31")


def best_hmm(X: np.ndarray, k: int, cov: str, n_init: int = 6) -> GaussianHMM:
    best, best_ll = None, -np.inf
    for seed in range(n_init):
        m = GaussianHMM(k, covariance_type=cov, n_iter=200, tol=1e-5, random_state=seed)
        try:
            m.fit(X)
            ll = m.score(X)
        except Exception:
            continue
        if ll > best_ll:
            best, best_ll = m, ll
    return best


def order_by_risk(gamma: np.ndarray, port: np.ndarray) -> np.ndarray:
    """Reorder state columns by (probability-weighted) portfolio variance, ascending."""
    var = [np.average((port - np.average(port, weights=gamma[:, k])) ** 2, weights=gamma[:, k] + 1e-12)
           for k in range(gamma.shape[1])]
    return gamma[:, np.argsort(var)]


def main() -> None:
    R, vix = load_explore_returns()
    df = R[ASSETS].dropna()
    vix = vix.reindex(df.index).ffill()
    X = df.values
    port = X.mean(axis=1)
    spy = X[:, 0]

    gammas: dict[str, np.ndarray] = {}   # T x K, columns ordered calm -> stress
    g = fit_hmm(spy).predict_proba(spy.reshape(-1, 1)); gammas["HMM_SPY2"] = g
    m3 = best_hmm(spy.reshape(-1, 1), 3, "diag")
    gammas["HMM_SPY3"] = order_by_risk(m3.predict_proba(spy.reshape(-1, 1)), spy)
    mmv = best_hmm(X, 2, "full")
    gammas["HMM_MV2"] = order_by_risk(mmv.predict_proba(X), port)
    lv = np.log(vix.values); lv = (lv - lv.mean()) / lv.std()
    X2 = np.c_[spy / spy.std(), lv]
    mvx = best_hmm(X2, 2, "full")
    gammas["HMM_SPYVIX2"] = order_by_risk(mvx.predict_proba(X2), spy)

    hard = lambda mask: np.c_[1 - mask, mask].astype(float)
    gammas["RULE_VIX20"] = hard((vix.values >= 20).astype(float))
    rv = pd.Series(spy, index=df.index).rolling(21).std()
    thr = rv.quantile(0.75)
    gammas["RULE_RV75"] = hard((rv.fillna(rv.median()).values >= thr).astype(float))
    cr = pd.Series(df["SPY"]).rolling(63).corr(df["IEF"])
    cthr = cr.quantile(2 / 3)
    gammas["RULE_CORR"] = hard((cr.fillna(cr.median()).values >= cthr).astype(float))

    base_p = gammas["HMM_SPY2"][:, -1]
    results, stress_p = {}, {}
    idx = df.index
    for name, G in gammas.items():
        p = G[:, -1]                       # P(highest-risk / "stress" state)
        stress_p[name] = p
        hard_state = (p > 0.5).astype(int)
        runs = run_lengths(hard_state, 1)
        dec = regime_decomposition(X, np.c_[G[:, 0], G[:, -1]])
        eps = {e: float(p[(idx >= a) & (idx <= b)].mean()) for e, (a, b) in EPISODES.items()}
        results[name] = {
            "stress_share": float(p.mean()),
            "mean_stress_run_days": float(runs.mean()) if len(runs) else None,
            "n_stress_episodes": int(len(runs)),
            "switches_per_year": float(np.abs(np.diff(hard_state)).sum() / (len(idx) / 252)),
            "calm_vol_ann": dec["calm_vol"], "stress_vol_ann": dec["stress_vol"],
            "vol_share": dec["vol_share"], "corr_share": dec["corr_share"],
            "d_avg_pair_corr": dec["d_avg_pair_corr"],
            "corr_eq_bond_calm": float(dec["corr_calm"][0, 1]), "corr_eq_bond_stress": float(dec["corr_stress"][0, 1]),
            "episode_mean_stress_prob": eps,
            "calm_control_2017_mean_stress_prob": float(p[(idx >= CALM_CTRL[0]) & (idx <= CALM_CTRL[1])].mean()),
            "corr_with_baseline_stress_prob": float(np.corrcoef(p, base_p)[0, 1]),
        }

    (OUT / "regime_definitions.json").write_text(json.dumps(results, indent=2))
    pd.DataFrame(stress_p, index=idx).to_csv(OUT / "regime_stress_probs.csv")

    hdr = f"{'definition':13s}{'share':>6s}{'run(d)':>8s}{'sw/yr':>7s}{'corr%':>7s}{'dCorr':>7s}{'EQ-BD calm':>11s}{'stress':>8s}{'2017':>6s}{'taper13':>8s}{'corr~base':>10s}"
    print(hdr)
    for n, r in results.items():
        print(f"{n:13s}{r['stress_share']:6.2f}{r['mean_stress_run_days']:8.1f}{r['switches_per_year']:7.1f}"
              f"{r['corr_share']*100:7.0f}{r['d_avg_pair_corr']:+7.2f}{r['corr_eq_bond_calm']:+11.2f}{r['corr_eq_bond_stress']:+8.2f}"
              f"{r['calm_control_2017_mean_stress_prob']:6.2f}{r['episode_mean_stress_prob']['Taper tantrum 2013']:8.2f}"
              f"{r['corr_with_baseline_stress_prob']:10.2f}")
    print("\nepisode mean stress prob:")
    print(pd.DataFrame({n: r["episode_mean_stress_prob"] for n, r in results.items()}).round(2).to_string())


if __name__ == "__main__":
    main()
