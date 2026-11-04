# Chapter draft: Design and Methods

*Working draft, corrected 3 November 2026 after supervisor feedback (changes listed in `notes/outbox/01_correction_note.md`). Numbers appear only in the results chapter. Every design choice here is logged in `docs/decisions_log.md`.*

## 1. Research question and design logic

For a fixed diversified portfolio, a forecaster of one-day-ahead tail risk can depart from a plain normal model in three ways: (i) let **volatility** depend on a market regime, (ii) let **volatility follow GARCH(1,1) dynamics** (not regime-specific in the present specification), and (iii) let **correlations** depend on the regime. The thesis asks which of these, if any, improves out-of-sample Value-at-Risk (VaR) and Expected Shortfall (ES) forecasts, and, as importantly, **how large an improvement this data could ever reveal**.

The models form a sequence of comparisons that share data, regime signal and estimation window. Two of them (D vs B, RSC vs CCC) differ in the correlation matrix only; others also differ in how volatility is modelled and are interpreted as comparisons between model classes. The primary contrast of the original design (model D against model B) is one of these comparisons.

| Model | Description | Compared with | What the comparison changes |
|---|---|---|---|
| A | Pooled normal (no regimes) | reference | |
| B | Regime-specific volatilities, pooled correlation | A | volatility takes two regime-specific levels (nested in volatility) |
| D | Regime-specific volatilities and correlations | B | all correlations regime-specific, static (nested in the correlation matrix) |
| CCC | GARCH(1,1) margins, constant correlation | B | replaces regime-specific static variance by a single-regime GARCH(1,1) (no regime dependence); also changes the correlation input, the mean estimator and the mixture (non-nested) |
| RSC | GARCH(1,1) margins, regime-switching correlation | CCC; D | vs CCC: correlation matrix only (same margins). vs D: a model-class comparison (non-nested) |
| DCC | DCC-GARCH | CCC; RSC | vs CCC: correlation recursion, nested with a = b = 0 on the boundary. vs RSC: two ways of letting correlation move (non-nested) |
| GARCH-t | Univariate GARCH-t on the portfolio return | DCC | portfolio-level benchmark, different information set (non-nested) |

Each model is a forecasting procedure: the model, the rolling window, the refit schedule and the regime-estimation chain together. Comparisons between models are comparisons of these procedures.

## 2. Data and the exploratory/confirmatory split

Daily adjusted closing prices of exchange-traded funds (primary universe SPY, IEF, GLD, equal-weighted with constant weights (1/3 each), i.e. rebalanced daily, with implied turnover ignored) are downloaded once, archived with a SHA-256 hash (`data/raw/MANIFEST.txt`) and never re-pulled. Returns are simple returns from adjusted prices. Three further universes (SPY/IEF/HYG, four sector ETFs, HYG/EEM/VNQ/DBC) are used in the exploration, and a 1992-2019 mutual-fund sample (VFINX, VUSTX) is a further check that reaches back before the ETFs; its 2010-2019 part overlaps the ETF samples in time.

The sample is split in time before any model is evaluated. Development and exploration use data through 31 December 2019. The years 2016-2019 are used as a dry-run window for the confirmatory pipeline; they are not independent of the development choices and are not presented as validation. The period 2020-2025, which contains the 2022 reversal of the stock-bond correlation, is a confirmatory hold-out: no specification is fitted or tuned on it, and it is evaluated once, after the specification is frozen and tagged. Earlier descriptive work displayed summary statistics for 2010-2025, and this is disclosed in the preregistration. Every specification tried during exploration is logged, including unpromising ones.

## 3. Regime model

A two-state Gaussian hidden Markov model is fitted to SPY daily returns. States are ordered by variance (state 0 is calm). The model is re-estimated every 21 trading days on a rolling window of 1,260 trading days. Regime moments in each window are weighted by smoothed in-window probabilities (data up to the window end only). Forecast-day mixture weights are filtered probabilities propagated one step through the estimated transition matrix, so the forecast of day *t* uses data through day *t*-1 only. A unit test perturbs returns after day *t* and checks that forecasts up to *t* are unchanged.

## 4. Covariance models

**Static within-regime models (A, B, D).** On each estimation window, state-*k* moments are the probability-weighted mean and covariance, with weights equal to the smoothed in-window state probabilities. A uses one pooled covariance. B takes regime-specific standard deviations but one pooled correlation matrix of raw returns. D takes the full regime-specific covariance. Volatility is fixed within each 21-day block; only the mixture weights move daily. The portfolio return forecast is a two-component mixture whose weights are the one-step-ahead predictive state probabilities.

**GARCH-margin models (CCC, RSC).** Each asset follows a Gaussian-QML GARCH(1,1) with a constant mean, fitted to the whole window with no regime dependence. Parameters are re-estimated every 63 days. Every 21 days the window is re-filtered with the current parameters, and within a block the one-step variance is updated daily from the realised residual. Standardised residuals are used to estimate a correlation matrix: pooled for CCC, regime-weighted for RSC. The forecast variance of the portfolio is `w' D_t R D_t w`, with `D_t` the diagonal matrix of filtered volatilities and `R` the pooled or regime-specific correlation matrix. CCC uses one Gaussian component and no regime information. For RSC the forecast is the mixture over regimes of the corresponding portfolio distributions, with the same volatilities in both components.

**Benchmarks.** DCC-GARCH(1,1) with Gaussian (DCC-N) and Student-t (DCC-t) innovations; univariate GARCH(1,1)-t on the portfolio return; historical simulation (500 days) and EWMA ($\lambda$ = 0.94) in the pilot. For a fixed-weight portfolio, multivariate and univariate EWMA are algebraically identical and are not reported separately.

**Distribution.** Each model is run with Gaussian components and with Student-t components of common degrees of freedom, estimated by maximum likelihood on in-window standardised portfolio returns. The standardisation differs between families: static arms use the smoothed-probability mixture mean and variance; GARCH-margin arms use the portfolio standard deviation implied by the pooled correlation of the standardised residuals.

## 5. Controlling the mean

An earlier contrast between GARCH-margin and static models also changed the mean treatment (regime-specific means versus one constant mean). The static arms are therefore re-run with (a) one pooled mean in every regime and (b) zero mean, and the GARCH-margin arms are run with (a) their fitted constant mean and (b) zero mean. The primary comparisons use the pooled-mean versions, so that the static and GARCH-margin arms differ in the volatility model; the constant mean is estimated differently (window mean vs QML), which the zero-mean variant addresses. The benchmarks keep their own fitted means (a stated limitation).

## 6. Forecast evaluation

VaR and ES are scored jointly with the FZ0 loss of Patton, Ziegel and Chen (2019), for which the pair (VaR, ES) is jointly elicitable (Fissler and Ziegel, 2016). Lower is better. Tail levels are $\alpha$ = 5% (primary) and 2.5%; the tail level is a property of the forecast, not of a test. Models are compared with the Diebold-Mariano statistic on the loss difference (richer minus baseline; negative means the richer model is better), using a Bartlett kernel with lag floor(4(T/100)^(2/9)) (7 at T = 1,508), the Newey-West (1994) rule of thumb, not their data-driven selection. With a finite rolling window this tests whether two forecasting procedures have equal expected loss over the evaluation sample, in the sense of Giacomini and White (2006). It is not a test of whether the extra parameters of the larger model are zero in the population, and size is therefore checked by simulation. Calibration is reported alongside loss: hit rates, the Kupiec unconditional coverage test, the Christoffersen independence test and the Acerbi-Székely ES test.

**Reporting effect sizes.** For every comparison the thesis reports the mean loss difference, its standard error, a two-sided 95% confidence interval and the **minimum detectable difference** at 80% power and a two-sided 5% test, `2.80 x SE`. Every table labels its sidedness: p-values in the comparison tables are two-sided and rejection rates in the power tables are one-sided at 5%, unless stated otherwise. A non-significant result is read against the interval and that number: a difference smaller than the minimum detectable difference is inconclusive, and a lack of statistically significant improvement is not evidence that the effect is absent.

## 7. Multiple testing

Test families are declared before results are scored. One primary family (the comparison of single-regime GARCH margins with static regime covariance, RSC vs D, pooled-mean, Gaussian, $\alpha$ = 5%, full window, four universes) is adjusted by the Holm procedure. Every other comparison is secondary and reported unadjusted, with Holm applied where stated within a universe and chain. Outside the declared families, no p-value is cited as evidence. The ETF universes share most of their data, so results are not pooled across them.

## 8. Power study

The ability of the design to detect a given effect is assessed by simulation. Two data-generating processes are used: the pilot's two-state Markov-switching multivariate Student-t process (constant covariance within regime) and a second process whose margins also follow GARCH(1,1) (`src/dgp_garch.py`). Four scenarios for the stress-regime correlation: vol-only (null), moderate breakdown, strong breakdown, flight to quality. Each replication of the original study has 1,260 burn-in days and 2,520 test days, run through the same walk-forward pipeline, with 200 replications per scenario; a second study of the GARCH-margin process uses 1,508 test days (the hold-out length) and 500 replications per scenario. Size is read from the null scenario, power from the others, both for a one-sided 5% test unless stated otherwise. Simulated numbers describe the simulated process, not markets.

## 9. Reproducibility and correctness

All parameters and seeds are in `config/pilot.yaml`. Walk-forward code is validated by reproducing earlier saved forecasts to numerical precision before any new run is trusted, and the test suite covers the mixture VaR/ES calculation against Monte Carlo, the HMM against simulated data, the FZ0 loss, the Acerbi-Székely statistic, the look-ahead invariant and the locked period. Runs use fixed seeds and archived raw data on a single machine; multi-machine reproducibility is not claimed.

## 10. Known limitations of the design (to be carried into the discussion)

- Regimes are identified from equity returns; a bond-led shock such as the 2013 taper tantrum is not flagged.
- The regime model is a fast volatility regime, while the stock-bond correlation sign may move more slowly (the literature on this is being checked for the literature chapter).
- One equal-weight portfolio per universe; the conclusions are conditional on it.
- Regime-model uncertainty is not propagated into the Diebold-Mariano tests.
- The long-history sample uses mutual funds as proxies (daily pricing, long Treasuries in place of IEF).
- All ETF data come from one vendor.
