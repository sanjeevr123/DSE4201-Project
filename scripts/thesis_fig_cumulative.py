"""Figure 7.1: cumulative daily FZ0 loss difference on the hold-out, switching SPY-IEF correlation (RSC_P) minus constant
correlation (CCC), tail level 5%, Gaussian chain. Falling = switching model better. Reads the stored hold-out forecasts
(output/confirm/holdout_forecasts.pkl); refits nothing. Descriptive (POST HOC presentation of the scored series).
Output: output/figures/fig_holdout_cumulative.png
Run: .venv/bin/python scripts/thesis_fig_cumulative.py
"""
import pickle
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import confirm_01_score as S  # noqa: E402

INK, MUTED, GRID, SHADE, SHADE2 = "#111111", "#555555", "#e6e6e6", "#e9e9e9", "#cfcfcf"


def main():
    res = pickle.load(open(ROOT / "output/confirm/holdout_forecasts.pkl", "rb"))
    d = S.losses(res, "RSC_P_N", 0.05) - S.losses(res, "CCC_S_N", 0.05)
    c = pd.Series(d, index=pd.DatetimeIndex(res["dates"])).cumsum()
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    ax.axvspan(pd.Timestamp("2020-02-15"), pd.Timestamp("2020-04-30"), color=SHADE2, lw=0, zorder=0)
    ax.axvspan(pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31"), color=SHADE, lw=0, zorder=0)
    ax.text(pd.Timestamp("2020-05-10"), 2.05, "2020 crash\n(15 Feb-30 Apr)", fontsize=6.5, color=MUTED, va="top")
    ax.text(pd.Timestamp("2022-01-20"), 2.05, "2022: correlation\nturns positive", fontsize=6.5, color=MUTED, va="top")
    ax.axhline(0, color=MUTED, lw=0.8, zorder=1)
    ax.plot(c.index, c.values, color=INK, lw=1.0, zorder=2)
    ax.set_ylabel("Cumulative FZ0 difference", fontsize=7, color=INK)
    ax.tick_params(labelsize=7, colors=INK)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    out = ROOT / "output" / "figures" / "fig_holdout_cumulative.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
