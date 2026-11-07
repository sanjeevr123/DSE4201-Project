"""
Thesis figure: forest plot of the model comparisons (FZ0 difference, richer minus baseline; negative = richer model
better) per sample, with two-sided 95% CI and the minimum detectable difference (two-sided 5%, 80% power) as a grey band.
Each panel has its own x-scale, because the volatility and margin contrasts are about ten times larger than the
correlation contrasts.
Tail level 5%, Gaussian chain, full window. One figure per mean treatment: pooled (Chapter 6), zero and regime (Appendix B).
Labels state what each comparison changes and do not imply a nested sequence. Greyscale. Source:
output/explore/ladder/ladder_dm_table.csv. Output: output/figures/forest_comparisons_{pooled,zero,regime}.png
Run: .venv/bin/python scripts/thesis_fig_forest.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STEPS = [("regime_vol", "B vs A: regime-specific volatility levels (nested in volatility)"),
         ("static_corr", "D vs B: regime-specific correlations, static (nested in the correlation matrix)"),
         ("margin_pooledcorr", "CCC vs B: single-regime GARCH vs static regime variance (non-nested)"),
         ("margin_effect", "RSC vs D: single-regime GARCH vs static regime variance, regime correlations (non-nested)"),
         ("corr_with_margins", "RSC vs CCC: regime correlations, same GARCH margins (nested in the correlation matrix)"),
         ("regime_vs_smooth", "DCC vs RSC: smooth vs regime-weighted correlation (non-nested)")]
UNIS = [("U1_pilot", "SPY/IEF/GLD"), ("U3_credit", "SPY/IEF/HYG"), ("U8_sectors", "Sectors"),
        ("U10_riskassets", "Risk assets"), ("L1_longhist", "Funds 1992-2019")]
INK, MUTED, GRID, BAND = "#111111", "#555555", "#e6e6e6", "#d4d4d4"


def p_label(p: float) -> str:
    return "p<0.001" if p < 0.001 else f"p={p:.3f}"


def forest(d: pd.DataFrame, out: Path):
    steps = [(s, t) for s, t in STEPS if (d.step == s).any()]
    fig, axes = plt.subplots(len(steps), 1, figsize=(6.3, 1.25 * len(steps) + 0.6))
    for ax, (step, title) in zip(axes, steps):
        for i, (u, label) in enumerate(UNIS):
            r = d[(d.universe == u) & (d.step == step)].iloc[0]
            y = len(UNIS) - 1 - i
            ax.barh(y, 2 * r.mde80, left=-r.mde80, height=0.62, color=BAND, zorder=1)
            ax.plot([r.mean_diff - 1.96 * r.se, r.mean_diff + 1.96 * r.se], [y, y], color=INK, lw=1.4, zorder=2)
            ax.plot(r.mean_diff, y, "o", ms=5, mfc=INK if r.p < 0.05 else "white", mec=INK, mew=1.4, zorder=3)
            ax.text(1.01, y, f"{r.mean_diff:+.4f}  ({p_label(r.p)})", va="center", ha="left", fontsize=6.5, color=INK,
                    transform=ax.get_yaxis_transform())
        ax.axvline(0, color=MUTED, lw=0.8, zorder=0)
        ax.set_yticks(range(len(UNIS)))
        ax.set_yticklabels([l for _, l in UNIS][::-1], fontsize=7, color=INK)
        ax.set_title(title, loc="left", fontsize=7, color=INK, pad=3)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        sub = d[d.step == step]
        lo = min((sub.mean_diff - 1.96 * sub.se).min(), -sub.mde80.max())
        hi = max((sub.mean_diff + 1.96 * sub.se).max(), sub.mde80.max())
        pad = 0.08 * (hi - lo)
        ax.set_xlim(lo - pad, hi + pad)
        ax.tick_params(axis="x", labelsize=6.5, colors=INK)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
    axes[-1].set_xlabel("Mean FZ0 loss difference, richer minus baseline (negative: richer model better)", fontsize=7, color=INK)
    fig.tight_layout(rect=(0, 0, 0.8, 1))
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print("saved", out)


def main():
    dm = pd.read_csv(ROOT / "output" / "explore" / "ladder" / "ladder_dm_table.csv")
    base = dm[(dm.alpha == 0.05) & (dm.period == "full") & (dm.chain == "N")]
    for ms in ("pooled", "zero", "regime"):
        forest(base[base.mean_set == ms], ROOT / "output" / "figures" / f"forest_comparisons_{ms}.png")


if __name__ == "__main__":
    main()
