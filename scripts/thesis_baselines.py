"""POST HOC reference rows: the practitioner baselines (historical simulation, RiskMetrics EWMA, GARCH-t on the portfolio)
scored on the hold-out against the two primary models, from the forecasts already stored in
output/confirm/holdout_forecasts.pkl. Nothing is refitted and no forecast is produced; this script is not part of the
frozen specification. Also writes SPY-IEF correlation by calendar year from the frozen raw file (descriptive).
Writes output/confirm/baselines.json and output/confirm/corr_by_year.json."""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import chi2
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import confirm_01_score as S

res = pickle.load(open(ROOT / "output/confirm/holdout_forecasts.pkl", "rb"))
ARMS = ["CCC_S_N", "RSC_P_N", "GARCHt", "HS", "EWMA"]
out = {"alpha": 0.05, "mean_loss": {}, "hit_rate": {}, "kupiec_p": {}, "vs_ccc": {}}
base = S.losses(res, "CCC_S_N", 0.05)
for a in ARMS:
    v, e = S.forecast(res, a, 0.05)
    l = S.fz0(res["y"], v, e, 0.05)
    out["mean_loss"][a] = float(l.mean())
    out["hit_rate"][a] = float((res["y"] <= v).mean())
    out["kupiec_p"][a] = float(1 - chi2.cdf(S.kupiec_lr((res["y"] <= v).astype(float), 0.05), 1))
    if a != "CCC_S_N":
        d = l - base                       # arm minus CCC; negative favours the arm
        lrv, _ = S.hac_lrv(d)
        se = float(np.sqrt(lrv / len(d)))
        out["vs_ccc"][a] = {"mean_diff": float(d.mean()), "se": se, "t": float(d.mean() / se),
                            "ci_lo": float(d.mean() - 1.96 * se), "ci_hi": float(d.mean() + 1.96 * se)}
(ROOT / "output/confirm/baselines.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))

# SPY-IEF correlation of daily returns by calendar year, from the frozen raw file (descriptive only)
raw = ROOT / "data/raw/spy_ief_gld_raw_2026-09-26.csv"
px = pd.read_csv(raw, index_col=0, parse_dates=True)[["Adj Close_SPY", "Adj Close_IEF", "Adj Close_GLD"]].dropna()
px = px[px.index <= "2025-12-31"]
r = px.pct_change().dropna()
c = {str(y): float(g["Adj Close_SPY"].corr(g["Adj Close_IEF"])) for y, g in r.groupby(r.index.year) if y >= 2010}
dev = r[(r.index >= "2010-01-01") & (r.index <= "2019-12-31")]
c["2010_2019"] = float(dev["Adj Close_SPY"].corr(dev["Adj Close_IEF"]))
(ROOT / "output/confirm/corr_by_year.json").write_text(json.dumps(c, indent=2))
print(json.dumps(c, indent=1))
