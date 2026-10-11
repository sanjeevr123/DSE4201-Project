"""
Exploratory step 6: score the saved walk-forward forecasts.

Reads output/explore/backtests/*.pkl and writes
  output/explore/backtest_loss_table.csv   FZ0 / hit rate / Kupiec / Acerbi-Szekely Z2 per model
  output/explore/backtest_dm_table.csv     Diebold-Mariano comparisons (negative = first model better)

Comparisons (per regime provider p):  D_p vs A (does a regime-switching covariance help),
D_p vs B_p (the correlation channel: does letting correlation switch add anything over
regime volatility alone), C_p vs A, B_p vs A, plus D_p vs the smooth benchmarks GARCH-t and
DCC-t. `mde80` = 2.8 x the standard error of the mean loss difference, i.e. the smallest
true FZ0 difference this sample could detect with ~80% power at the 5% level.
Descriptive/exploratory: p-values are NOT adjusted unless the column says so.

Run: .venv/bin/python scripts/explore_06_score.py
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

BT = ROOT / "output" / "explore" / "backtests"
OUT = ROOT / "output" / "explore"
BENCH = ["HS", "EWMA", "GARCHt", "DCC_N", "DCC_t"]
PERIODS_ETF = {"full_2010_2019": ("2010-01-01", "2019-12-31"),
               "dev_2010_2015": ("2010-01-01", "2015-12-31"),
               "pseudo_2016_2019": ("2016-01-01", "2019-12-31")}
PERIODS_L = {"full_1992_2019": ("1992-01-01", "2019-12-31"),
             "1992_1999": ("1992-01-01", "1999-12-31"),
             "2000_2009": ("2000-01-01", "2009-12-31"),
             "2010_2019": ("2010-01-01", "2019-12-31")}


def providers_of(res) -> list[str]:
    return sorted({k.split("/")[0] for k in res["V"][0.05] if "/" in k})


def main() -> None:
    loss_rows, dm_rows = [], []
    for f in sorted(BT.glob("*.pkl")):
        res = pickle.load(open(f, "rb"))
        uni = res["universe"]
        dates = pd.DatetimeIndex(res["dates"])
        periods = PERIODS_L if uni.startswith("L") else PERIODS_ETF
        provs = providers_of(res)
        for a in (0.05, 0.025):
            V, E = res["V"][a], res["E"][a]
            for pname, (d0, d1) in periods.items():
                m = (dates >= d0) & (dates <= d1)
                y = res["y"][m]
                if len(y) < 100:
                    continue
                L = {k: fz0(y, V[k][m], E[k][m], a) for k in V}
                for k in V:
                    h = (y <= V[k][m]).astype(float)
                    loss_rows.append(dict(universe=uni, alpha=a, period=pname, model=k, n=len(y),
                                          fz0=L[k].mean(), hit=h.mean(), kupiec_p=kupiec(h, a),
                                          christ_p=christoffersen_ind(h),
                                          z2=acerbi_szekely_z2(y, V[k][m], E[k][m], a)))

                def dm(first, second, family, prov):
                    if first not in L or second not in L:
                        return
                    d = L[first] - L[second]
                    t, p = dm_test(L[first], L[second])
                    se = d.mean() / t if abs(t) > 1e-9 else np.nan
                    dm_rows.append(dict(universe=uni, alpha=a, period=pname, family=family, provider=prov,
                                        first=first, second=second, n=len(y), mean_diff=d.mean(),
                                        t=t, p=p, mde80=2.8 * abs(se)))
                dm("GARCHt", "A", "GARCHt_vs_A", "-")
                dm("DCC_t", "GARCHt", "DCCt_vs_GARCHt", "-")
                dm("DCC_t", "A", "DCCt_vs_A", "-")
                for p in provs:
                    dm(f"{p}/D", "A", "D_vs_A", p)
                    dm(f"{p}/B", "A", "B_vs_A", p)
                    dm(f"{p}/C", "A", "C_vs_A", p)
                    dm(f"{p}/D", f"{p}/B", "D_vs_B", p)
                    dm(f"{p}/D", "GARCHt", "D_vs_GARCHt", p)
                    dm(f"{p}/D", "DCC_t", "D_vs_DCCt", p)
    loss = pd.DataFrame(loss_rows)
    dmt = pd.DataFrame(dm_rows)
    # Holm-adjusted p within the headline family D_vs_B over all (universe, provider, alpha, full period)
    head = dmt[(dmt.family == "D_vs_B") & dmt.period.isin(["full_2010_2019", "full_1992_2019"])].copy()
    order = head.p.sort_values().index
    m = len(head)
    adj, run = {}, 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, head.p[i] * (m - rank)))
        adj[i] = run
    dmt["p_holm_headline"] = pd.Series(adj)
    loss.to_csv(OUT / "backtest_loss_table.csv", index=False)
    dmt.to_csv(OUT / "backtest_dm_table.csv", index=False)
    print(f"loss rows {len(loss)}, dm rows {len(dmt)}, headline D_vs_B tests (Holm family): {m}")


if __name__ == "__main__":
    main()
