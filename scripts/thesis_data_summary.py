"""Descriptive statistics and the stock-bond correlation figure for the data chapter (Chapter 3).

Reads the frozen raw file data/raw/spy_ief_gld_raw_2026-09-26.csv, truncates it at 2025-12-31, drops dates with a
missing price and computes simple daily returns of SPY, IEF, GLD and the equal-weight portfolio (constant weights 1/3),
exactly as the forecasting code does. Nothing is fitted. Descriptive only.

Writes
  output/tables/data_summary.json                 summary statistics by period
  thesis/tex/generated/tab_data_summary.tex       Table 3.2
  output/figures/fig_spy_ief_corr.png             Figure 3.1: 63-day rolling SPY-IEF correlation, 2005-2025
Run: .venv/bin/python scripts/thesis_data_summary.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "spy_ief_gld_raw_2026-09-26.csv"
ASSETS = ["SPY", "IEF", "GLD"]
PERIODS = {"dev": ("2010-01-01", "2019-12-31"), "holdout": ("2020-01-01", "2025-12-31")}
INK, MUTED, GRID, SHADE = "#111111", "#555555", "#e6e6e6", "#e9e9e9"


def returns() -> pd.DataFrame:
    px = pd.read_csv(RAW, index_col=0, parse_dates=True)[[f"Adj Close_{a}" for a in ASSETS]]
    px.columns = ASSETS
    px = px[px.index <= "2025-12-31"].dropna()
    r = px.pct_change().dropna()
    r["Portfolio"] = r[ASSETS].mean(axis=1)
    return r


def stats(x: pd.Series) -> dict:
    return {"n": int(len(x)), "mean_ann_pct": float(100 * 252 * x.mean()), "vol_ann_pct": float(100 * np.sqrt(252) * x.std()),
            "skew": float(x.skew()), "exkurt": float(x.kurt()), "min_pct": float(100 * x.min()),
            "q05_pct": float(100 * x.quantile(0.05))}


def table(out: dict) -> str:
    def row(name, s):
        return (f"{name} & {s['mean_ann_pct']:.1f} & {s['vol_ann_pct']:.1f} & {s['skew']:.2f} & {s['exkurt']:.1f} & "
                f"{s['min_pct']:.2f} & {s['q05_pct']:.2f} \\\\").replace("-", "$-$")
    lines = []
    for key, label in (("dev", "Development, 2010--2019"), ("holdout", "Hold-out, 2020--2025")):
        n = out[key]["SPY"]["n"]
        lines.append(f"\\multicolumn{{7}}{{l}}{{\\textbf{{{label}}} ({n:,} days; SPY--IEF correlation "
                     f"{out[key]['corr_spy_ief']:.2f})}}\\\\".replace("-0", "$-$0"))
        lines += [row(a, out[key][a]) for a in ASSETS + ["Portfolio"]]
        lines.append("\\midrule")
    lines.pop()
    body = "\n".join(lines)
    return f"""\\begin{{table}}[t]
\\centering\\setstretch{{1}}\\footnotesize\\setlength{{\\tabcolsep}}{{4pt}}
\\caption{{\\uc{{Summary statistics of daily returns}}}}\\label{{tab:data-summary}}
\\begin{{tabular}}{{lrrrrrr}}
\\toprule
 & Mean (\\% p.a.) & Volatility (\\% p.a.) & Skewness & Excess kurtosis & Minimum (\\%) & 5\\% quantile (\\%) \\\\
\\midrule
{body}
\\bottomrule
\\end{{tabular}}
\\tabnote{{Simple daily returns from adjusted closing prices; mean $\\times 252$, volatility $\\times\\sqrt{{252}}$. Portfolio: equal weights, rebalanced daily. The 5\\% quantile is the empirical counterpart of the 5\\% VaR. Source: \\texttt{{output/tables/data\\_summary.json}}, from \\texttt{{scripts/thesis\\_data\\_summary.py}}.}}
\\end{{table}}
"""


def figure(r: pd.DataFrame, path: Path) -> None:
    c = r["SPY"].rolling(63).corr(r["IEF"]).dropna()
    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    for (a, b), lab in ((PERIODS["holdout"], "Hold-out"),):
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=SHADE, lw=0, zorder=0)
        ax.text(pd.Timestamp(a) + pd.Timedelta(days=40), 0.86, lab, fontsize=7, color=MUTED, va="top")
    ax.axvline(pd.Timestamp("2010-01-01"), color=MUTED, lw=0.6, ls="--", zorder=1)
    ax.text(pd.Timestamp("2010-02-15"), 0.86, "Development forecasts", fontsize=7, color=MUTED, va="top")
    ax.axhline(0, color=MUTED, lw=0.8, zorder=1)
    ax.plot(c.index, c.values, color=INK, lw=1.0, zorder=2)
    ax.set_ylim(-0.95, 0.95)
    ax.set_ylabel("Correlation", fontsize=7, color=INK)
    ax.tick_params(labelsize=7, colors=INK)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print("saved", path)


def main() -> None:
    r = returns()
    out = {}
    for key, (a, b) in PERIODS.items():
        s = r[(r.index >= a) & (r.index <= b)]
        out[key] = {k: stats(s[k]) for k in ASSETS + ["Portfolio"]}
        out[key]["corr_spy_ief"] = float(s["SPY"].corr(s["IEF"]))
        c63 = r["SPY"].rolling(63).corr(r["IEF"])
        out[key]["share_rolling63_positive"] = float((c63[(c63.index >= a) & (c63.index <= b)] > 0).mean())
    out["first_return_date"] = str(r.index[0].date())
    out["n_returns_through_2019"] = int((r.index <= "2019-12-31").sum())
    (ROOT / "output" / "tables" / "data_summary.json").write_text(json.dumps(out, indent=2))
    (ROOT / "thesis" / "tex" / "generated" / "tab_data_summary.tex").write_text(table(out))
    figure(r, ROOT / "output" / "figures" / "fig_spy_ief_corr.png")
    print(json.dumps({k: out[k] for k in ("first_return_date", "n_returns_through_2019")}))


if __name__ == "__main__":
    main()
