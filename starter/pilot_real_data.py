"""
REAL-DATA PILOT  (run on your own laptop)
=========================================
Runs the thesis pipeline on SPY / IEF / GLD using ONLY data up to 2015-12-31.
The 2016-2025 period is your locked final test and is never loaded here,
so running this pilot does not contaminate the thesis results.

Walk-forward pilot window: 2010-01-01 .. 2015-12-31 (your validation period).

Usage
-----
    pip install yfinance hmmlearn arch scipy statsmodels matplotlib pandas
    python pilot_real_data.py                 # downloads from Yahoo Finance
    python pilot_real_data.py --csv prices.csv  # or use your own adjusted prices
                                               # (columns: Date,SPY,IEF,GLD)

Outputs (folder ./pilot_output):
    raw_prices_yahoo.csv      archived raw download (keep this, never re-pull)
    pilot_summary.txt         all tables
    fig1_regimes.png          SPY price with stress-state probability
    fig2_correlations.png     rolling 63-day correlations
    fig3_cum_loss_diff.png    cumulative FZ0 loss difference D - B (below 0 = D better)
"""
import argparse, os, sys
import numpy as np
import pandas as pd
from pilot_core import (fit_hmm, walk_forward, score, weighted_cov,
                        corr_from_cov)

CUTOFF = "2015-12-31"          # never change: protects the locked test period
PILOT_START = "2010-01-01"
TICKERS = ["SPY", "IEF", "GLD"]
W = np.ones(3) / 3
OUT = "pilot_output"


def load_prices(csv):
    if csv:
        px = pd.read_csv(csv, parse_dates=["Date"], index_col="Date")[TICKERS]
    else:
        import yfinance as yf
        raw = yf.download(TICKERS, start="2004-11-18", end="2016-01-01",
                          auto_adjust=False, progress=False)
        raw.to_csv(os.path.join(OUT, "raw_prices_yahoo.csv"))
        px = raw["Adj Close"][TICKERS]
        # audit: dividend days show up as gaps between Close and Adj Close returns
        close_ret = raw["Close"][TICKERS].pct_change()
        adj_ret = px.pct_change()
        div_days = ((adj_ret - close_ret).abs() > 1e-6).sum()
        print("Days where adjusted != raw return (dividend days):\n", div_days)
    px = px.loc[:CUTOFF].dropna()
    assert px.index.max() <= pd.Timestamp(CUTOFF), "Locked test data leaked!"
    return px


def christoffersen_ind(hits):
    from scipy import stats
    h = hits.astype(int)
    n00 = np.sum((h[:-1] == 0) & (h[1:] == 0)); n01 = np.sum((h[:-1] == 0) & (h[1:] == 1))
    n10 = np.sum((h[:-1] == 1) & (h[1:] == 0)); n11 = np.sum((h[:-1] == 1) & (h[1:] == 1))
    p01 = n01 / max(n00 + n01, 1); p11 = n11 / max(n10 + n11, 1)
    p = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    def ll(a, b, pr):
        pr = min(max(pr, 1e-12), 1 - 1e-12)
        return a * np.log(1 - pr) + b * np.log(pr)
    lr = -2 * (ll(n00 + n10, n01 + n11, p) - ll(n00, n01, p01) - ll(n10, n11, p11))
    return 1 - stats.chi2.cdf(lr, 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--csv", default=None)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    px = load_prices(args.csv)
    R = px.pct_change().dropna()
    dates = R.index
    Rv = R.values
    lines = []
    P = lambda s="": (print(s), lines.append(s))

    P(f"Data: {dates[0].date()} .. {dates[-1].date()}  ({len(R)} days)  cutoff={CUTOFF}")

    # ---------------- 1. descriptive: regime-conditional vols & correlations
    # HMM on SPY, estimated only on data up to the cutoff (in-sample, descriptive)
    hmm = fit_hmm(Rv[:, 0])
    gamma = hmm.predict_proba(Rv[:, :1])
    P("\n1. REGIME-CONDITIONAL MOMENTS (in-sample 2004-2015, descriptive only)")
    P(f"   Stress-state share of days: {gamma[:,1].mean():.1%}")
    P(f"   Expected calm duration: {1/(1-hmm.transmat_[0,0]):.0f} days, "
      f"stress duration: {1/(1-hmm.transmat_[1,1]):.0f} days")
    for k, name in enumerate(["Calm", "Stress"]):
        S, _ = weighted_cov(Rv, gamma[:, k])
        C, d = corr_from_cov(S)
        P(f"   {name:6s} ann. vol  SPY {d[0]*np.sqrt(252):.1%}  IEF {d[1]*np.sqrt(252):.1%}  "
          f"GLD {d[2]*np.sqrt(252):.1%} | corr SPY-IEF {C[0,1]:+.2f}  "
          f"SPY-GLD {C[0,2]:+.2f}  IEF-GLD {C[1,2]:+.2f}")

    # Risk attribution at the regime level (the thesis question in miniature)
    Sc, _ = weighted_cov(Rv, gamma[:, 0]); Ss, _ = weighted_cov(Rv, gamma[:, 1])
    Cc, dc = corr_from_cov(Sc); Cs, ds = corr_from_cov(Ss)
    vol = lambda d, C: np.sqrt(W @ (np.outer(d, d) * C) @ W) * np.sqrt(252)
    base, v_only, c_only, both = vol(dc, Cc), vol(ds, Cc), vol(dc, Cs), vol(ds, Cs)
    P("\n2. PORTFOLIO VOL ATTRIBUTION (calm -> stress)")
    P(f"   Calm: {base:.1%} | vol-only change: {v_only:.1%} | corr-only change: "
      f"{c_only:.1%} | both: {both:.1%}")
    P(f"   Share of the stress increase due to volatility (Shapley avg): "
      f"{0.5*((v_only-base)+(both-c_only))/(both-base):.0%}")

    # ---------------- 3. walk-forward pilot 2010-2015
    start = int(np.searchsorted(dates, pd.Timestamp(PILOT_START)))
    window = min(1260, start)
    P(f"\n3. WALK-FORWARD PILOT {PILOT_START}..{CUTOFF}  (window={window} days, monthly refit)")
    for alpha in (0.05, 0.025):
        res = walk_forward(Rv, W, start=start, window=window, alpha=alpha)
        sc = score(res, alpha)
        P(f"\n   alpha = {alpha}  (VaR {1-alpha:.1%})")
        P(f"   {'model':8s} {'FZ0 loss':>9s} {'hit rate':>9s} {'Kupiec p':>9s} {'Chr. ind p':>10s}")
        for m in res["V"]:
            hits = (res["y"] <= res["V"][m])
            P(f"   {m:8s} {sc['loss'][m]:9.4f} {sc['hit'][m]:9.2%} "
              f"{sc['kupiec_p'][m]:9.3f} {christoffersen_ind(hits):10.3f}")
        P("   Diebold-Mariano (negative t = first model better):")
        for k, (t, p) in sc["dm"].items():
            P(f"     {k:10s} t={t:+.2f}  p={p:.3f}")
        if alpha == 0.05:
            keep = (res, sc)

    # ---------------- figures
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        res, sc = keep
        d = dates[res["idx"]]
        fig, ax = plt.subplots(figsize=(10, 4)); ax2 = ax.twinx()
        ax.plot(px.index, px["SPY"], lw=1, color="#333")
        ax2.fill_between(d, res["stress_prob"], color="#d95f02", alpha=0.3, step="mid")
        ax.set_title("SPY and predictive stress-state probability (walk-forward)")
        ax2.set_ylim(0, 1); fig.tight_layout(); fig.savefig(f"{OUT}/fig1_regimes.png", dpi=150)
        fig, ax = plt.subplots(figsize=(10, 4))
        for a, b in [("SPY", "IEF"), ("SPY", "GLD"), ("IEF", "GLD")]:
            ax.plot(R[a].rolling(63).corr(R[b]), lw=1, label=f"{a}-{b}")
        ax.axhline(0, color="k", lw=0.5); ax.legend(); ax.set_title("Rolling 63-day correlations")
        fig.tight_layout(); fig.savefig(f"{OUT}/fig2_correlations.png", dpi=150)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(d, np.cumsum(sc["L"]["D"] - sc["L"]["B"]), label="D - B (correlation channel)")
        ax.plot(d, np.cumsum(sc["L"]["B"] - sc["L"]["GARCHt"]), label="B - GARCH-t")
        ax.axhline(0, color="k", lw=0.5); ax.legend()
        ax.set_title("Cumulative FZ0 loss difference (below zero = first model better)")
        fig.tight_layout(); fig.savefig(f"{OUT}/fig3_cum_loss_diff.png", dpi=150)
    except Exception as e:
        P(f"(figures skipped: {e})")

    open(f"{OUT}/pilot_summary.txt", "w").write("\n".join(lines))
    print(f"\nSaved to ./{OUT}/")


if __name__ == "__main__":
    main()
