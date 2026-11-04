"""
Exploratory step 18: Giacomini-White conditional predictive-ability test on the long-history sample (declared in
docs/decisions_log.md). d_t = FZ0(RSC) - FZ0(CCC) (negative = regime correlation better), alpha 5%, Gaussian chain.
Instruments: a constant and the lagged 63-day stock-bond correlation c_{t-1} (known at t-1). Reports the unconditional
test, the conditional test, and the mean d_t when c_{t-1} > 0 versus c_{t-1} <= 0. Data through 2019-12-31 only.
Run: .venv/bin/python scripts/explore_18_gw_conditional.py   Output: output/explore/ladder/gw_conditional.csv
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.engine import dm_test, fz0  # noqa: E402
from src.explore_inference import gw_test  # noqa: E402

LD = ROOT / "output" / "explore" / "ladder"
A = 0.05


def main():
    S = pickle.load(open(LD / "L1_longhist.pkl", "rb"))
    px = pd.read_csv(ROOT / "output" / "explore" / "longhistory_prices.csv", index_col=0, parse_dates=True)
    r = px[["VFINX", "VUSTX"]].pct_change().dropna()
    c = r["VFINX"].rolling(63).corr(r["VUSTX"]).shift(1)          # known at t-1
    idx = pd.DatetimeIndex(S["dates"])
    c = c.reindex(idx)
    y, l2, s = S["y"], S["L2"], S["S"]
    d = (fz0(y, l2["V"][A]["RSC_S_N"], l2["E"][A]["RSC_S_N"], A) - fz0(y, l2["V"][A]["CCC_S_N"], l2["E"][A]["CCC_S_N"], A))
    d2 = (fz0(y, l2["V"][A]["RSC_P_N"], l2["E"][A]["RSC_P_N"], A) - fz0(y, l2["V"][A]["CCC_S_N"], l2["E"][A]["CCC_S_N"], A))
    rows = []
    for name, dd in (("RSC_vs_CCC", d), ("RSC_P_vs_CCC", d2)):
        for pname, (d0, d1) in {"full": ("1990", "2019"), "1992_1999": ("1992", "1999"), "2000_2019": ("2000", "2019")}.items():
            m = (idx >= f"{d0}-01-01") & (idx <= f"{d1}-12-31") & c.notna().values
            dv, cv = dd[m], c.values[m]
            t_dm, p_dm = dm_test(dv, np.zeros_like(dv))
            gw = gw_test(dv, np.c_[np.ones(len(dv)), cv])
            pos = cv > 0
            rows.append(dict(contrast=name, period=pname, n=len(dv), mean_d=dv.mean(), p_dm=p_dm, gw_p=gw["p"],
                             coef_const=gw["coef"][0], coef_lagcorr=gw["coef"][1], share_pos_corr=pos.mean(),
                             mean_d_posc=dv[pos].mean() if pos.any() else np.nan,
                             mean_d_negc=dv[~pos].mean() if (~pos).any() else np.nan))
    out = pd.DataFrame(rows)
    out.to_csv(LD / "gw_conditional.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.float_format", lambda x: f"{x:.4f}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
