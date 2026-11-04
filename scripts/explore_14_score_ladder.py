"""
Exploratory step 14: score the controlled-ablation ladder (docs/decisions_log.md, "Ladder / equal-mean control").

Rungs (richer vs baseline; NEGATIVE mean_diff / t => the richer model is better):
  A      pooled static normal (no regimes)
  B      regime volatilities, pooled correlation (static within regime)
  D      regime volatilities and correlations (static within regime)
  CCC    GARCH(1,1) margins, constant correlation          (layer 2)
  RSC    GARCH(1,1) margins, regime-switching correlation  (layer 2)
  DCC    DCC-GARCH benchmark;   GARCHt  univariate GARCH-t on the portfolio (t chain only)
Mean sets: 'pooled' (one mean in every regime; PRIMARY), 'zero', and 'regime' (original B/D, reference only).
Steps: regime_vol B/A; static_corr D/B; margin_pooledcorr CCC/B; margin_effect RSC/D (PRIMARY, pooled, N, 5%,
full, Holm over U1/U3/U8/U10); corr_with_margins RSC/CCC; regime_vs_smooth DCC/RSC; smooth_corr DCC/CCC;
mv_vs_univariate GARCHt/DCC (t chain).

Output: output/explore/ladder/ladder_{loss,dm}_table.csv. Run: .venv/bin/python scripts/explore_14_score_ladder.py
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

LD = ROOT / "output" / "explore" / "ladder"
RT = ROOT / "output" / "explore" / "routes"
BT = ROOT / "output" / "explore" / "backtests"
UNIS = {"U1_pilot": "U1_routes_HMM_SPY2.pkl", "U3_credit": "U3_credit_routes_HMM_SPY2.pkl",
        "U8_sectors": "U8_sectors_routes_HMM_SPY2.pkl", "U10_riskassets": "U10_riskassets_routes_HMM_SPY2.pkl"}
PERIODS = {"full": ("2000-01-01", "2019-12-31"), "2010_2012": ("2010-01-01", "2012-12-31"),
           "2013_2015": ("2013-01-01", "2015-12-31"), "2016_2019": ("2016-01-01", "2019-12-31")}
PERIODS_L1 = {"full": ("1990-01-01", "2019-12-31"), "1992_1999": ("1992-01-01", "1999-12-31"),
              "2000_2009": ("2000-01-01", "2009-12-31"), "2010_2019": ("2010-01-01", "2019-12-31")}
STEPS = [("regime_vol", "B", "A"), ("static_corr", "D", "B"), ("margin_pooledcorr", "CCC", "B"),
         ("margin_effect", "RSC", "D"), ("corr_with_margins", "RSC", "CCC"), ("regime_vs_smooth", "DCC", "RSC"),
         ("smooth_corr", "DCC", "CCC"), ("mv_vs_univariate", "GARCHt", "DCC")]
Z = 2.8016  # (1.96 + 0.8416): minimum detectable effect at 80% power, two-sided 5%


def holm(p: pd.Series) -> pd.Series:
    order = p.sort_values().index
    adj, run = {}, 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, p[i] * (len(order) - rank)))
        adj[i] = run
    return pd.Series(adj)


def rung_forecasts(S, L2, L2Z, old, a):
    """{mean_set: {chain: {rung: (V, E)}}} for one universe and alpha."""
    out = {}
    for ms, l2 in (("pooled", L2), ("zero", L2Z)):
        for chain, d, c2 in (("N", "N", "N"), ("t", "t", "t")):
            g = lambda k: (S["V"][a][f"{k}|{ms}|{d}"], S["E"][a][f"{k}|{ms}|{d}"])
            r = {"A": g("A"), "B": g("B"), "D": g("D"),
                 "CCC": (l2["V"][a][f"CCC_S_{c2}"], l2["E"][a][f"CCC_S_{c2}"]),
                 "RSC": (l2["V"][a][f"RSC_S_{c2}"], l2["E"][a][f"RSC_S_{c2}"]),
                 "DCC": (old["V"][a][f"DCC_{c2}"], old["E"][a][f"DCC_{c2}"])}
            if chain == "t":
                r["GARCHt"] = (old["V"][a]["GARCHt"], old["E"][a]["GARCHt"])
            out[(ms, chain)] = r
    out[("regime", "N")] = {"B": (S["V"][a]["B|regime|N"], S["E"][a]["B|regime|N"]),
                            "D": (S["V"][a]["D|regime|N"], S["E"][a]["D|regime|N"]),
                            "A": (S["V"][a]["A|pooled|N"], S["E"][a]["A|pooled|N"]),
                            "CCC": (L2["V"][a]["CCC_S_N"], L2["E"][a]["CCC_S_N"]),
                            "RSC": (L2["V"][a]["RSC_S_N"], L2["E"][a]["RSC_S_N"])}
    return out


def main():
    loss_rows, dm_rows = [], []
    jobs = dict(UNIS)
    if (LD / "L1_longhist.pkl").exists():
        jobs["L1_longhist"] = None
    for u, rfile in jobs.items():
        S_all = pickle.load(open(LD / f"{u}.pkl", "rb"))
        if rfile is None:
            l2 = S_all["L2"]
            old = pickle.load(open(BT / "L1_longhist.pkl", "rb"))
            assert np.allclose(old["y"], S_all["y"]), f"{u}: forecast days differ"
            periods = PERIODS_L1
        else:
            rt = pickle.load(open(RT / rfile, "rb"))
            l2 = rt["L2"]
            old = pickle.load(open(BT / f"{u}.pkl", "rb"))
            assert np.allclose(old["y"], S_all["y"]) and np.allclose(rt["y"], S_all["y"]), f"{u}: forecast days differ"
            periods = PERIODS
        dates = pd.DatetimeIndex(S_all["dates"])
        for a in (0.05, 0.025):
            sets = rung_forecasts(S_all["S"], l2, S_all["L2Z"], old, a)
            for (ms, chain), rungs in sets.items():
                for pname, (d0, d1) in periods.items():
                    m = (dates >= d0) & (dates <= d1)
                    if m.sum() < 120:
                        continue
                    y = S_all["y"][m]
                    L = {k: fz0(y, v[0][m], v[1][m], a) for k, v in rungs.items()}
                    for k, (v, e) in rungs.items():
                        h = (y <= v[m]).astype(float)
                        loss_rows.append(dict(universe=u, alpha=a, period=pname, mean_set=ms, chain=chain, rung=k,
                                              n=len(y), fz0=L[k].mean(), hit=h.mean(), kupiec_p=kupiec(h, a),
                                              christ_p=christoffersen_ind(h)))
                    for step, f, s in STEPS:
                        if f not in L or s not in L:
                            continue
                        t, p = dm_test(L[f], L[s])
                        d = L[f] - L[s]
                        se = d.mean() / t if t != 0 else np.nan
                        dm_rows.append(dict(universe=u, alpha=a, period=pname, mean_set=ms, chain=chain, step=step,
                                            richer=f, baseline=s, n=len(y), mean_diff=d.mean(), se=abs(se), t=t, p=p,
                                            mde80=Z * abs(se)))
    loss, dm = pd.DataFrame(loss_rows), pd.DataFrame(dm_rows)
    # primary family: margin_effect, pooled, N, 5%, full, Holm over the four universes
    pri = dm[(dm.universe != "L1_longhist") & (dm.step == "margin_effect") & (dm.mean_set == "pooled") & (dm.chain == "N") & (dm.alpha == 0.05)
             & (dm.period == "full")]
    dm["p_holm_primary"] = holm(pri.p)
    # secondary: Holm over the six within-chain steps per universe x set x chain x alpha x period
    dm["p_holm_steps"] = np.nan
    for _, g in dm[dm.step != "mv_vs_univariate"].groupby(["universe", "alpha", "period", "mean_set", "chain"]):
        dm.loc[g.index, "p_holm_steps"] = holm(g.p)
    loss.to_csv(LD / "ladder_loss_table.csv", index=False)
    dm.to_csv(LD / "ladder_dm_table.csv", index=False)
    print("saved", len(loss), "loss rows,", len(dm), "dm rows")


if __name__ == "__main__":
    main()
