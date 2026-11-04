"""
Dry run against the exploration path (docs/THESIS_PLAN.md 4.11, 3.10.4). The dry-run pickle (forecasts 2016-2019, HMM chain and margin
refit anchored at the first forecast day, cold HMM start in 2016) is compared with the exploration forecasts for the same days
(chains anchored in 2010, warm HMM since 2010): absolute differences in VaR and ES, in mean FZ0, and in the Diebold-Mariano
quantities of the primary comparison RSC_P_N vs CCC_S_N. Pipeline check only: it is evidence about the size of the path difference, not
about the hypothesis. Data through 2019-12-31.

  .venv/bin/python scripts/confirm_05_dryrun_compare.py
Output: output/confirm/dryrun_vs_exploration.csv, output/confirm/dryrun_vs_exploration_summary.json
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.engine import dm_test, fz0  # noqa: E402

OUT = ROOT / "output" / "confirm"
EXP = ROOT / "output" / "explore"
ALPHAS = (0.05, 0.025)
L2_ARMS = ("CCC_S_N", "RSC_S_N", "RSC_P_N", "CCC_S_t", "RSC_P_t")
S_ARMS = ("A|pooled|N", "B|pooled|N", "D|pooled|N")
B_ARMS = ("DCC_N", "DCC_t", "GARCHt")


def main():
    ps = pickle.load(open(OUT / "pseudo_forecasts.pkl", "rb"))
    rt = pickle.load(open(EXP / "routes" / "U1_routes_HMM_SPY2.pkl", "rb"))
    ld = pickle.load(open(EXP / "ladder" / "U1_pilot.pkl", "rb"))
    bt = pickle.load(open(EXP / "backtests" / "U1_pilot.pkl", "rb"))
    idx = pd.DatetimeIndex(rt["dates"]).get_indexer(pd.DatetimeIndex(ps["dates"]))
    assert (idx >= 0).all(), "dry-run dates not all in the exploration sample"
    y = ps["y"]
    out = {"n_days": len(y), "first": str(ps["dates"][0].date()), "last": str(ps["dates"][-1].date()),
           "max_abs_portfolio_return_diff": float(np.max(np.abs(y - rt["y"][idx])))}
    rows, loss = [], {}
    sources = [("L2", ps["L2"], rt["L2"], L2_ARMS), ("S", ps["S"], ld["S"], S_ARMS), ("B", ps["B"], bt, B_ARMS)]
    for block, mine, exp, arms in sources:
        for a in ALPHAS:
            for arm in arms:
                v1, e1 = mine["V"][a][arm], mine["E"][a][arm]
                v2, e2 = exp["V"][a][arm][idx], exp["E"][a][arm][idx]
                if block == "B":                                      # backtests pickle is indexed by its own forecast days
                    ib = pd.DatetimeIndex(bt["dates"]).get_indexer(pd.DatetimeIndex(ps["dates"])) if "dates" in bt else idx
                    v2, e2 = exp["V"][a][arm][ib], exp["E"][a][arm][ib]
                l1, l2 = fz0(y, v1, e1, a), fz0(y, v2, e2, a)
                loss[(a, arm)] = (l1, l2)
                dv, de = np.abs(v1 - v2), np.abs(e1 - e2)
                rows.append(dict(block=block, alpha=a, arm=arm, median_abs_var_diff=np.median(dv), max_abs_var_diff=dv.max(),
                                 median_abs_es_diff=np.median(de), max_abs_es_diff=de.max(), mean_fz0_dryrun=l1.mean(),
                                 mean_fz0_exploration=l2.mean(), mean_fz0_diff=l1.mean() - l2.mean(),
                                 sign_mismatch_hits=int(np.sum((y <= v1) != (y <= v2)))))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "dryrun_vs_exploration.csv", index=False)
    for a in ALPHAS:
        r1, c1 = loss[(a, "RSC_P_N")][0], loss[(a, "CCC_S_N")][0]
        r2, c2 = loss[(a, "RSC_P_N")][1], loss[(a, "CCC_S_N")][1]
        t1, t2 = dm_test(r1, c1)[0], dm_test(r2, c2)[0]
        out[f"primary_alpha{a}"] = dict(mean_diff_dryrun=float((r1 - c1).mean()), mean_diff_exploration=float((r2 - c2).mean()),
                                         t_dryrun=float(t1), t_exploration=float(t2))
    out["median_abs_var_diff_by_block"] = {b: float(g.median_abs_var_diff.median()) for b, g in df.groupby("block")}
    out["max_abs_var_diff_by_block"] = {b: float(g.max_abs_var_diff.max()) for b, g in df.groupby("block")}
    out["max_abs_mean_fz0_diff"] = float(df.mean_fz0_diff.abs().max())
    (OUT / "dryrun_vs_exploration_summary.json").write_text(json.dumps(out, indent=2))
    pd.set_option("display.width", 220, "display.max_columns", 20, "display.float_format", lambda x: f"{x:.2e}")
    print(df.to_string(index=False))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
