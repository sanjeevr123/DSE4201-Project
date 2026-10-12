"""
Exploratory step 9: score the Route M / Route P comparison and the GARCH-margin + regime-correlation arm.

Reads output/explore/routes/U1_routes_<provider>.pkl and the benchmarks (A, HS, EWMA, GARCH-t, DCC-N, DCC-t)
from output/explore/backtests/U1_pilot.pkl (same forecast days, checked below). Writes
routes_loss_table.csv and routes_dm_table.csv in output/explore/routes/.

DM sign convention: negative mean_diff / t = FIRST model better. Pre-declared PRIMARY tests (docs): D_M vs B and
D_P vs B at alpha = 5%, full window, provider HMM_SPY2, Holm-adjusted over these two. Everything else is
secondary/descriptive and unadjusted. mde80 = 2.8 x SE of the mean loss difference.

Run: .venv/bin/python scripts/explore_09_score_routes.py
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.engine import acerbi_szekely_z2, christoffersen_ind, dm_test, fz0, kupiec  # noqa: E402

RT = ROOT / "output" / "explore" / "routes"
PERIODS = {"full_2010_2019": ("2010-01-01", "2019-12-31"), "dev_2010_2015": ("2010-01-01", "2015-12-31"),
           "pseudo_2016_2019": ("2016-01-01", "2019-12-31")}
BENCH = ["A", "HS", "EWMA", "GARCHt", "DCC_N", "DCC_t"]


def load(provider):
    r = pickle.load(open(RT / f"U1_routes_{provider}.pkl", "rb"))
    old = pickle.load(open(ROOT / "output" / "explore" / "backtests" / "U1_pilot.pkl", "rb"))
    assert len(old["y"]) == len(r["y"]) and np.allclose(old["y"], r["y"]), "forecast days / returns differ"
    V, E = {}, {}
    for a in (0.05, 0.025):
        V[a] = {**{k: r["L1"]["V"][a][k] for k in r["L1"]["V"][a]}, **{k: r["L2"]["V"][a][k] for k in r["L2"]["V"][a]},
                **{k: old["V"][a][k] for k in BENCH}}
        E[a] = {**{k: r["L1"]["E"][a][k] for k in r["L1"]["E"][a]}, **{k: r["L2"]["E"][a][k] for k in r["L2"]["E"][a]},
                **{k: old["E"][a][k] for k in BENCH}}
    return r, V, E


def comparisons():
    c = []                                                       # (family, first, second)
    c += [("PRIMARY_L1", "D_M", "B"), ("PRIMARY_L1", "D_P", "B")]
    c += [("L1_channel", "D", "B"), ("L1_channel_within_M", "D_M", "B_M"), ("L1_M_vs_D", "D_M", "D"),
          ("L1_P_vs_D", "D_P", "D"), ("L1_M_vs_P", "D_M", "D_P")]
    for d in ("N", "t"):
        c += [(f"L2_channel_{d}", f"RSC_S_{d}", f"CCC_S_{d}"), (f"L2_channel_M_{d}", f"RSC_M_{d}", f"CCC_M_{d}"),
              (f"L2_channel_P_{d}", f"RSC_P_{d}", f"CCC_S_{d}"),
              (f"L2_M_vs_S_{d}", f"RSC_M_{d}", f"RSC_S_{d}"), (f"L2_P_vs_S_{d}", f"RSC_P_{d}", f"RSC_S_{d}")]
        bench = "DCC_N" if d == "N" else "DCC_t"
        for m in ("CCC_S", "CCC_M", "RSC_S", "RSC_M", "RSC_P"):
            c.append((f"L2_vs_DCC_{d}", f"{m}_{d}", bench))
    c += [("CCC_vs_B", "CCC_S_N", "B"), ("RSC_vs_D", "RSC_S_N", "D"), ("D_vs_DCC_N", "D", "DCC_N"),
          ("D_vs_GARCHt", "D", "GARCHt"), ("RSC_S_t_vs_GARCHt", "RSC_S_t", "GARCHt"),
          ("DCC_t_vs_GARCHt", "DCC_t", "GARCHt"), ("DCC_N_vs_DCC_t", "DCC_N", "DCC_t")]
    return c


def main():
    loss_rows, dm_rows = [], []
    for provider in ("HMM_SPY2", "RULE_RV75"):
        r, V, E = load(provider)
        dates = pd.DatetimeIndex(r["dates"])
        for a in (0.05, 0.025):
            for pname, (d0, d1) in PERIODS.items():
                m = (dates >= d0) & (dates <= d1)
                y = r["y"][m]
                L = {k: fz0(y, V[a][k][m], E[a][k][m], a) for k in V[a]}
                for k in V[a]:
                    h = (y <= V[a][k][m]).astype(float)
                    loss_rows.append(dict(provider=provider, alpha=a, period=pname, model=k, n=len(y),
                                          fz0=L[k].mean(), hit=h.mean(), kupiec_p=kupiec(h, a),
                                          christ_p=christoffersen_ind(h),
                                          z2=acerbi_szekely_z2(y, V[a][k][m], E[a][k][m], a)))
                for fam, f, s in comparisons():
                    if f not in L or s not in L:
                        continue
                    t, p = dm_test(L[f], L[s])
                    d = L[f] - L[s]
                    dm_rows.append(dict(provider=provider, alpha=a, period=pname, family=fam, first=f, second=s,
                                        n=len(y), mean_diff=d.mean(), t=t, p=p,
                                        mde80=2.8 * abs(d.mean() / t) if abs(t) > 1e-9 else np.nan))
    loss, dm = pd.DataFrame(loss_rows), pd.DataFrame(dm_rows)
    prim = dm[(dm.family == "PRIMARY_L1") & (dm.provider == "HMM_SPY2") & (dm.alpha == 0.05)
              & (dm.period == "full_2010_2019")].p.sort_values()
    adj, run = {}, 0.0
    for rank, i in enumerate(prim.index):
        run = max(run, min(1.0, prim[i] * (len(prim) - rank)))
        adj[i] = run
    dm["p_holm_primary"] = pd.Series(adj)
    loss.to_csv(RT / "routes_loss_table.csv", index=False)
    dm.to_csv(RT / "routes_dm_table.csv", index=False)
    print(f"loss rows {len(loss)}, dm rows {len(dm)}")


if __name__ == "__main__":
    main()
