"""
WP3: real-data pilot driver. Produces:
  - output/tables/wp3_descriptive.json
  - output/tables/wp3_walk_forward.json
  - output/tables/wp3_stability.json
  - output/tables/wp3_episodes.json
  - output/figures/fig1_regimes.png .. fig6_var_es_bands.png (300 dpi)

Run with:
    .venv/bin/python scripts/wp3_run_real_data_pilot.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.config import get_config
from src.wp3_real_data import (
    W,
    _walk_forward_result,
    descriptive_regime_stats,
    episode_diagnostics,
    load_pilot_prices,
    stability_diagnostics,
    walk_forward_backtest,
)

FIG_DIR = REPO_ROOT / "output" / "figures"
TABLE_DIR = REPO_ROOT / "output" / "tables"


def save_json(obj: dict, name: str) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    with open(TABLE_DIR / name, "w") as f:
        json.dump(obj, f, indent=2, default=float)
    print(f"Saved {TABLE_DIR / name}")


def make_figures(R) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    dates_all = R.index
    cfg = get_config()

    res, dates = _walk_forward_result(R, alpha=0.05)

    # fig1: SPY price with predictive stress probability
    px_spy = (1 + R["SPY"]).cumprod()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax2 = ax.twinx()
    ax.plot(px_spy.index, px_spy.values, lw=1, color="#333", label="SPY (cum. return index)")
    ax2.fill_between(dates, res["stress_prob"], color="#d95f02", alpha=0.3, step="mid")
    ax.set_title("SPY cumulative return and predictive stress-state probability (walk-forward)")
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("P(stress)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_regimes.png", dpi=300)
    plt.close(fig)

    # fig2: rolling 63-day pairwise correlations
    fig, ax = plt.subplots(figsize=(10, 4))
    for a, b in [("SPY", "IEF"), ("SPY", "GLD"), ("IEF", "GLD")]:
        ax.plot(R[a].rolling(63).corr(R[b]), lw=1, label=f"{a}-{b}")
    ax.axhline(0, color="k", lw=0.5)
    ax.legend()
    ax.set_title("Rolling 63-day pairwise correlations (2004-2015)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_correlations.png", dpi=300)
    plt.close(fig)

    # fig3: regime-conditional correlation bars
    desc = descriptive_regime_stats(R)
    pairs = [("SPY", "IEF"), ("SPY", "GLD"), ("IEF", "GLD")]
    tickers = list(R.columns)
    idx_pairs = [(tickers.index(a), tickers.index(b)) for a, b in pairs]
    calm_corr = np.array(desc["regime_conditional_moments"]["calm"]["correlation"])
    stress_corr = np.array(desc["regime_conditional_moments"]["stress"]["correlation"])
    calm_vals = [calm_corr[i, j] for i, j in idx_pairs]
    stress_vals = [stress_corr[i, j] for i, j in idx_pairs]
    x = np.arange(len(pairs))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - 0.18, calm_vals, width=0.36, label="Calm")
    ax.bar(x + 0.18, stress_vals, width=0.36, label="Stress")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}-{b}" for a, b in pairs])
    ax.axhline(0, color="k", lw=0.5)
    ax.legend()
    ax.set_title("Regime-conditional pairwise correlations (2004-2015, in-sample)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_regime_correlations.png", dpi=300)
    plt.close(fig)

    # fig4: cumulative FZ0 loss differences D-B and B-GARCHt
    from src.engine import fz0
    L_D = fz0(res["y"], res["V"]["D"], res["E"]["D"], 0.05)
    L_B = fz0(res["y"], res["V"]["B"], res["E"]["B"], 0.05)
    L_G = fz0(res["y"], res["V"]["GARCHt"], res["E"]["GARCHt"], 0.05)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, np.cumsum(L_D - L_B), label="D - B (correlation channel)")
    ax.plot(dates, np.cumsum(L_B - L_G), label="B - GARCH-t")
    ax.axhline(0, color="k", lw=0.5)
    ax.legend()
    ax.set_title("Cumulative FZ0 loss difference (below zero = first model better)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_cumulative_loss_diff.png", dpi=300)
    plt.close(fig)

    # fig5: power curves from WP2 (if available)
    wp2_path = TABLE_DIR / "wp2_summary.json"
    if wp2_path.exists():
        with open(wp2_path) as f:
            wp2 = json.load(f)
        pvl = wp2.get("power_vs_length", {})
        by_years = pvl.get("by_years", {})
        if by_years:
            years = sorted(int(y) for y in by_years)
            powers = [by_years[str(y)]["D_lt_B"]["power"] for y in years]
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(years, powers, marker="o")
            ax.axhline(0.5, color="k", lw=0.5, ls="--", label="G3 threshold (50%)")
            ax.set_xlabel("Test length (years)")
            ax.set_ylabel("Power of one-sided D<B DM test @5%")
            ax.set_title(f"Power vs test length ({pvl.get('scenario', 'S1')}, stylised DGP)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(FIG_DIR / "fig5_power_curves.png", dpi=300)
            plt.close(fig)
            print("Saved fig5_power_curves.png")
    else:
        print("WP2 summary not found yet -- skipping fig5 (power curves). "
              "Re-run this script after scripts/wp2_run_simulation.py completes.")

    # fig6: VaR/ES forecast bands vs realised returns for B and D
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for ax, model in zip(axes, ["B", "D"]):
        ax.plot(dates, res["y"], color="#333", lw=0.6, label="realised return")
        ax.plot(dates, res["V"][model], color="#d95f02", lw=1, label="VaR (5%)")
        ax.plot(dates, res["E"][model], color="#1b9e77", lw=1, label="ES (5%)")
        ax.set_title(f"Model {model}: VaR/ES forecast bands vs realised portfolio return")
        ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_var_es_bands.png", dpi=300)
    plt.close(fig)

    print(f"Saved figures to {FIG_DIR}")


def main() -> None:
    panel = load_pilot_prices()
    R = panel.pct_change().dropna()
    print(f"Loaded real data: {R.index.min().date()} .. {R.index.max().date()} ({len(R)} days)")

    cfg = get_config()
    alphas = cfg["alphas"]

    print("Running descriptive regime stats...")
    desc = descriptive_regime_stats(R)
    save_json(desc, "wp3_descriptive.json")

    print("Running 2010-2015 walk-forward backtest...")
    wf = walk_forward_backtest(R, alphas)
    save_json(wf, "wp3_walk_forward.json")

    print("Running stability diagnostics (this includes the window/refit sensitivity sweep)...")
    stab = stability_diagnostics(R)
    save_json(stab, "wp3_stability.json")

    print("Running episode diagnostics...")
    ep = episode_diagnostics(R)
    save_json(ep, "wp3_episodes.json")

    print("Generating figures...")
    make_figures(R)


if __name__ == "__main__":
    main()
