"""
Exploratory step 12: does giving the regime model GARCH margins remove the gap to GARCH-t / DCC, beyond the
pilot universe? Layer-2 forecasts (explore_08 --universes ...) for U3, U8, U10 are compared with the static-
covariance regime models B, D and the benchmarks stored in output/explore/backtests/<universe>.pkl
(same forecast days, same SPY HMM). U1 is included for reference.

Pre-declared primary family (docs/decisions_log.md): RSC_S_N vs D, alpha 5%, full window, Holm over U3/U8/U10.
Negative mean_diff / t = FIRST model better. Output: output/explore/routes/confound_{loss,dm}_table.csv.

Run: .venv/bin/python scripts/explore_12_score_confound.py
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.engine import christoffersen_ind, dm_test, fz0, kupiec  # noqa: E402

RT = ROOT / "output" / "explore" / "routes"
BT = ROOT / "output" / "explore" / "backtests"
UNIS = {"U1_pilot": RT / "U1_routes_HMM_SPY2.pkl", "U3_credit": RT / "U3_credit_routes_HMM_SPY2.pkl",
        "U8_sectors": RT / "U8_sectors_routes_HMM_SPY2.pkl", "U10_riskassets": RT / "U10_riskassets_routes_HMM_SPY2.pkl"}
PRIMARY_UNIS = ["U3_credit", "U8_sectors", "U10_riskassets"]
COMPARE = [("GARCH_margin_effect", "RSC_S_N", "D"), ("GARCH_margin_effect_CCC", "CCC_S_N", "B"),
           ("RSC_vs_DCC_N", "RSC_S_N", "DCC_N"), ("RSC_vs_DCC_t", "RSC_S_t", "DCC_t"),
           ("RSC_vs_GARCHt", "RSC_S_t", "GARCHt"), ("CCC_vs_DCC_N", "CCC_S_N", "DCC_N"),
           ("correlation_channel_N", "RSC_S_N", "CCC_S_N"), ("correlation_channel_t", "RSC_S_t", "CCC_S_t"),
           ("OLD_GAP_D_vs_GARCHt", "D", "GARCHt"), ("OLD_GAP_D_vs_DCC_N", "D", "DCC_N"),
           ("OLD_GAP_B_vs_GARCHt", "B", "GARCHt")]
PERIODS = {"full": ("2000-01-01", "2019-12-31"), "pseudo_2016_2019": ("2016-01-01", "2019-12-31")}


def main():
    loss_rows, dm_rows = [], []
    for u, path in UNIS.items():
        r = pickle.load(open(path, "rb"))
        old = pickle.load(open(BT / f"{u}.pkl", "rb"))
        assert len(old["y"]) == len(r["y"]) and np.allclose(old["y"], r["y"]), f"{u}: forecast days differ"
        dates = pd.DatetimeIndex(r["dates"])
        for a in (0.05, 0.025):
            V = {**{k: v for k, v in r["L2"]["V"][a].items()},
                 **{"B": old["V"][a]["HMM_SPY2/B"], "D": old["V"][a]["HMM_SPY2/D"],
                    **{k: old["V"][a][k] for k in ("A", "GARCHt", "DCC_N", "DCC_t")}}}
            E = {**{k: v for k, v in r["L2"]["E"][a].items()},
                 **{"B": old["E"][a]["HMM_SPY2/B"], "D": old["E"][a]["HMM_SPY2/D"],
                    **{k: old["E"][a][k] for k in ("A", "GARCHt", "DCC_N", "DCC_t")}}}
            for pname, (d0, d1) in PERIODS.items():
                m = (dates >= d0) & (dates <= d1)
                y = r["y"][m]
                L = {k: fz0(y, V[k][m], E[k][m], a) for k in V}
                for k in ("A", "B", "D", "CCC_S_N", "RSC_S_N", "CCC_S_t", "RSC_S_t", "DCC_N", "DCC_t", "GARCHt"):
                    h = (y <= V[k][m]).astype(float)
                    loss_rows.append(dict(universe=u, alpha=a, period=pname, model=k, n=len(y), fz0=L[k].mean(),
                                          hit=h.mean(), kupiec_p=kupiec(h, a), christ_p=christoffersen_ind(h)))
                for fam, f, s in COMPARE:
                    t, p = dm_test(L[f], L[s])
                    d = L[f] - L[s]
                    dm_rows.append(dict(universe=u, alpha=a, period=pname, family=fam, first=f, second=s, n=len(y),
                                        mean_diff=d.mean(), t=t, p=p))
    loss, dm = pd.DataFrame(loss_rows), pd.DataFrame(dm_rows)
    prim = dm[(dm.family == "GARCH_margin_effect") & dm.universe.isin(PRIMARY_UNIS) & (dm.alpha == 0.05)
              & (dm.period == "full")].p.sort_values()
    adj, run = {}, 0.0
    for rank, i in enumerate(prim.index):
        run = max(run, min(1.0, prim[i] * (len(prim) - rank)))
        adj[i] = run
    dm["p_holm_primary"] = pd.Series(adj)
    loss.to_csv(RT / "confound_loss_table.csv", index=False)
    dm.to_csv(RT / "confound_dm_table.csv", index=False)
    print("saved")


if __name__ == "__main__":
    main()
