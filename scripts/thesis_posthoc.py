"""Post hoc descriptive checks on the hold-out (read-only; written after the result, labelled POST HOC in the thesis).
Reads output/confirm/holdout_forecasts.pkl, writes output/confirm/posthoc.json. Does not refit anything.

  hac            standard error and t of the primary difference at HAC lags 0, 7, 21, 42
  year_sum/mean  the primary difference by calendar year; the 2020 crash window
  bootstrap      stationary-bootstrap 95% percentile intervals for the mean difference (expected block lengths 5, 21 and
                 63 days, 10,000 draws, seed 0), a check on the normal interval of a heavy-tailed series
  breach_by_year 5% VaR breach rate by calendar year for CCC, RSC_P and the RiskMetrics EWMA, with days per year
  t_chain_calib  coverage of the two primary models in the Student-t chain (hit rate, Kupiec, Christoffersen
                 independence, conditional coverage, mean y/ES on breach days); Z2 is not simulated for this chain;
                 keys are ARM_a50 (5%) and ARM_a25 (2.5%)
"""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
from arch.bootstrap import StationaryBootstrap
from scipy.stats import chi2
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import confirm_01_score as S

res = pickle.load(open(ROOT / "output/confirm/holdout_forecasts.pkl", "rb"))
d = S.losses(res, "RSC_P_N", 0.05) - S.losses(res, "CCC_S_N", 0.05)
s = pd.Series(d, index=pd.DatetimeIndex(res["dates"]))
n = len(d)
out = {"hac": {}, "year_sum": {}, "year_mean": {}}
for m in (0, 7, 21, 42):
    v, _ = S.hac_lrv(d, m)
    se = float(np.sqrt(v / n))
    out["hac"][str(m)] = {"se": se, "t": float(d.mean() / se)}
for y, g in s.groupby(s.index.year):
    out["year_sum"][str(y)] = float(g.sum()); out["year_mean"][str(y)] = float(g.mean())
cov = (s.index >= "2020-02-15") & (s.index <= "2020-04-30")
out["covid_window_sum"] = float(s[cov].sum())
out["mean_excluding_covid_window"] = float(s[~cov].mean())
out["total_sum"] = float(s.sum())

out["bootstrap"] = {}
for b in (5, 21, 63):
    bs = StationaryBootstrap(b, d, seed=0)
    means = np.array([x[0][0].mean() for x in bs.bootstrap(10_000)])
    out["bootstrap"][str(b)] = {"ci_lo": float(np.quantile(means, 0.025)), "ci_hi": float(np.quantile(means, 0.975)),
                                "share_below_zero": float((means < 0).mean())}

y = res["y"]
out["t_chain_calib"] = {}
for a in (0.05, 0.025):
    for arm in ("RSC_P_t", "CCC_S_t"):
        v, e = S.forecast(res, arm, a)
        h = (y <= v).astype(float)
        uc, ind = S.kupiec_lr(h, a), S.christoffersen_lr(h)
        out["t_chain_calib"][f"{arm}_a{int(a * 1000)}"] = {"hits": int(h.sum()), "hit_rate": float(h.mean()),
                                              "kupiec_p": float(1 - chi2.cdf(uc, 1)),
                                              "independence_p": float(1 - chi2.cdf(ind, 1)),
                                              "cc_p": float(1 - chi2.cdf(uc + ind, 2)),
                                              "es_ratio": float(np.mean(y[h == 1] / e[h == 1]))}
out["breach_by_year"] = {"days": {str(k): int(v) for k, v in s.groupby(s.index.year).size().items()}}
for arm in ("CCC_S_N", "RSC_P_N", "EWMA"):
    v, _ = S.forecast(res, arm, 0.05)
    hb = pd.Series(res["y"] <= v, index=s.index)
    out["breach_by_year"][arm] = {str(k): float(g.mean()) for k, g in hb.groupby(hb.index.year)}
(ROOT / "output/confirm/posthoc.json").write_text(json.dumps(out, indent=2))
print(json.dumps({k: out[k] for k in ("bootstrap", "t_chain_calib")}, indent=1))
