"""
Step 3 of the pilot pipeline: exploratory data analysis.

Reads ONLY the processed data saved by scripts/02_validate_and_build_processed_data.py
(no re-download, no re-validation of raw data).

Produces:
- outputs/tables/pilot_return_summary.csv
- outputs/tables/pilot_return_correlations.csv
- outputs/tables/pilot_21d_rolling_volatility.csv
- outputs/tables/supervisor_pilot_summary.csv
- outputs/figures/pilot_asset_returns.png
- outputs/figures/pilot_portfolio_returns.png
- outputs/figures/pilot_21d_rolling_volatility.png
- outputs/figures/pilot_acf_returns.png
- outputs/figures/pilot_acf_squared_returns.png
- outputs/figures/supervisor_portfolio_volatility_overview.png

Run with:
    .venv/bin/python scripts/03_run_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
from statsmodels.graphics.tsaplots import plot_acf

from src.returns import rolling_volatility

TICKERS = ["SPY", "IEF", "GLD"]
ROLLING_WINDOW = 21
ACF_MAX_LAGS = 40
TRADING_DAYS_PER_YEAR = 252

PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TABLES_DIR = REPO_ROOT / "outputs" / "tables"
FIGURES_DIR = REPO_ROOT / "outputs" / "figures"
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def summarize_series(returns: pd.Series) -> dict:
    """Summary statistics for one daily simple-return series."""
    clean = returns.dropna()
    return {
        "count": int(clean.shape[0]),
        "mean": clean.mean(),
        "std": clean.std(),
        "min": clean.min(),
        "p25": clean.quantile(0.25),
        "median": clean.median(),
        "p75": clean.quantile(0.75),
        "max": clean.max(),
        "skewness": stats.skew(clean),
        "excess_kurtosis": stats.kurtosis(clean, fisher=True),
        "annualised_mean": clean.mean() * TRADING_DAYS_PER_YEAR,
        "annualised_volatility": clean.std() * (TRADING_DAYS_PER_YEAR ** 0.5),
    }


def main() -> None:
    simple_returns = pd.read_csv(
        PROCESSED_DIR / "pilot_simple_returns.csv", index_col="Date", parse_dates=True
    )
    portfolio_returns = pd.read_csv(
        PROCESSED_DIR / "pilot_portfolio_returns.csv", index_col="Date", parse_dates=True
    )["portfolio_return"]

    combined = simple_returns[TICKERS].copy()
    combined["Equal-weight portfolio"] = portfolio_returns

    # --- Section 18: summary statistics ---------------------------------
    summary = pd.DataFrame(
        {name: summarize_series(combined[name]) for name in combined.columns}
    ).T
    summary_path = TABLES_DIR / "pilot_return_summary.csv"
    summary.to_csv(summary_path, index=True, index_label="series")
    print(f"Saved summary statistics: {summary_path}")
    print(summary)

    # --- Section 19: correlation matrix (assets only, simple returns) ---
    corr = simple_returns[TICKERS].dropna().corr(method="pearson")
    corr_path = TABLES_DIR / "pilot_return_correlations.csv"
    corr.to_csv(corr_path, index=True, index_label="ticker")
    print(f"\nSaved correlation matrix: {corr_path}")
    print(corr)

    # --- Section 20: individual ETF return plot --------------------------
    fig, ax = plt.subplots(figsize=(10, 5))
    for ticker in TICKERS:
        ax.plot(combined.index, combined[ticker], label=ticker, linewidth=0.6)
    ax.set_title("Pilot ETF Daily Simple Returns (SPY, IEF, GLD)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily simple return")
    ax.legend()
    ax.axhline(0, color="black", linewidth=0.5)
    fig.tight_layout()
    asset_returns_path = FIGURES_DIR / "pilot_asset_returns.png"
    fig.savefig(asset_returns_path, dpi=150)
    plt.close(fig)
    print(f"\nSaved figure: {asset_returns_path}")

    # --- Section 21: portfolio return plot --------------------------------
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(portfolio_returns.index, portfolio_returns, color="tab:blue", linewidth=0.6)
    ax.set_title("Equal-Weight Pilot Portfolio Daily Simple Returns (TEMPORARY / PILOT)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily simple return")
    ax.axhline(0, color="black", linewidth=0.5)
    fig.tight_layout()
    portfolio_returns_fig_path = FIGURES_DIR / "pilot_portfolio_returns.png"
    fig.savefig(portfolio_returns_fig_path, dpi=150)
    plt.close(fig)
    print(f"Saved figure: {portfolio_returns_fig_path}")

    # --- Section 22: 21-day rolling volatility -----------------------------
    roll_vol = rolling_volatility(portfolio_returns, window=ROLLING_WINDOW)
    roll_vol_path = TABLES_DIR / "pilot_21d_rolling_volatility.csv"
    roll_vol.to_csv(roll_vol_path, index=True, header=["rolling_21d_volatility"])
    print(f"Saved rolling volatility table: {roll_vol_path}")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(roll_vol.index, roll_vol, color="tab:red", linewidth=0.8)
    ax.set_title(
        f"Equal-Weight Portfolio: {ROLLING_WINDOW}-Trading-Day Trailing Rolling "
        f"Volatility (Daily Units)"
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Rolling daily standard deviation")
    fig.tight_layout()
    roll_vol_fig_path = FIGURES_DIR / "pilot_21d_rolling_volatility.png"
    fig.savefig(roll_vol_fig_path, dpi=150)
    plt.close(fig)
    print(f"Saved figure: {roll_vol_fig_path}")

    # --- Section 23: ACF of returns and squared returns ---------------------
    portfolio_clean = portfolio_returns.dropna()
    portfolio_sq_clean = (portfolio_clean ** 2)

    fig, ax = plt.subplots(figsize=(8, 4))
    plot_acf(portfolio_clean, lags=ACF_MAX_LAGS, ax=ax, title="")
    ax.set_title(
        f"ACF of Equal-Weight Portfolio Daily Simple Returns (lags 1-{ACF_MAX_LAGS})"
    )
    ax.set_xlabel("Lag (trading days)")
    ax.set_ylabel("Autocorrelation")
    fig.tight_layout()
    acf_returns_path = FIGURES_DIR / "pilot_acf_returns.png"
    fig.savefig(acf_returns_path, dpi=150)
    plt.close(fig)
    print(f"Saved figure: {acf_returns_path}")

    fig, ax = plt.subplots(figsize=(8, 4))
    plot_acf(portfolio_sq_clean, lags=ACF_MAX_LAGS, ax=ax, title="")
    ax.set_title(
        f"ACF of Squared Equal-Weight Portfolio Returns (lags 1-{ACF_MAX_LAGS})"
    )
    ax.set_xlabel("Lag (trading days)")
    ax.set_ylabel("Autocorrelation")
    fig.tight_layout()
    acf_sq_returns_path = FIGURES_DIR / "pilot_acf_squared_returns.png"
    fig.savefig(acf_sq_returns_path, dpi=150)
    plt.close(fig)
    print(f"Saved figure: {acf_sq_returns_path}")

    # --- Section 29: supervisor summary table --------------------------------
    rows = []
    for name in combined.columns:
        clean = combined[name].dropna()
        rows.append(
            {
                "series": name,
                "start_date": str(clean.index.min().date()),
                "end_date": str(clean.index.max().date()),
                "n_observations": int(clean.shape[0]),
                "mean_daily_return": clean.mean(),
                "daily_volatility": clean.std(),
                "minimum_daily_return": clean.min(),
                "maximum_daily_return": clean.max(),
                "skewness": stats.skew(clean),
                "excess_kurtosis": stats.kurtosis(clean, fisher=True),
            }
        )
    supervisor_summary = pd.DataFrame(rows).set_index("series")
    supervisor_summary_path = TABLES_DIR / "supervisor_pilot_summary.csv"
    supervisor_summary.to_csv(supervisor_summary_path, index=True)
    print(f"\nSaved supervisor summary table: {supervisor_summary_path}")

    # --- Section 30: supervisor figure (rolling volatility overview) ----------
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(roll_vol.index, roll_vol, color="tab:red", linewidth=0.8)
    ax.set_title(
        f"Equal-Weight Pilot Portfolio: {ROLLING_WINDOW}-Day Rolling Volatility "
        f"(SPY/IEF/GLD, 2010-2025, TEMPORARY / PILOT)"
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Rolling daily standard deviation of portfolio return")
    fig.tight_layout()
    supervisor_fig_path = FIGURES_DIR / "supervisor_portfolio_volatility_overview.png"
    fig.savefig(supervisor_fig_path, dpi=150)
    plt.close(fig)
    print(f"Saved figure: {supervisor_fig_path}")

    # --- Diagnostics printed for the final report, not fabricated ---------
    print("\n=== Correlation matrix ===")
    print(corr)
    print("\n=== Portfolio return / squared-return description ===")
    print(f"Portfolio return skewness: {stats.skew(portfolio_clean):.4f}")
    print(f"Portfolio return excess kurtosis: {stats.kurtosis(portfolio_clean, fisher=True):.4f}")


if __name__ == "__main__":
    main()
