"""
Generates the illustrative (non-data) diagrams used in the study guide:
prices-vs-returns, volatility clustering, the 2-state regime diagram, the
mixture-distribution picture, the walk-forward backtest structure, and the
A/B/C/D ablation grid. These are conceptual sketches, not pilot results --
the pilot's own real figures (fig1-fig6) are reused separately.

Run with:
    .venv/bin/python scripts/make_study_guide_diagrams.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "output" / "figures" / "study_guide"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 10, "figure.dpi": 150})


def prices_vs_returns():
    rng = np.random.default_rng(3)
    n = 250
    r = rng.normal(0.0003, 0.01, n)
    p = 100 * np.exp(np.cumsum(r))
    simple_r = p[1:] / p[:-1] - 1

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
    ax1.plot(p, color="#2166ac")
    ax1.set_title("A price series: what you observe day to day")
    ax1.set_ylabel("Price ($)")
    ax2.plot(simple_r, color="#b2182b", linewidth=0.8)
    ax2.axhline(0, color="gray", linewidth=0.5)
    ax2.set_title(r"Its return series: $R_t = P_t / P_{t-1} - 1$ (the day-to-day % change)")
    ax2.set_ylabel("Daily return")
    ax2.set_xlabel("Trading day")
    fig.suptitle("Prices vs. returns", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "prices_vs_returns.png", bbox_inches="tight")
    plt.close(fig)


def vol_clustering():
    rng = np.random.default_rng(7)
    n = 500
    vol = np.ones(n) * 0.006
    vol[100:160] = 0.022
    vol[300:340] = 0.028
    vol = vol + rng.normal(0, 0.0005, n).clip(min=-0.001)
    r = rng.normal(0, 1, n) * vol

    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(r, color="#4d4d4d", linewidth=0.7)
    ax.axvspan(100, 160, color="#b2182b", alpha=0.15, label="turbulent period")
    ax.axvspan(300, 340, color="#b2182b", alpha=0.15)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_title("Volatility clustering: quiet stretches, then a run of large moves")
    ax.set_xlabel("Trading day")
    ax.set_ylabel("Simulated daily return")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "vol_clustering.png", bbox_inches="tight")
    plt.close(fig)


def regime_state_diagram():
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    calm = Rectangle((0.5, 2), 3, 2, facecolor="#d1e5f0", edgecolor="#2166ac", linewidth=1.5)
    stress = Rectangle((6, 2), 3, 2, facecolor="#fddbc7", edgecolor="#b2182b", linewidth=1.5)
    ax.add_patch(calm)
    ax.add_patch(stress)
    ax.text(2, 3, "CALM state\n(state 0)\nlower variance", ha="center", va="center", fontsize=10)
    ax.text(7.5, 3, "STRESS state\n(state 1)\nhigher variance", ha="center", va="center", fontsize=10)

    ax.annotate("", xy=(6, 3.4), xytext=(3.5, 3.4),
                arrowprops=dict(arrowstyle="->", color="#b2182b", lw=1.5))
    ax.text(4.7, 3.7, "switch to stress\n(small probability\neach day)", ha="center", fontsize=8)
    ax.annotate("", xy=(3.5, 2.6), xytext=(6, 2.6),
                arrowprops=dict(arrowstyle="->", color="#2166ac", lw=1.5))
    ax.text(4.7, 2.0, "switch back to calm", ha="center", fontsize=8)

    ax.annotate("", xy=(1.9, 4.3), xytext=(0.6, 4.3),
                arrowprops=dict(arrowstyle="->", color="#2166ac", lw=1.2, connectionstyle="arc3,rad=2.2"))
    ax.text(0.4, 5.0, "stays calm\n(usual case)", ha="center", fontsize=8)
    ax.annotate("", xy=(9.4, 4.3), xytext=(8.1, 4.3),
                arrowprops=dict(arrowstyle="->", color="#b2182b", lw=1.2, connectionstyle="arc3,rad=-2.2"))
    ax.text(9.6, 5.0, "stays stressed\n(persistence)", ha="center", fontsize=8)

    ax.set_title("A 2-state Markov-switching regime: the market is always in\none of two hidden states, which can persist or switch each day")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "regime_state_diagram.png", bbox_inches="tight")
    plt.close(fig)


def mixture_distribution():
    x = np.linspace(-0.06, 0.06, 1000)
    calm = stats.norm.pdf(x, 0.0003, 0.006)
    stress = stats.norm.pdf(x, -0.002, 0.02)
    p_calm, p_stress = 0.85, 0.15
    mix = p_calm * calm + p_stress * stress

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x, calm * p_calm, "--", color="#2166ac", label=f"calm component (weight {p_calm:.0%})")
    ax.plot(x, stress * p_stress, "--", color="#b2182b", label=f"stress component (weight {p_stress:.0%})")
    ax.plot(x, mix, color="black", linewidth=2, label="mixture (the actual forecast distribution)")
    var_level = -0.025
    ax.axvline(var_level, color="#4d4d4d", linestyle=":", linewidth=1.5)
    ax.fill_between(x, mix, where=(x <= var_level), color="#b2182b", alpha=0.3)
    ax.text(var_level, ax.get_ylim()[1] * 0.9, " VaR\n (5% quantile)", fontsize=8, va="top")
    ax.set_title("Two regime-conditional normals, weighted by state probability,\ncombine into one mixture distribution -- VaR/ES come from its left tail")
    ax.set_xlabel("Tomorrow's portfolio return")
    ax.set_ylabel("Density")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "mixture_distribution.png", bbox_inches="tight")
    plt.close(fig)


def walk_forward_diagram():
    fig, ax = plt.subplots(figsize=(7.5, 3.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 5)
    ax.axis("off")

    blocks = [(5, 35, "#d1e5f0", "Estimation window 1\n(1260 days)"),
              (40, 6, "#fddbc7", "forecast\nblock 1\n(21 days)"),
              (11, 35, "#d1e5f0", None),
              (61, 6, "#fddbc7", "forecast\nblock 2\n(21 days)")]
    ax.add_patch(Rectangle((5, 2.5), 35, 1, facecolor="#d1e5f0", edgecolor="#2166ac"))
    ax.text(22.5, 3, "Estimation window 1 (1260 days):\nfit HMM/GARCH here", ha="center", va="center", fontsize=8)
    ax.add_patch(Rectangle((40, 2.5), 6, 1, facecolor="#fddbc7", edgecolor="#b2182b"))
    ax.text(43, 3, "forecast\nblock 1", ha="center", va="center", fontsize=7)

    ax.add_patch(Rectangle((11, 1), 35, 1, facecolor="#d1e5f0", edgecolor="#2166ac", alpha=0.7))
    ax.text(28.5, 1.5, "Estimation window 2 (slides forward 21 days, refit)", ha="center", va="center", fontsize=8)
    ax.add_patch(Rectangle((46, 1), 6, 1, facecolor="#fddbc7", edgecolor="#b2182b"))
    ax.text(49, 1.5, "forecast\nblock 2", ha="center", va="center", fontsize=7)

    ax.annotate("", xy=(70, 1.5), xytext=(52, 1.5),
                arrowprops=dict(arrowstyle="->", color="gray", lw=1))
    ax.text(75, 1.5, "... repeats through\nthe full test period", fontsize=8, va="center")

    ax.set_title("Walk-forward backtest: refit every 21 days, forecast one day\nahead using only data up to that point, then slide the window forward")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "walk_forward_diagram.png", bbox_inches="tight")
    plt.close(fig)


def abcd_grid():
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    cells = [
        (0.5, 5.2, 4.2, 4.2, "A", "Pooled covariance\n(no regime at all)", "#f7f7f7"),
        (5.3, 5.2, 4.2, 4.2, "B", "Volatility varies by\nregime; correlation pooled", "#d1e5f0"),
        (0.5, 0.5, 4.2, 4.2, "C", "Correlation varies by\nregime; volatility pooled", "#fddbc7"),
        (5.3, 0.5, 4.2, 4.2, "D", "BOTH volatility and\ncorrelation vary by regime", "#f4a582"),
    ]
    for x, y, w, h, label, desc, color in cells:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="black"))
        ax.text(x + w / 2, y + h - 0.6, label, ha="center", fontsize=16, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 0.3, desc, ha="center", va="center", fontsize=9)

    ax.text(5.4, 9.9, "Volatility regime-dependent? -->", ha="left", fontsize=9)
    ax.text(-0.3, 5.0, "Correlation\nregime-\ndependent?", ha="center", va="top", fontsize=9, rotation=90)
    ax.annotate("D vs B: the thesis's PRIMARY test\n(isolates the correlation channel,\nholding volatility treatment fixed)",
                xy=(7.4, 2.6), xytext=(0.3, -1.6),
                fontsize=8, ha="left",
                arrowprops=dict(arrowstyle="->", color="#b2182b"))
    ax.set_title("The A/B/C/D covariance-variant ablation")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "abcd_grid.png", bbox_inches="tight")
    plt.close(fig)


def main():
    prices_vs_returns()
    vol_clustering()
    regime_state_diagram()
    mixture_distribution()
    walk_forward_diagram()
    abcd_grid()
    print(f"Saved 6 diagrams to {OUT_DIR}")


if __name__ == "__main__":
    main()
