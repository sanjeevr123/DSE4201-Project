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
