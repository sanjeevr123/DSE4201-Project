# Chapter draft: Design and Methods

*Working draft. Numbers appear only in the results chapter. Every design choice here is logged in `docs/decisions_log.md`.*

## 1. Research question and design logic

For a fixed diversified portfolio, a forecaster of one-day-ahead tail risk can improve on a plain normal model in three separable ways: (i) let **volatility** depend on a market regime, (ii) let **volatility evolve within a regime** (volatility clustering), and (iii) let **correlations** depend on the regime. The thesis asks which of these, if any, improves out-of-sample Value-at-Risk (VaR) and Expected Shortfall (ES) forecasts, and, as importantly, **how large an improvement this data could ever reveal**.

Each ingredient is added one at a time to a nested "ladder" of models that share the same data, the same regime signal and the same estimation window. Differences in forecast loss between adjacent rungs then attribute the improvement to a single ingredient. This is a controlled ablation: the primary contrast of the original design (model D against model B) is one rung of it.

| Rung | Model | What changes relative to the rung below |
|---|---|---|
| A | Pooled normal (no regimes) | reference |
| B | Regime-specific volatilities, pooled correlation | adds regime volatility |
| D | Regime-specific volatilities and correlations | adds regime correlation (static) |
| CCC | GARCH(1,1) margins, constant correlation | replaces static within-regime variance by volatility dynamics |
| RSC | GARCH(1,1) margins, regime-switching correlation | adds regime correlation on top of dynamic margins |
| DCC | DCC-GARCH | replaces regime-switching by smoothly evolving correlation |
| GARCH-t | Univariate GARCH-t on the portfolio return | portfolio-level benchmark |

## 2. Data and the exploratory/confirmatory split

Daily adjusted closing prices of exchange-traded funds (primary universe SPY, IEF, GLD, equal-weighted without rebalancing) are downloaded once, archived with a SHA-256 hash (`data/raw/MANIFEST.txt`) and never re-pulled. Returns are simple returns from adjusted prices. Three further universes (SPY/IEF/HYG, four sector ETFs, HYG/EEM/VNQ/DBC) serve as robustness checks, and a 1992-2019 mutual-fund sample (VFINX, VUSTX) serves as a pre-ETF replication.

The sample is split in time before any model is evaluated. Development and exploration use data through 31 December 2019 (2016-2019 doubles as a pseudo-holdout). The period 2020-2025, which contains the 2022 reversal of the stock-bond correlation, is a confirmatory hold-out: no specification is fitted or tuned on it, and it is evaluated once, after the specification is frozen and tagged. Every specification tried during exploration is logged, including unpromising ones.

## 3. Regime model

A two-state Gaussian hidden Markov model is fitted to SPY daily returns. States are ordered by variance (state 0 is calm). The model is re-estimated every 21 trading days on a rolling window of 1,260 trading days. For the forecast of day *t*, only the **filtered** state probabilities through day *t*-1 are used, propagated one step through the estimated transition matrix. Smoothed probabilities, which use observations after the forecast date, are never used for forecasting. A unit test perturbs returns after day *t* and checks that forecasts up to *t* are unchanged.

## 4. Covariance models

**Static within-regime models (A, B, D).** On each estimation window, state-*k* moments are the probability-weighted mean and covariance, with weights equal to the in-window state probabilities. A uses one pooled covariance. B takes regime-specific standard deviations but one pooled correlation matrix. D takes the full regime-specific covariance. The portfolio return forecast is a two-component mixture whose weights are the one-step-ahead predictive state probabilities.

**GARCH-margin models (CCC, RSC).** Each asset follows a Gaussian-QML GARCH(1,1) with a constant mean, re-estimated every 63 days and re-filtered daily with those parameters. Standardised residuals are used to estimate a correlation matrix: pooled for CCC, regime-weighted for RSC. The forecast variance of the portfolio is `w' D_t R D_t w`, with `D_t` the diagonal matrix of filtered volatilities and `R` the pooled or regime-specific correlation matrix. For RSC the forecast is the mixture over regimes of the corresponding portfolio distributions.

**Benchmarks.** DCC-GARCH(1,1) with Gaussian (DCC-N) and Student-t (DCC-t) innovations; univariate GARCH(1,1)-t on the portfolio return; historical simulation (500 days) and EWMA (λ = 0.94) in the pilot. For a fixed-weight portfolio, multivariate and univariate EWMA are algebraically identical and are not reported separately.

**Distribution.** Each model is run with Gaussian components and with Student-t components of common degrees of freedom, estimated by maximum likelihood on in-window standardised portfolio returns.

## 5. Controlling the mean

An earlier contrast between GARCH-margin and static models also changed the mean treatment (regime-specific means versus one constant mean). The static arms are therefore re-run with (a) one pooled mean in every regime and (b) zero mean, and the GARCH-margin arms are run with (a) their fitted constant mean and (b) zero mean. The primary comparisons use the pooled-mean versions, so that the static and GARCH-margin arms differ only in how volatility is modelled. The benchmarks keep their own fitted means (a stated limitation).

## 6. Forecast evaluation

VaR and ES are scored jointly with the FZ0 loss of Patton, Ziegel and Chen (2019), for which the pair (VaR, ES) is jointly elicitable (Fissler and Ziegel, 2016). Lower is better. Levels are α = 5% (primary) and 2.5%. Models are compared with the Diebold-Mariano test on the loss difference with Newey-West (Bartlett) errors and automatic lag selection. Calibration is reported alongside loss: hit rates, the Kupiec unconditional coverage test, the Christoffersen independence test and the Acerbi-Székely ES test.

**Reporting effect sizes.** For every comparison the thesis reports the mean loss difference, its standard error and the **minimum detectable difference** at 80% power and a two-sided 5% test, `2.80 x SE`. A non-significant result is read against that number: a difference smaller than the minimum detectable difference is not evidence of no effect.

## 7. Multiple testing

Test families are declared before results are scored. One primary family (the GARCH-margin effect, pooled-mean, Gaussian, α = 5%, full window, four universes) is adjusted by the Holm procedure. Every other comparison is secondary and reported unadjusted, with Holm applied where stated within a universe and chain. Outside the declared families, no p-value is cited as evidence. The ETF universes share most of their data, so results are not pooled across them.

## 8. Power study

The ability of the design to detect a given effect is assessed by simulation. Two data-generating processes are used: the pilot's two-state Markov-switching multivariate Student-t process (constant covariance within regime) and a second process whose margins also follow GARCH(1,1) (`src/dgp_garch.py`). Four scenarios for the stress-regime correlation: vol-only (null), moderate breakdown, strong breakdown, flight to quality. Each replication has 1,260 burn-in days and 2,520 test days, run through the same walk-forward pipeline; 200 replications per scenario. Size is read from the null scenario, power from the others. Simulated numbers describe the simulated process, not markets.

## 9. Reproducibility and correctness

All parameters and seeds are in `config/pilot.yaml`. Walk-forward code is validated by reproducing earlier saved forecasts to numerical precision before any new run is trusted, and the test suite covers the mixture VaR/ES calculation against Monte Carlo, the HMM against simulated data, the FZ0 loss, the Acerbi-Székely statistic, the look-ahead invariant and the locked period. Runs use fixed seeds and archived raw data on a single machine; multi-machine reproducibility is not claimed.

## 10. Known limitations of the design (to be carried into the discussion)

- Regimes are identified from equity returns; a bond-led shock such as the 2013 taper tantrum is not flagged.
- The regime model is a fast volatility regime, while the stock-bond correlation sign appears to be a slow macro state.
- One equal-weight portfolio per universe; the conclusions are conditional on it.
- Regime-model uncertainty is not propagated into the Diebold-Mariano tests.
- The long-history replication uses mutual funds as proxies (daily pricing, long Treasuries in place of IEF).
