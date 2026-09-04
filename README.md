# Regime-Switching Risk Models for ETF Portfolios

## Approved Thesis Title

Regime-Switching Risk Models for ETF Portfolios:
Do Market-State Shifts Improve Tail-Risk Forecasting
and Risk-Controlled Allocation?

## Working Research Question

Does a real-time regime-aware model improve one-day-ahead
tail-risk forecasts for a fixed diversified ETF portfolio relative
to conventional non-regime benchmarks?

This research question is currently provisional and will be refined
with my thesis supervisor.

## Current Project Stage

Week 1 — Foundations, research setup, data pipeline and preliminary analysis.

## Current Pilot Dataset

Initial Day-1 pilot universe:

- SPY — US equities
- IEF — US Treasury bonds
- GLD — gold

Pilot period:

2010-01-01 to 2025-12-31

This is a temporary pilot universe, not the final thesis ETF universe.

## Core Empirical Principle

Every forecast for date t+1 must be constructed using only
information available by date t.

Avoiding look-ahead bias and data leakage is a non-negotiable
requirement of this research project.

## Research Data Flow

Public data source
→ immutable raw snapshot
→ data validation
→ processed prices and returns
→ model inputs
→ forecasts
→ backtests
→ figures and tables

## Pilot Data / EDA

Current temporary pilot:

- SPY, IEF, GLD
- 2010-01-04 to 2025-12-31 (Yahoo Finance via yfinance)
- daily adjusted-price simple and log returns
- equal-weight exploratory portfolio (no rebalancing)
- 21-day trailing rolling volatility, return and squared-return ACF

This is not the final empirical specification. See
`notes/pilot_eda.md` for the full write-up, `notes/decision_log.md`
for status, and `notebooks/01_pilot_data_and_eda.ipynb` for the
reproducible walkthrough. Pipeline: `scripts/01_download_raw_data.py`
→ `scripts/02_validate_and_build_processed_data.py` →
`scripts/03_run_eda.py`.

## Current Open Methodological Decisions

The following are NOT yet final:

- Final ETF universe
- Portfolio construction method
- Two versus three regimes
- Regime-identifying variable
- Markov-switching versus alternative latent-state specification
- Expanding versus rolling estimation window
- Initial estimation-window length
- Benchmark model set
- VaR/Expected Shortfall evaluation design
- Dependence-testing method
- Portfolio-allocation extension

These decisions should not be silently fixed by code.
