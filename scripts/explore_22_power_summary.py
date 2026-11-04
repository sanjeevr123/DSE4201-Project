"""
Exploratory step 22: summarise the power study at the hold-out length (scripts/explore_21_power_holdout_length.py), and add
two-sided columns for the earlier 2,520-day study without changing its power_summary.csv.
Per scenario x tail level x step: rejection rates one-sided (t < -1.6449, richer better), two-sided (|t| > 1.96) and upper
tail (t > +1.6449, t > +1.96), each with a 95% binomial interval (normal approximation, as in power_summary.csv); mean FZ0
difference with its Monte Carlo SE; mean and median HAC standard error of the loss difference; mean hit rates.
Output: output/explore/ladder/power_1508_summary.csv, output/explore/ladder/power_2520_twosided.csv.
Run: .venv/bin/python scripts/explore_22_power_summary.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LD = ROOT / "output" / "explore" / "ladder"
ONE, TWO = 1.6449, 1.96
PAIRS = {"regime_vol": ("B|pooled|N", "A|pooled|N"), "static_corr": ("D|pooled|N", "B|pooled|N"),
         "margin_pooledcorr": ("CCC_S_N", "B|pooled|N"), "margin_effect": ("RSC_S_N", "D|pooled|N"),
         "corr_with_margins": ("RSC_S_N", "CCC_S_N"), "corr_with_margins_t": ("RSC_S_t", "CCC_S_t"),
         "pair_with_margins": ("RSC_P_N", "CCC_S_N"), "pair_with_margins_t": ("RSC_P_t", "CCC_S_t")}


def rate(hit: np.ndarray, name: str) -> dict:
    p, n = float(hit.mean()), len(hit)
    se = np.sqrt(p * (1 - p) / n)
    return {name: p, f"{name}_lo": max(0.0, p - 1.96 * se), f"{name}_hi": min(1.0, p + 1.96 * se)}


def t_of(entry) -> float:
    """t statistic of one step: a dict in the 1,508-day study, a [t, p] list in the 2,520-day study."""
    return entry["t"] if isinstance(entry, dict) else entry[0]


def summarise(folder: Path) -> pd.DataFrame:
    rows = []
    for f in sorted(folder.glob("*.jsonl")):
        reps = [json.loads(l) for l in open(f) if l.strip()]
        for a in ("0.05", "0.025"):
            for step, (rich, base) in PAIRS.items():
                t = np.array([t_of(r[a]["dm"][step]) for r in reps])
                d = np.array([r[a]["loss"][rich] - r[a]["loss"][base] for r in reps])
                se = np.abs(d / t)
                row = dict(scenario=reps[0]["scenario"], alpha=float(a), step=step, n_reps=len(reps))
                row.update(rate(t < -ONE, "one_sided"))
                row.update(rate(np.abs(t) > TWO, "two_sided"))
                row.update(rate(t > ONE, "upper_1645"))
                row.update(rate(t > TWO, "upper_196"))
                row.update(mean_diff=d.mean(), mc_se=d.std(ddof=1) / np.sqrt(len(d)), mean_t=t.mean(),
                           mean_se_d=se.mean(), median_se_d=float(np.median(se)),
                           hit_rich=float(np.mean([r[a]["hit"][rich] for r in reps])),
                           hit_base=float(np.mean([r[a]["hit"][base] for r in reps])))
                rows.append(row)
    return pd.DataFrame(rows)


def main():
    s1508 = summarise(LD / "power_1508")
    s1508.to_csv(LD / "power_1508_summary.csv", index=False)
    summarise(LD / "power").to_csv(LD / "power_2520_twosided.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.float_format", lambda x: f"{x:.3f}")
    b = s1508[s1508.alpha == 0.05]
    for col in ("one_sided", "two_sided", "upper_196"):
        print(f"\n{col}, tail level 5% (S0 = size)")
        print(b.pivot_table(index="step", columns="scenario", values=col))
    print("\nS0, one-sided CI")
    print(b[b.scenario.str.startswith("S0")][["step", "one_sided", "one_sided_lo", "one_sided_hi"]].to_string(index=False))
    print("\nreps per scenario:", s1508.groupby("scenario").n_reps.first().to_dict())


if __name__ == "__main__":
    main()
