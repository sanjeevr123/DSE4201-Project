# Methodology Decision Log

The purpose of this file is to distinguish temporary coding choices
from actual research decisions.

Possible statuses:

- Temporary
- Provisional
- Confirmed with supervisor
- Final/Frozen

| Date | Decision | Status | Working Choice | Reason | Evidence Still Needed | Supervisor Input Needed? |
|---|---|---|---|---|---|---|
| 2026-08-23 | Primary forecast target | Provisional | Fixed ETF portfolio return | Keeps the central forecasting comparison tractable | Understand portfolio construction and confirm research design | Yes |
| 2026-08-23 | Forecast horizon | Provisional | One trading day | Matches daily data and planned VaR/ES evaluation | Confirm literature and methodology | Yes |
| 2026-08-23 | Pilot ETF universe | Temporary | SPY, IEF, GLD | Small multi-asset dataset for learning and pipeline development | Validate data and later choose final universe | No |
| 2026-08-23 | Final regime count | Open | Not selected | Requires understanding of Markov-switching models and identification | Learn regime modelling | Yes |
| 2026-09-04 | Pilot data source | Temporary | Yahoo Finance via yfinance (v1.2.0) | Pipeline validation and preliminary EDA only; not an official Yahoo API | Cross-validate against a second source before final thesis use | Yes |
| 2026-09-04 | Pilot portfolio construction | Temporary | Equal-weight (1/3 each), simple returns, no rebalancing | Simplest possible fixed portfolio for learning and pipeline validation | Confirm final portfolio construction with supervisor | Yes |
| 2026-09-04 | Pilot EDA scope | Temporary | Returns, summary stats, correlations, 21-day rolling vol, return/squared-return ACF only — no GARCH/HMM/VaR/ES/regime models | Understand empirical data before any conditional-variance or regime model is fitted | Discuss findings and next modelling step with supervisor | Yes |
| 2026-11-03 | Pilot portfolio construction (correction of the 2026-09-04 row) | Confirmed with supervisor | Constant weights of 1/3 each, rebalanced daily; "no rebalancing" in the earlier row was wrong as a description of the code | The code computes `R @ w` with the same `w` every day, and all results use it | None | No |
| 2026-11-03 | Primary forecast target, horizon, universe | Confirmed with supervisor | Equal-weight SPY/IEF/GLD portfolio return, one trading day; other universes appear in the exploration only | Approved direction in her November feedback | None | No |
| 2026-11-03 | Regime count and signal | Confirmed with supervisor | Two-state HMM on SPY returns; macro-regime models not added | She said no additional macro-regime models are necessary | Frozen in the preregistration | No |
| 2026-11-03 | Data source | Confirmed with supervisor | Yahoo Finance via yfinance; second vendor not required at this stage; same-vendor limitation stated | "You don't need CRSP at this stage" | Optional check of the NUS library's CRSP access | No |
| 2026-11-03 | Confirmatory test | Provisional until the tag `spec-freeze-v1` | RSC_P_N vs CCC_S_N, tail level 5%, one-sided 5% test, two-sided CI reported | She approved the test and asked for hypothesis, sidedness and exact specification before the run | Frozen specification, 3-working-day window | Yes |
| 2026-11-03 | Title | Provisional | "Regime-Switching Risk Models for ETF Portfolios: Do Market-State Shifts Improve Tail-Risk Forecasting?" | Allocation extension dropped; she allowed narrowing | Official title-change process | No |
| 2026-11-03 | Portfolio-allocation extension | Final/Frozen | Dropped from scope | See `docs/decisions_log.md`, ladder entry | None | No |

