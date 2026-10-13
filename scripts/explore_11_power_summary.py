"""
Exploratory step 11: aggregate the Route M / Route P power simulation (explore_10) into power / size tables
and a figure. One-sided DM test at the 5% level (reject when t < -1.645, i.e. first model better).
S0 is the null (rejection rate = false-positive rate); S1-S3 are the alternatives. Wrong-sign = rejects in
the opposite direction (t > +1.645).

Run: .venv/bin/python scripts/explore_11_power_summary.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PW = ROOT / "output" / "explore" / "routes" / "power"
Z = 1.6448536269514722
LABEL = {"D-B": "D vs B (all pairs, sample corr.)", "DM-B": "D_M vs B (Route M, Kendall)",
         "DP-B": "D_P vs B (Route P, SPY-IEF only)"}
SC = {"S0_vol_only": "S0 null", "S1_moderate_breakdown": "S1 moderate", "S2_strong_breakdown": "S2 strong",
      "S3_flight_to_quality": "S3 flight-to-quality"}


def main():
    rows = []
    for scen in SC:
        reps = [json.loads(l) for l in open(PW / f"{scen}.jsonl") if l.strip()]
        for a in ("0.05", "0.025"):
            for pair in ("D-B", "DM-B", "DP-B", "DM-BM", "DM-D", "DP-D", "DM-DP"):
                t = np.array([r[a]["dm"][pair][0] for r in reps])
                d = np.array([r[a]["loss"][pair.split("-")[0].replace("DM", "D_M").replace("DP", "D_P")]
                              - r[a]["loss"][pair.split("-")[1].replace("BM", "B_M").replace("DP", "D_P").replace("DM", "D_M")]
                              for r in reps])
                n, k = len(t), int((t < -Z).sum())
                p = k / n
                rows.append(dict(scenario=scen, alpha=float(a), comparison=pair, n_reps=n, power=p,
                                 ci_lo=max(0, p - 1.96 * np.sqrt(p * (1 - p) / n)),
                                 ci_hi=min(1, p + 1.96 * np.sqrt(p * (1 - p) / n)),
                                 wrong_sign=float((t > Z).mean()), mean_loss_diff=d.mean(),
                                 se_loss_diff=d.std(ddof=1) / np.sqrt(n), median_abs_t=float(np.median(np.abs(t)))))
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "output" / "explore" / "routes" / "power_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    d5 = df[(df.alpha == 0.05) & df.comparison.isin(LABEL)]
    cols = {"D-B": "#9a9a9a", "DM-B": "#2a6f97", "DP-B": "#c8553d"}
    xs = np.arange(len(SC))
    for j, (cmp_, c) in enumerate(cols.items()):
        sub = d5[d5.comparison == cmp_].set_index("scenario").loc[list(SC)]
        ax.bar(xs + (j - 1) * 0.26, sub.power * 100, 0.24, color=c, label=LABEL[cmp_],
               yerr=[(sub.power - sub.ci_lo) * 100, (sub.ci_hi - sub.power) * 100], capsize=2, ecolor="#555")
    ax.axhline(5, color="#222", lw=0.8, ls="--"); ax.text(len(SC) - 0.55, 6.2, "nominal 5%", fontsize=8)
    ax.set_xticks(xs, [SC[s] for s in SC]); ax.set_ylabel("rejection rate, one-sided 5% DM test (%)")
    ax.set_title("Power of the correlation-channel test by route (pilot DGP, 10 years of daily data, VaR/ES 5%)",
                 fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(ROOT / "output" / "explore" / "fig_routes_G_power.png", dpi=150)
    pd.set_option("display.width", 220)
    print(df[df.comparison.isin(["D-B", "DM-B", "DP-B", "DM-BM", "DM-DP"])]
          .assign(power=lambda x: (x.power * 100).round(1), wrong_sign=lambda x: (x.wrong_sign * 100).round(1))
          [["scenario", "alpha", "comparison", "n_reps", "power", "wrong_sign", "mean_loss_diff", "median_abs_t"]]
          .round(4).to_string(index=False))


if __name__ == "__main__":
    main()
