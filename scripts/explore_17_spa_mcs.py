"""
Exploratory step 17: Hansen SPA ("does any regime model beat the smooth benchmark?") and the model confidence set,
per universe, FZ0 loss, alpha 5%, Student-t chain, pooled mean. Declared in docs/decisions_log.md.
Output: output/explore/ladder/spa_mcs.csv. Run: .venv/bin/python scripts/explore_17_spa_mcs.py
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from arch.bootstrap import MCS, SPA

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.engine import fz0  # noqa: E402
from explore_14_score_ladder import BT, LD, RT, UNIS  # noqa: E402

A, REPS = 0.05, 2000


def losses(u):
    S_all = pickle.load(open(LD / f"{u}.pkl", "rb"))
    old = pickle.load(open(BT / f"{u}.pkl", "rb"))
    l2 = S_all["L2"] if u == "L1_longhist" else pickle.load(open(RT / UNIS[u], "rb"))["L2"]
    y, S = S_all["y"], S_all["S"]
    F = {k: (S["V"][A][f"{k}|pooled|t"], S["E"][A][f"{k}|pooled|t"]) for k in ("A", "B", "D")}
    for k in ("CCC_S", "RSC_S", "RSC_P"):
        F[k.replace("_S", "")] = (l2["V"][A][f"{k}_t"], l2["E"][A][f"{k}_t"])
    F["DCC_t"], F["GARCHt"] = (old["V"][A]["DCC_t"], old["E"][A]["DCC_t"]), (old["V"][A]["GARCHt"], old["E"][A]["GARCHt"])
    return pd.DataFrame({k: fz0(y, v, e, A) for k, (v, e) in F.items()}, index=pd.DatetimeIndex(S_all["dates"]))


def main():
    rows = []
    unis = list(UNIS) + (["L1_longhist"] if (LD / "L1_longhist.pkl").exists() else [])
    for u in unis:
        L = losses(u)
        cands = ["B", "D", "RSC", "RSC_P"]
        for bench in ("GARCHt", "DCC_t"):
            spa = SPA(L[bench].values, L[cands].values, reps=REPS, seed=0)
            spa.compute()
            pv = spa.pvalues
            rows.append(dict(universe=u, test="SPA", benchmark=bench, n=len(L), spa_p_consistent=float(pv["consistent"]),
                             spa_p_upper=float(pv["upper"]), best_candidate=cands[int(np.argmin(L[cands].mean().values))],
                             best_minus_bench=float(L[cands].mean().min() - L[bench].mean())))
        mcs = MCS(L.values, size=0.10, reps=REPS, seed=0)
        mcs.compute()
        inc = [L.columns[i] for i in mcs.included] if all(isinstance(i, (int, np.integer)) for i in mcs.included) \
            else list(mcs.included)
        rows.append(dict(universe=u, test="MCS90", benchmark="", n=len(L), included=",".join(map(str, inc))))
    pd.DataFrame(rows).to_csv(LD / "spa_mcs.csv", index=False)
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
