"""Post hoc descriptive checks on the hold-out loss difference (read-only; written after the result, labelled POST HOC
in the thesis). Reads output/confirm/holdout_forecasts.pkl, writes output/confirm/posthoc.json. Does not refit anything."""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
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
(ROOT / "output/confirm/posthoc.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
