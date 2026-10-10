"""Figures for the universe screen. Run after explore_01_universe_screen.py."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parents[1] / "output" / "explore"
d = json.load(open(OUT / "universe_screen.json"))
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# --- Fig A: calm -> stress correlation with SPY, per asset (post-2010 window)
singles = d["singles_vs_spy"]
order = sorted(singles, key=lambda a: singles[a]["post2010"]["delta"])
fig, ax = plt.subplots(figsize=(7.5, 5))
for i, a in enumerate(order):
    x = singles[a]["post2010"]
    col = "#c0392b" if x["delta"] > 0 else "#2471a3"
    ax.plot([x["corr_calm"], x["corr_stress"]], [i, i], color=col, lw=2.5, alpha=.8)
    ax.scatter([x["corr_calm"]], [i], color="white", edgecolor=col, zorder=3, s=45)
    ax.scatter([x["corr_stress"]], [i], color=col, zorder=3, s=45)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order)
ax.axvline(0, color="grey", lw=.8)
ax.set_xlabel("Correlation with SPY   (hollow = calm regime, filled = stress regime)")
ax.set_title("Which assets change their SPY correlation in stress? (2010-2019)\n"
             "Treasuries get more negative (hedge); risk assets get more positive", loc="left", fontsize=11)
fig.tight_layout(); fig.savefig(OUT / "fig_universe_A_pair_corr.png", dpi=160); plt.close(fig)

# --- Fig B: change in average pairwise correlation, per universe, both windows
names = list(d["universes"])
fig, ax = plt.subplots(figsize=(8, 5.2))
h = 0.38
for j, (w, c) in enumerate([("full", "#7f8c8d"), ("post2010", "#1f4e79")]):
    for i, n in enumerate(names):
        x = d["universes"][n][w]
        y = i + (j - .5) * h
        ax.barh(y, x["d_avg_pair_corr"], height=h, color=c, label=w if i == 0 else None)
        lo, hi = x["d_avg_pair_corr_ci90"]
        ax.plot([lo, hi], [y, y], color="black", lw=1)
ax.set_yticks(range(len(names))); ax.set_yticklabels(names); ax.invert_yaxis()
ax.axvline(0, color="black", lw=.8)
ax.set_xlabel("Change in avg pairwise correlation, calm to stress\n(black lines: 90% block-bootstrap CI)")
ax.set_title("Where is there a correlation channel?\nDiversified multi-asset universes: correlations FALL in stress", loc="left", fontsize=11)
ax.legend(title="window", frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(OUT / "fig_universe_B_universes.png", dpi=160); plt.close(fig)
print("ok")
