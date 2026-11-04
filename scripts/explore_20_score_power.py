"""
Exploratory step 20: summarise the GARCH-DGP power study (scripts/explore_16_power_garch.py).
Per scenario x alpha x ladder step: one-sided 5% rejection rate (t < -1.645 = richer model better), 95% interval
(normal approximation, as in the pilot's power_summary.csv), wrong-sign rate (t > +1.645), mean FZ0 difference with its
Monte Carlo SE, calibration (mean hit rate) for the models involved. Size is read from S0 (no correlation change).
Output: output/explore/ladder/power_summary.csv. Run: .venv/bin/python scripts/explore_20_score_power.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PW = ROOT / "output" / "explore" / "ladder" / "power"
CRIT = 1.6449
PAIRS = {"regime_vol": ("B|pooled|N", "A|pooled|N"), "static_corr": ("D|pooled|N", "B|pooled|N"),
         "margin_pooledcorr": ("CCC_S_N", "B|pooled|N"), "margin_effect": ("RSC_S_N", "D|pooled|N"),
         "corr_with_margins": ("RSC_S_N", "CCC_S_N"), "corr_with_margins_t": ("RSC_S_t", "CCC_S_t"),
         "pair_with_margins": ("RSC_P_N", "CCC_S_N"), "pair_with_margins_t": ("RSC_P_t", "CCC_S_t")}


def main():
    rows = []
    for f in sorted(PW.glob("*.jsonl")):
        reps = [json.loads(l) for l in open(f) if l.strip()]
        scen = reps[0]["scenario"]
        for a in ("0.05", "0.025"):
            for step, (rich, base) in PAIRS.items():
                t = np.array([r[a]["dm"][step][0] for r in reps])
                d = np.array([r[a]["loss"][rich] - r[a]["loss"][base] for r in reps])
                n = len(reps)
                pw = float(np.mean(t < -CRIT))
                se = np.sqrt(pw * (1 - pw) / n)
                rows.append(dict(scenario=scen, alpha=float(a), step=step, n_reps=n, power=pw,
                                 ci_lo=max(0.0, pw - 1.96 * se), ci_hi=min(1.0, pw + 1.96 * se),
                                 wrong_sign=float(np.mean(t > CRIT)), mean_diff=d.mean(),
                                 mc_se=d.std(ddof=1) / np.sqrt(n), median_abs_t=float(np.median(np.abs(t))),
                                 hit_rich=float(np.mean([r[a]["hit"][rich] for r in reps])),
                                 hit_base=float(np.mean([r[a]["hit"][base] for r in reps]))))
    out = pd.DataFrame(rows)
    out.to_csv(PW.parent / "power_summary.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.float_format", lambda x: f"{x:.3f}")
    b = out[out.alpha == 0.05]
    print("Rejection rate (one-sided 5%), alpha 5% (S0 = size)")
    print(b.pivot_table(index="step", columns="scenario", values="power"))
    print("\nWrong-sign rate"); print(b.pivot_table(index="step", columns="scenario", values="wrong_sign"))
    print("\nMean FZ0 difference"); print(b.pivot_table(index="step", columns="scenario", values="mean_diff"))
    print("\nreps per scenario:", out.groupby("scenario").n_reps.first().to_dict())


if __name__ == "__main__":
    main()
