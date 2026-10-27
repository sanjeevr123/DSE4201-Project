"""
Exploratory step 19: forest plot of every ladder step (FZ0 difference, richer minus baseline; negative = richer model
better) per sample, 95% CI, with the minimum detectable difference (80% power) as a grey band. alpha 5%, Gaussian chain,
pooled mean, full window. Output: output/figures/ladder_forest.png (300 dpi). Run: .venv/bin/python scripts/explore_19_ladder_figure.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
dm = pd.read_csv(ROOT / "output" / "explore" / "ladder" / "ladder_dm_table.csv")
d = dm[(dm.alpha == 0.05) & (dm.period == "full") & (dm.mean_set == "pooled") & (dm.chain == "N")]
STEPS = [("regime_vol", "Regime volatility\n(B vs A)"), ("static_corr", "Static regime correlation\n(D vs B)"),
         ("margin_pooledcorr", "GARCH margins, pooled corr.\n(CCC vs B)"),
         ("corr_with_margins", "Regime correlation on GARCH margins\n(RSC vs CCC)"),
         ("regime_vs_smooth", "Regime vs smooth correlation\n(DCC vs RSC)")]
UNIS = [("U1_pilot", "SPY/IEF/GLD"), ("U3_credit", "SPY/IEF/HYG"), ("U8_sectors", "Sectors"),
        ("U10_riskassets", "Risk assets"), ("L1_longhist", "Funds 1992-2019")]
INK, MUTED, GRID, BAND, MARK = "#1f2933", "#6b7280", "#e5e7eb", "#d9dde3", "#2a6fb0"

fig, axes = plt.subplots(len(STEPS), 1, figsize=(8.2, 9.6), sharex=True)
for ax, (step, title) in zip(axes, STEPS):
    for i, (u, label) in enumerate(UNIS):
        r = d[(d.universe == u) & (d.step == step)].iloc[0]
        y = len(UNIS) - 1 - i
        ax.barh(y, 2 * r.mde80, left=-r.mde80, height=0.62, color=BAND, zorder=1)
        ax.plot([r.mean_diff - 1.96 * r.se, r.mean_diff + 1.96 * r.se], [y, y], color=MARK, lw=1.6, zorder=2)
        sig = r.p < 0.05
        ax.plot(r.mean_diff, y, "o", ms=7, mfc=MARK if sig else "white", mec=MARK, mew=1.6, zorder=3)
        ax.text(0.205, y, f"{r.mean_diff:+.4f}  (" + ("p<0.001" if r.p < 0.001 else f"p={r.p:.2f}") + ")", va="center", ha="right", fontsize=8, color=INK)
    ax.axvline(0, color=MUTED, lw=0.8, zorder=0)
    ax.set_yticks(range(len(UNIS)))
    ax.set_yticklabels([l for _, l in UNIS][::-1], fontsize=8.5, color=INK)
    ax.set_title(title, loc="left", fontsize=9.5, color=INK, pad=3)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-0.30, 0.21)
axes[-1].set_xlabel("Mean FZ0 loss difference, richer minus baseline (negative: richer model better)", fontsize=9, color=INK)
fig.suptitle("Where does regime information help? Each rung of the ladder, with what the data can detect",
             x=0.01, ha="left", fontsize=11, color=INK)
fig.text(0.01, 0.005, "Filled marker: raw p < 0.05. Line: 95% CI. Grey band: minimum detectable difference (80% power). "
         "5% VaR/ES, Gaussian chain, pooled mean.", fontsize=7.5, color=MUTED)
fig.tight_layout(rect=(0, 0.02, 1, 0.97))
out = ROOT / "output" / "figures" / "ladder_forest.png"
fig.savefig(out, dpi=300)
print("saved", out)
