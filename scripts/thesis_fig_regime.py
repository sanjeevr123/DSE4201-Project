"""Figure 8.1: what the switching model believed on the hold-out against what happened. Descriptive (POST HOC presentation).

Top panel: the predicted probability of the stress state for each forecast day. Bottom panel: the switching model's
calm-state and stress-state SPY-IEF correlation estimates (standardised residuals, re-estimated every 21 days) against the
realised correlation of SPY and IEF returns over the 63 days before each forecast day. Everything is read from the stored
hold-out forecasts (output/confirm/holdout_forecasts.pkl); nothing is refitted.

Writes output/figures/fig_holdout_regime.png and output/confirm/regime_summary.json.
Run: .venv/bin/python scripts/thesis_fig_regime.py
"""
import json
import pickle
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import confirm_01_score as S  # noqa: E402

INK, MUTED, GRID, SHADE, LIGHT = "#111111", "#555555", "#e6e6e6", "#e9e9e9", "#9a9a9a"


def main():
    res = pickle.load(open(ROOT / "output/confirm/holdout_forecasts.pkl", "rb"))
    dates = pd.DatetimeIndex(res["dates"])
    stress = pd.Series(res["L2"]["stress"], index=dates)
    realised = pd.Series(S.lagged_corr(res["prior_returns"], res["returns"]), index=dates)
    cp = res["L2"]["diag"]["corr_pair"]
    keys = sorted(cp)
    first = keys[0]                                   # refit keys are positions in the full return array
    est = pd.DataFrame([(dates[k - first], cp[k]["regime"][0], cp[k]["regime"][1]) for k in keys],
                       columns=["date", "calm", "stress"]).set_index("date")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.3, 4.4), sharex=True, gridspec_kw={"height_ratios": [1, 1.6]})
    for ax in (a1, a2):
        ax.axvspan(pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31"), color=SHADE, lw=0, zorder=0)
        ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
        ax.tick_params(labelsize=7, colors=INK)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    a1.fill_between(stress.index, 0, stress.values, color=LIGHT, lw=0, step="post")
    a1.plot(stress.index, stress.values, color=INK, lw=0.6, drawstyle="steps-post")
    a1.set_ylim(0, 1); a1.set_ylabel("Stress probability", fontsize=7, color=INK)

    a2.axhline(0, color=MUTED, lw=0.8)
    a2.plot(realised.index, realised.values, color=LIGHT, lw=0.9, label="Realised, previous 63 days")
    a2.plot(est.index, est["stress"], color=INK, lw=1.4, drawstyle="steps-post", label="Model estimate, stress state")
    a2.plot(est.index, est["calm"], color=INK, lw=1.0, ls="--", drawstyle="steps-post", label="Model estimate, calm state")
    a2.set_ylim(-0.75, 0.65); a2.set_ylabel("SPY-IEF correlation", fontsize=7, color=INK)
    a2.legend(fontsize=6.5, frameon=False, loc="upper left", ncol=3)
    fig.tight_layout()
    out = ROOT / "output" / "figures" / "fig_holdout_regime.png"
    fig.savefig(out, dpi=300); plt.close(fig)

    y22 = est[est.index.year == 2022]
    summary = {
        "stress_prob_above_half_share_by_year": {str(y): float(g.gt(0.5).mean()) for y, g in stress.groupby(stress.index.year)},
        "stress_corr_min": float(est["stress"].min()), "stress_corr_max": float(est["stress"].max()),
        "stress_corr_2022_min": float(y22["stress"].min()), "stress_corr_2022_max": float(y22["stress"].max()),
        "calm_corr_2022_min": float(y22["calm"].min()), "calm_corr_2022_max": float(y22["calm"].max()),
        "first_positive_stress_estimate": str(est.index[est["stress"] > 0][0].date()) if (est["stress"] > 0).any() else None,
        "realised_corr_max": float(realised.max()),
    }
    (ROOT / "output/confirm/regime_summary.json").write_text(json.dumps(summary, indent=2))
    print("saved", out); print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
