"""Figure 7.1: cumulative daily FZ0 loss difference on the hold-out, switching SPY-IEF correlation (RSC_P) minus constant
correlation (CCC), tail level 5%, Gaussian chain. Falling = switching model better. Reads the stored hold-out forecasts
(output/confirm/holdout_forecasts.pkl); refits nothing. Descriptive (POST HOC presentation of the scored series).
Output: output/figures/fig_holdout_cumulative.pdf (and .png)
Run: .venv/bin/python scripts/thesis_fig_cumulative.py
"""
import pickle
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import confirm_01_score as S  # noqa: E402
import thesis_plot_style as st  # noqa: E402


def main():
    st.apply()
    res = pickle.load(open(ROOT / "output/confirm/holdout_forecasts.pkl", "rb"))
    d = S.losses(res, "RSC_P_N", 0.05) - S.losses(res, "CCC_S_N", 0.05)
    c = pd.Series(d, index=pd.DatetimeIndex(res["dates"])).cumsum()
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    ax.axvspan(pd.Timestamp("2020-02-15"), pd.Timestamp("2020-04-30"), color=st.SHADE2, lw=0, zorder=0)
    ax.axvspan(pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31"), color=st.SHADE, lw=0, zorder=0)
    ax.text(pd.Timestamp("2020-05-10"), 2.1, "2020 crash\n(15 Feb-30 Apr)", color=st.MUTED, va="top")
    ax.text(pd.Timestamp("2022-01-20"), 2.1, "2022: correlation\nturns positive", color=st.MUTED, va="top")
    ax.axhline(0, color=st.MUTED, lw=0.6, zorder=1)
    ax.plot(c.index, c.values, color=st.INK, lw=0.9, zorder=2)
    ax.set_ylabel("Cumulative FZ0 difference")
    ax.grid(axis="y", color=st.GRID, lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    st.save(fig, ROOT / "output" / "figures" / "fig_holdout_cumulative")


if __name__ == "__main__":
    main()
