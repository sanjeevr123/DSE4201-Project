"""
Exploratory step 7: figure for the backtest scores. Heatmap of the correlation-channel
test (mean FZ0 of D minus B, x1000; negative = letting correlations switch helped),
alpha = 5%, full forecast window, one cell per (universe, regime definition).

Run: .venv/bin/python scripts/explore_07_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap

OUT = Path(__file__).resolve().parents[1] / "output" / "explore"
D = pd.read_csv(OUT / "backtest_dm_table.csv")
d = D[(D.family == "D_vs_B") & (D.alpha == 0.05) & D.period.isin(["full_2010_2019", "full_1992_2019"])]
mat = d.pivot(index="universe", columns="provider", values="mean_diff") * 1000
sig = d.pivot(index="universe", columns="provider", values="p") < 0.05
cols = ["HMM_SPY2", "HMM_SPY3", "HMM_SPYVIX2", "HMM_SPYIEF2", "RULE_VIX20", "RULE_RV75",
        "RULE_CORR", "RULE_IEFRV75", "RULE_YLDVOL75", "RULE_MOVE75"]
mat, sig = mat[cols], sig[cols]
cmap = LinearSegmentedColormap.from_list("div", ["#2a6f97", "#f2f2f2", "#c8553d"])
fig, ax = plt.subplots(figsize=(10.5, 5.4))
im = ax.imshow(mat.values, cmap=cmap, norm=TwoSlopeNorm(0, -20, 20), aspect="auto")
ax.set_xticks(range(len(cols)), cols, rotation=35, ha="right", fontsize=9)
ax.set_yticks(range(len(mat)), mat.index, fontsize=9)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat.values[i, j]
        if np.isfinite(v):
            ax.text(j, i, f"{v:.1f}" + ("*" if sig.values[i, j] else ""), ha="center", va="center", fontsize=8,
                    color="#222")
ax.set_title("Does letting correlation switch help? Mean FZ0(D) - FZ0(B), x1000, VaR/ES 5%\n"
             "blue = D better, red = D worse, * = DM p<0.05 (unadjusted; none survive Holm)", fontsize=10, loc="left")
fig.colorbar(im, ax=ax, shrink=0.8, label="FZ0 difference x1000")
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_backtest_E_corr_channel.png", dpi=150)
