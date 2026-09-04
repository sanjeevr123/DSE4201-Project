# Pilot ETF Exploratory Analysis

**Status: TEMPORARY / PILOT.** This note describes an early-stage pipeline
check and exploratory look at the data, not a final empirical result.

## Dataset

- Tickers (TEMPORARY / PILOT universe): SPY (US equities), IEF (US
  Treasury bonds, ~7-10y), GLD (gold).
- Requested period: 2010-01-01 to 2026-01-01 (yfinance `end` is
  exclusive-ish; actual returned range verified below).
- Actual returned range: **2010-01-04 to 2025-12-31**, 4,024 daily
  observations per ticker.
- Source: Yahoo Finance, accessed via the third-party `yfinance` package
  (version 1.2.0). `yfinance` is an independent, community-maintained
  interface, **not** an official Yahoo Finance API. This is a
  provisional pilot data source; final thesis data-source validation is
  a later task.
- Acquisition used `auto_adjust=False` and `actions=True`, so `Close`
  and `Adj Close` remain distinct and dividends/splits/capital gains
  were requested where available.
- Raw snapshot: `data/raw/pilot_etf_yahoo_2010_2025.csv` (immutable,
  27 columns: OHLC, Adj Close, Volume, Dividends, Stock Splits, Capital
  Gains, for each of the 3 tickers).
- Metadata/provenance: `data/metadata/pilot_etf_yahoo_2010_2025_metadata.json`
- Raw-data validation report: `data/metadata/pilot_etf_yahoo_2010_2025_validation_report.json`

### Validation results

- No missing `Adj Close` values for SPY, IEF, or GLD (0 of 4,024 rows
  each).
- No duplicate dates; the date index is monotonically increasing.
- No zero or negative adjusted prices for any ticker.
- All three tickers already share an identical trading-date index over
  this period, so **no dates were lost or dropped** when building the
  common adjusted-price panel — this was checked explicitly (0 dates
  lost), not assumed.

No cleaning, filling, dropping, or alteration of the raw data was
performed.

## Why adjusted prices are used

`Adj Close` incorporates dividends and other corporate actions, so
day-to-day changes in it reflect the actual total return an investor
would have earned, rather than only the price change. Since `SPY` in
particular pays regular dividends, using unadjusted `Close` would
understate its true historical return. `Close` is preserved in the raw
file for reference but is not used for the return calculations below.

## Return construction

Two return definitions were calculated from the adjusted-price panel
(`data/processed/pilot_adjusted_prices.csv`), for learning and
cross-validation:

- **Simple return:** R_t = P_t / P_(t-1) - 1
  (`data/processed/pilot_simple_returns.csv`)
- **Log return:** r_t = log(P_t) - log(P_(t-1))
  (`data/processed/pilot_log_returns.csv`)

Both were manually validated against hand-computed values at several
dates (see `tests/test_returns.py`); all checks matched to within
1e-6.

## Equal-weight portfolio

A TEMPORARY / PILOT fixed equal-weight portfolio (w = [1/3, 1/3, 1/3]
across SPY/IEF/GLD, no rebalancing logic, no optimisation) was built
from the **simple** asset returns directly:

    portfolio_return_t = (1/3) * SPY_t + (1/3) * IEF_t + (1/3) * GLD_t

This is the exact equal-weight simple portfolio return — it was **not**
constructed by averaging log returns. Manually checked against three
sample dates in `tests/test_returns.py`; all matched to within 1e-9.
Saved to `data/processed/pilot_portfolio_returns.csv`.

## Summary statistics

Daily simple returns, full sample (n = 4,023 return observations after
the leading NaN from differencing). Full table:
`outputs/tables/pilot_return_summary.csv`.

| Series | Mean (daily) | Std (daily) | Min | Max | Skew | Excess kurtosis | Ann. mean | Ann. vol |
|---|---|---|---|---|---|---|---|---|
| SPY | 0.000577 | 0.010841 | -0.1094 | 0.1050 | -0.33 | 12.10 | 0.145 | 0.172 |
| IEF | 0.000116 | 0.004178 | -0.0251 | 0.0264 | 0.05 | 2.32 | 0.029 | 0.066 |
| GLD | 0.000369 | 0.009964 | -0.0878 | 0.0490 | -0.42 | 4.36 | 0.093 | 0.158 |
| Equal-weight portfolio | 0.000354 | 0.005219 | -0.0450 | 0.0463 | -0.16 | 7.52 | 0.089 | 0.083 |

Annualisation assumption: 252 trading days/year
(mean x 252, std x sqrt(252)). These annualised figures are simple
scalings of the sample daily moments over 2010-2025 and should not be
read as forward-looking return/risk forecasts.

Consistent with the diversification intuition covered so far: the
equal-weight portfolio's daily standard deviation (0.0052) is lower
than SPY's (0.0108) or GLD's (0.0100) alone, and also below the simple
average of the three individual standard deviations — an early,
descriptive illustration of the benefit of combining imperfectly
correlated assets, not a general claim about this specific weighting
being optimal.

## Correlations

Pearson correlation of daily simple returns, full sample
(`outputs/tables/pilot_return_correlations.csv`):

| | SPY | IEF | GLD |
|---|---|---|---|
| SPY | 1.00 | -0.26 | 0.05 |
| IEF | -0.26 | 1.00 | 0.28 |
| GLD | 0.05 | 0.28 | 1.00 |

SPY and IEF show a negative correlation over this sample, consistent
with the conventional "equities vs. Treasuries" diversification
narrative, though this is a single unconditional full-sample estimate
and says nothing about whether that relationship is stable through
time. GLD's correlation with both SPY and IEF is small in magnitude.
No formal dependence testing was performed.

## Volatility clustering

The 21-trading-day trailing rolling standard deviation of the
equal-weight portfolio's daily simple return
(`outputs/figures/pilot_21d_rolling_volatility.png`,
`outputs/tables/pilot_21d_rolling_volatility.csv`) is **not constant
over time**: it ranges from roughly 0.0015 in quiet periods up to about
0.022 during the sharpest spike in the sample (around early 2020). It
also rises noticeably around 2011-2012, mid-2013, 2018, 2022, and in a
sharp brief spike around 2025. Periods of elevated rolling volatility
tend to persist for multiple weeks rather than appearing as isolated
single-day spikes, which is visually consistent with volatility
clustering in this sample.

This rolling statistic is explicitly a **backward-looking descriptive
calculation** using only trailing (not centred) windows — the value at
date t uses only returns dated at or before t. It is not, by itself, a
one-day-ahead volatility forecast.

## Return ACF versus squared-return ACF

Computed with `statsmodels.graphics.tsaplots.plot_acf`, 40 lags, on the
equal-weight portfolio's daily simple return (n = 4,023 observations;
approximate 95% significance band ≈ ±0.031):

- **Returns** (`outputs/figures/pilot_acf_returns.png`): sample
  autocorrelations at lags 1-40 are small in magnitude (e.g. lag 1:
  -0.011, lag 2: 0.034, lag 5: 0.005, lag 20: -0.016) and mostly sit
  inside or only marginally outside the approximate significance band.
  The plot does not show a strong, persistent linear dependence
  structure in the level of returns over this sample.

- **Squared returns** (`outputs/figures/pilot_acf_squared_returns.png`):
  autocorrelations are visibly larger and decay only slowly (e.g. lag
  1: 0.111, lag 2: 0.210, lag 3: 0.167, lag 5: 0.089, lag 10: 0.115,
  lag 20: 0.077), and most of the first ~30 lags sit clearly above the
  significance band before tapering by lag 40.

The sample shows relatively weak serial correlation in the level of
portfolio returns, while squared returns show noticeably stronger and
more persistent autocorrelation. This pattern is consistent with
volatility clustering — the direction of tomorrow's return may be
difficult to predict from past returns alone, while the magnitude of
recent movements appears more persistent. This is a descriptive
reading of a single plot/table, not a formal statistical test of
either claim.

## What this suggests for later volatility modelling

Little persistence in returns themselves does not imply that the
return distribution is constant through time. Here, squared returns
remain positively autocorrelated over many lags, suggesting that large
movements in the pilot portfolio tend to be followed by other
comparatively large movements (in either direction). Together with the
visibly time-varying 21-day rolling volatility above, this provides
empirical motivation for later modelling conditional variance directly
(e.g. EWMA, then GARCH-family models) rather than assuming constant
volatility — but no such model has been fitted here.

## Data limitations

- Yahoo Finance / `yfinance` is a public, convenient pilot source, not
  an official or institutional data vendor; adjustment methodology has
  not been cross-checked against a second provider.
- Single-source, single-universe, single-weighting pilot: results are
  descriptive of this specific SPY/IEF/GLD equal-weight construction
  over 2010-2025 only and should not be generalised.
- Excess kurtosis is high for SPY (12.1) and the portfolio (7.5),
  indicating heavy tails; summary statistics like the mean/std alone
  do not fully characterise this behaviour.
- No formal statistical tests (e.g. Ljung-Box) were run on the ACFs;
  conclusions above are visual/descriptive only, as required by the
  pilot task scope.

## Questions for supervisor

- Is SPY/IEF/GLD an acceptable starting universe, or should the final
  thesis universe include a broader/different asset set?
- Is equal-weighting an acceptable placeholder for the pilot only, and
  what portfolio construction should the thesis ultimately evaluate?
- Given the volatility-clustering pattern observed here, is EWMA the
  right next step before GARCH, or should GARCH be introduced directly?
- Should Yahoo Finance data be cross-validated against another source
  before it is used for the final thesis empirical work?
