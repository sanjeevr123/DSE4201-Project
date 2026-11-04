# Confirmatory specification (self-registered; frozen by git tag `spec-freeze-v1`)

Status: written 2026-11-04, before the hold-out has been run. Not an entry in an independent registry; the git tag is the only timestamp. The thesis text of Chapters 3 to 5 (`thesis/tex/chapters/`) describes the same design in prose; if they differ, this file governs.

## 1. Question and hypotheses
One test. Let `d_t = FZ0_t(RSC_P_N) - FZ0_t(CCC_S_N)` at tail level alpha = 5%, for every forecast day t in 2020-01-02 to 2025-12-31, and `mu = E[d_t]` the long-run mean loss difference of the two forecasting procedures (finite rolling window; Giacomini-White sense). Negative favours the regime-switching SPY-IEF model.
- H0: mu >= 0. H1: mu < 0.
- The test is of procedures (model, 1,260-day window, refit schedule, HMM chain), not of population parameters.

## 2. Models
Exactly as implemented in `scripts/confirm_00_run.py` and `src/explore_routes.py::run_rs_corr` and described in Chapter 4 (portfolio SPY/IEF/GLD, weights 1/3 constant, simple returns from adjusted close; window 1,260; HMM and covariances refitted every 21 days; GARCH(1,1) Gaussian QML margins refitted every 63 days; two-state Gaussian HMM on SPY, seed 0, cold start at the first block of the run; Gaussian mixture chain; mean = QML constants). CCC_S_N: one component, pooled correlation of standardised residuals. RSC_P_N: two components, only the (SPY, IEF) correlation regime-specific, mixture weights the one-step predictive state probabilities. Differences: components (2 vs 1) and the (SPY, IEF) entry.

## 3. Data and sample
Raw file `data/raw/spy_ief_gld_raw_2026-09-26.csv`, SHA-256 `0ab8c7f353a7223e154cc3ee4cc3656c465dded45c19269fc24efba371150e29`, truncated at 2025-12-31 before any computation. Forecast days: all dates 2020-01-01 to 2025-12-31 with all three prices present; expected n = 1,508. The run is void if the count differs. Missing data: drop, no forward fill.

## 4. Test, level and decision rule
- Loss FZ0 (`src/engine.py::fz0`). Statistic `t = d_bar / SE`, Bartlett HAC, lags floor(4 (T/100)^(2/9)) = 7 at T = 1,508, standard normal reference, no small-sample correction.
- The tail level (5%) and the test size (5%, one-sided) are distinct. Reject H0 if `t < -1.6449`.
- Outcomes in order, each with the frozen sentence in `scripts/confirm_01_score.py::frozen_sentence`: O1 `t <= -1.6449`; O4 `t >= +1.96` ("significantly worse", a statement separate from H0 and H1); O3 (SESOI declared) `d_bar - 1.6449 SE > -0.002`; O2 otherwise. No outcome is worded as an absence of an effect.
- Always reported: d_bar, HAC SE, two-sided 95% CI, one-sided and two-sided p-values (labelled), MDE 2.8016 SE (two-sided) and 2.4865 SE (one-sided), simulated power.
- Smallest effect of interest 0.002 FZ0 units (`output/confirm/sesoi.json`: mean of the 3% over- and understatement penalties, 0.00167, one significant figure; the Student-t(6) variant rounds to 0.001). It is used only in O3. O3 is expected to be unlikely. Equivalence is never claimed.

## 5. Power, declared rules
Simulated power at 1,508 days, 500 replications per scenario (`output/explore/ladder/power_1508_summary.csv`): one-sided size 3.6%; power 18.2% (S1), 35.2% (S2), 2.4% (S3). The test does not change whatever the simulation shows. The low-power rule (first sentence of the results chapter if S2 power < 30%) is not triggered; power is reported prominently regardless. Caveat: simulated SEs of the primary difference (0.0006 under S0) are smaller than real-data SEs (0.0013 to 0.0015), so simulated power does not transfer one-for-one.

## 6. Secondary analyses (unadjusted, labelled secondary, never cited as confirmation)
(1) ladder steps B/A, D/B, CCC/B, RSC/D, RSC/CCC, DCC/RSC, Gaussian chain, pooled mean, alpha 5%; (2) calendar 2022, interval only; (3) Giacomini-White conditional test of the primary pair with instruments {1, lagged 63-day SPY-IEF correlation}; (4) alpha 2.5% and the Student-t chain; (5) SPA against GARCH-t (candidates B, D, RSC, RSC_P; 2,000 bootstrap draws, seed 0); (6) calibration (hit rates, Kupiec, independence, conditional coverage, Acerbi-Szekely Z2 with 5,000-draw simulated p-values). Nothing else is scored. Kendall-matrix arms, HS and EWMA are computed by the pipeline and never scored. No model confidence set. Anything else computed is marked POST HOC and carries no inferential weight.

## 6a. Run protocol
`scripts/confirm_00_run.py holdout` runs once, only after the tag exists, with no uncommitted change to `src/`, `scripts/confirm_*.py` or this file. A valid run has git_head = tag commit, n = 1,508, finite forecasts with ES <= VaR < 0 for the primary arms. A crash before output is written may be repaired under tag `spec-freeze-v1.1` with a log entry that states why the repair does not depend on results; a numerical change after any result is seen is not allowed (both versions would be reported). A completed run is never repeated.

## 7. Frozen file hashes (SHA-256, at writing)
- `scripts/confirm_00_run.py` 918f90d58cab483f8e0a98a9ec45e0b7e5945897904bdafcff9875d123327468
- `scripts/confirm_01_score.py` 84dba9cdfd3f85ed2921e33e61643f3c2af1c4cf227ccd2366029fb8ca1ad293
- `src/engine.py` 7081a6c063c921538a830d6ca621de8f680d1c17dc1f489559e0786643481a2c
- `src/explore_routes.py` 2b0e41871107a2ce6ec36634c33c64a9d09bfd84104ceb50250dde23a943994d
- `src/explore_wf.py` a85090fa74ac776c4bb3f08ac8c6976ec8c5d29143fd576341ac1a8f377ef8e2
- `src/explore_ladder.py` bbe1011e832e9135a4355c7e932995a58d8b03f17333918bcb38952545815ac6
- `src/explore_inference.py` ada839ccea23289540dad76fecb1486e82ea5ae6fd518fbbdbaf1efb52edea4c
- `requirements.txt` e59d7c0f12027b9ffddac4bf1a1eabb920645126550822c8af93cb4bbd093fc3

## 8. Disclosure
- Descriptive EDA and the data audit displayed 2010-2025 summary statistics before the freeze (`notes/pilot_eda.md`, `outputs/tables/supervisor_pilot_summary.csv`). Three unit tests read 2010-2025 pilot returns and passed (now marked `holdout_data`). `tests/test_returns.py` hard-codes returns for 2020-03-10 and 2023-11-01, printed once by accident on 2026-11-03; not used. No model was fitted or tuned on 2020-2025, but the author knows of the 2022 stock-bond reversal.
- The choice of RSC_P over RSC was made from simulated power on a process whose SPY-IEF shift is largest by construction (2,520-day run). The pair was fixed by the stock-bond hypothesis, not by scanning.
- The dry-run chain starts cold at 2016, unlike the exploration chain (median absolute VaR difference about 1.4e-5, maximum 4.8e-4 over GARCH-margin arms); the hold-out starts cold too. Dry-run results enter no argument for the hypothesis.
- Same vendor (Yahoo Finance, `yfinance`) for all ETF data; two downloads agree to 2.5e-6 in daily returns.
- Static D-vs-B tests are oversized under GARCH margins (one-sided size 9.6% at 1,508 days in simulation).
- HMM estimation uncertainty is not carried into the test; null-scenario size stands in. 214 headline exploration tests, 10 ETF universes and 10 regime definitions were examined; all are logged in `docs/decisions_log.md`.
- Self-registration: git tag only, no OSF deposit, no independent timestamp.
