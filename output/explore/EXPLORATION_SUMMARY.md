# Exploration summary: regime definitions, ETF universes, stock-bond history

For the meeting with Prof. Seo. Descriptive and in-sample, all data through 2019-12-31. 2020-2025 is held out and untouched.
Scripts: `scripts/explore_00..07_*.py`. Tables: `*.json` / `*.csv` in this folder.
Specs tried so far: 10 universes x 2 windows, 13 single assets x 2 windows, 7 regime definitions, 1 long-history check (descriptive); then walk-forward backtests of 10 ETF universes x 10 regime definitions plus 1 long-history sample x 7 regime definitions, each at 2 alpha levels with 4 covariance variants and 5 benchmarks (214 headline correlation-channel tests). None were dropped.

## Three findings

**1. The pilot universe has no correlation channel to detect, and neither does any diversified one.**
In stress, Treasuries become *more* negatively correlated with SPY (IEF: -0.30 to -0.63). Risk assets become *more* positively correlated (EEM, VNQ, DBC, HYG, XLE, XLU: +0.15 to +0.38). In a mixed universe the two shifts cancel.
- Bond-containing universes (SPY/IEF/GLD, SPY/TLT/GLD, SPY/IEF/HYG, the 8-asset multi-asset set): correlation falls in stress, by -0.05 to -0.22.
- Equity-only or risk-asset universes (global equity, sectors, HYG/EEM/VNQ/DBC): correlation rises by +0.13 to +0.39. Sectors have the largest correlation share of the vol increase (14-24%).

*Figures:* `fig_universe_A_pair_corr.png`, `fig_universe_B_universes.png`.

**2. How regimes are defined barely matters if they are volatility-based, and all of them miss the same episode.**
- The SPY HMM, the SPY+VIX HMM, VIX >= 20 and top-quartile realised vol give the same picture. Stress share is 22-41%, the correlation share of the vol increase is about -14% to -18%, and the stress prob series correlate 0.69-0.76 with the baseline.
- All of them miss the 2013 taper tantrum (stress prob 0.00-0.17). It was a bond-led shock, so equity volatility did not flag it.
- The 3-state HMM's top state only captures the GFC and the 2011 downgrade (4% of days), so it would need a different "stress" definition.
- The joint SPY+IEF+GLD HMM is unstable: 4.5-day average runs and 16 switches per year. It is probably fitting noise, so it would need a persistence prior.
- A correlation-defined regime (top tercile of the 63-day SPY-IEF correlation) is the *only* one that flags the taper tantrum (stress prob 0.68). It is a different regime, not a better volatility regime. It also fires in calm 2017 (0.42), and it ignores the GFC (0.08), when bonds hedged strongly.

*Figure:* `fig_regimes_C_timelines.png`.

**3. The thesis's motivating regime (positive stock-bond correlation) is absent from the entire development window.**
Using long-history funds (VFINX vs VUSTX), the 252-day stock-bond correlation was positive on **91% of days in 1988-1999, 24% in 2000-2009 and 0% in 2010-2019**. The 2022 reversal can only be tested in the held-out 2020-2025 period. Exploration data can say nothing about whether the model detects it.

*Figure:* `fig_longhistory_D_stock_bond_corr.png`.

## Backtest results (walk-forward VaR/ES, FZ0 loss, forecasts 2010-2019; 1992-2019 for the long-history sample)

Engine check: the generalised engine reproduces the pilot's WP3 loss table to within 5e-6 (`explore_05_backtests.py --validate`). Scores: `backtest_loss_table.csv`, `backtest_dm_table.csv`; figure `fig_backtest_E_corr_channel.png`. Universes containing HYG (U3, U7, U10) start forecasting in 2012 because HYG history is short. Model D = regime-specific volatilities and correlations, B = regime-specific volatilities only, A = pooled single normal.

**4. Regime models beat the pooled normal but never beat smooth benchmarks.**
- D beats A significantly in 105 of 214 comparisons and is never significantly worse.
- D is never significantly better than GARCH-t or DCC-t (0 of 214 each) and is significantly worse in 96 (GARCH-t) and 124 (DCC-t) of them. The few negative differences against DCC-t have p of 0.58 to 0.95.
- DCC-t and GARCH-t are statistically indistinguishable in 9 of 11 samples. DCC-t is a little better in U4 and U7.

**5. The correlation channel (D vs B) is not detectable, and its sign depends on the regime signal.**
- 37 of 214 tests have raw p < 0.05, against about 11 expected under no effect. They split 18 favouring D and 19 favouring B, and none survive a Holm correction (smallest adjusted p = 0.14).
- The sign follows the signal: equity-volatility HMMs favour D in the equity-heavy universes U8 and U10 (-9 to -12 per 1000). Bond-aware rules (MOVE, yield vol, IEF vol, correlation) favour B in the same universes (+4 to +13). In bond-containing universes (U1, U2, U3) D is usually slightly better, up to -18 per 1000 for the correlation rule in U3.
- The sample cannot resolve the effect. The median minimum detectable FZ0 difference (80% power) is 0.009 at the 5% level and 0.012 at 2.5%, against a median observed |D-B| of 0.003.
- Pseudo-holdout 2016-2019 looks the same: 22 of 100 tests have p < 0.05, with mixed signs.

**6. Direction A (long history) does not rescue the correlation channel.**
In the 1992-1999 era, when stock-bond correlation was positive, D-B is within +/-7 per 1000 for six of seven signals (e.g. HMM_SPY2 -5.6, RULE_RV75 -6.3) and +11.5 for RULE_CORR. It is positive (D worse) in 2000-2009 for every signal, and negative in 2010-2019. A correlation-switching model does not help even in the regime the thesis is about, using this fund proxy and these regime signals. 2022 remains untested.

**7. Direction B (bond-aware signals) gives no consistent gain over the equity-vol signals.**
The SPY+IEF HMM, IEF vol, yield-change vol and MOVE rules beat the SPY HMM on D-A in a few universes (e.g. MOVE and SPY+IEF HMM in U2 and U7) and lose in others, with no consistent pattern. The correlation rule is the extreme case: D is no better than A in most universes (D-A from -12 to +20 per 1000) because that rule carries little volatility information. Its only clear win is D vs B in U3 (-18 per 1000), where it is also the signal that flagged the taper tantrum.

**Reading.** Taken together with findings 1-3, the exploration points toward direction D as the honest headline: the correlation-regime hypothesis is not testable with power on 2010-2019 data, and no specification tried here changes that. The remaining question for the held-out period is whether 2022 behaves differently, and a single stock-bond reversal episode gives little statistical power either.

## Caveats

- **Regime weights are smoothed and in-sample.** These are descriptive statistics, not forecasts. They show where a correlation channel exists, not whether the model improves forecasts.
- **Correlations rise in high-volatility regimes partly by construction** (Forbes & Rigobon 2002). The positive shifts for risk assets are therefore an upper bound on true contagion.
- **Block-bootstrap CIs hold the regime weights fixed.** They ignore uncertainty in the HMM fit, so they are narrower than the true uncertainty.
- **VFINX/VUSTX are mutual funds used as proxies.** They are not ETFs, they price once a day, and VUSTX tracks long Treasuries rather than IEF.
- **Backtest p-values are unadjusted except the Holm correction on the headline D-vs-B family.** The 10 regime definitions and 11 samples were all examined, so any single positive result would need that correction before it is cited. Backtest samples overlap heavily (the same SPY and bond series appear in most universes), so the 214 tests are not independent.
- **Benchmarks are refit on a different schedule than the regime models** (GARCH-t and DCC every 63 days, HMM every 21), which does not favour the regime models. Regime models are not tuned to beat them.

## Candidate directions

| | Direction | Why | Cost |
|---|---|---|---|
| A | Move the development sample back to 1986 (funds/index proxies), so it contains a positive stock-bond regime. | It is the only way to *develop* a correlation-regime model on the phenomenon the thesis is about before testing on 2022. | Data proxy quality; a slow structural shift, not a fast regime. |
| B | Keep a modern ETF sample but add a bond-aware or correlation-defined regime signal (rates, MOVE, rolling stock-bond correlation). | It addresses the taper-tantrum blind spot and could also detect 2022. | Mechanical overlap between "regime" and "correlation." |
| C | Use an equity-heavy or risk-asset universe (sectors, global equity, HYG/EEM/VNQ/DBC), where a correlation channel exists. | It tests the D-vs-B question on a universe where the effect is at least present. | Less relevant to the "diversified portfolio" framing; Forbes-Rigobon caveat. |
| D | Report power and detectability as the headline result. | It matches the pilot's strongest finding and is a safe fallback. | Weaker as a thesis contribution. |

## Questions for the supervisor

1. Is extending the development sample back before ETFs existed (direction A) acceptable, given the proxy-quality caveats?
2. Should the regime signal itself include bond or correlation information (direction B)? Is that circular for testing a correlation-regime hypothesis?
3. Are risk-asset or sector universes (direction C) still on-topic for "diversified ETF portfolio," or should the universe stay multi-asset?
4. Is the plan acceptable to keep 2020-2025 fully held out, with every spec tried logged?
