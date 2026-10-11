"""Figures for regime-definition comparison and long-history stock-bond correlation."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "output" / "explore"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# ---- Fig C: stress probability timelines
P = pd.read_csv(OUT / "regime_stress_probs.csv", index_col=0, parse_dates=True)
labels = {"HMM_SPY2": "HMM on SPY, 2 states (baseline)", "HMM_SPY3": "HMM on SPY, 3 states (top state only)",
          "HMM_MV2": "HMM on SPY+IEF+GLD jointly", "HMM_SPYVIX2": "HMM on SPY + VIX",
          "RULE_VIX20": "Rule: VIX >= 20", "RULE_RV75": "Rule: realised vol top quartile",
          "RULE_CORR": "Rule: top-tercile 63d SPY-IEF correlation"}
eps = {"Taper\n2013": ("2013-05-01", "2013-09-30"), "GFC": ("2008-09-15", "2009-03-31"),
       "2011": ("2011-08-01", "2011-10-31"), "Q4\n2018": ("2018-10-01", "2018-12-31")}
fig, axes = plt.subplots(len(labels), 1, figsize=(9, 8.5), sharex=True)
for ax, (k, lab) in zip(axes, labels.items()):
    col = "#c0392b" if k != "RULE_CORR" else "#7d3c98"
    ax.fill_between(P.index, P[k], step="mid", color=col, alpha=.85, lw=0)
    ax.set_ylim(0, 1); ax.set_yticks([]); ax.set_ylabel("")
    ax.text(0.005, 0.78, lab, transform=ax.transAxes, fontsize=9, fontweight="bold")
    a, b = eps["Taper\n2013"]
    ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color="#f1c40f", alpha=.35, lw=0)
axes[-1].xaxis.set_major_locator(mdates.YearLocator(2)); axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.suptitle("Seven ways to define 'stress' on SPY/IEF/GLD (yellow band = 2013 taper tantrum)\n"
             "All volatility-based definitions agree and all miss the taper tantrum; only the correlation-defined regime flags it",
             x=0.01, ha="left", fontsize=10.5)
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(OUT / "fig_regimes_C_timelines.png", dpi=160); plt.close(fig)

# ---- Fig D: long-history rolling stock-bond correlation
L = pd.read_csv(OUT / "longhistory_rolling_corr.csv", index_col=0, parse_dates=True).iloc[:, 0].dropna()
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.plot(L.index, L.values, color="#1f4e79", lw=1.3)
ax.axhline(0, color="black", lw=.8)
ax.fill_between(L.index, 0, L.values, where=L.values > 0, color="#c0392b", alpha=.25, lw=0)
ax.axvspan(pd.Timestamp("2010-01-01"), pd.Timestamp("2019-12-31"), color="grey", alpha=.15, lw=0)
ax.text(pd.Timestamp("2010-06-01"), 0.55, "pilot / exploration\nwindow: corr never > 0", fontsize=8.5)
ax.text(pd.Timestamp("1989-01-01"), 0.72, "1988-1999: stocks and bonds\nmoved TOGETHER (positive corr)", fontsize=8.5, color="#c0392b")
ax.set_ylabel("252-day stock-bond correlation"); ax.set_ylim(-0.9, 0.9)
ax.set_title("A positive stock-bond correlation regime exists in history, but not in 2010-2019\n"
             "(VFINX vs VUSTX, S&P 500 vs long Treasury fund; 2020+ held out)", loc="left", fontsize=10.5)
fig.tight_layout(); fig.savefig(OUT / "fig_longhistory_D_stock_bond_corr.png", dpi=160); plt.close(fig)
print("ok")
