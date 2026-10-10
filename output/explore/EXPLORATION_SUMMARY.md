# Exploration summary: regime definitions, ETF universes, stock-bond history

For the meeting with Prof. Seo. Descriptive and in-sample, all data through 2019-12-31. 2020-2025 is held out and untouched.
Scripts: `scripts/explore_00..04_*.py`. Tables: `*.json` in this folder.
Specs tried so far: 10 universes x 2 windows, 13 single assets x 2 windows, 7 regime definitions, 1 long-history check. None were dropped.

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

## Caveats

- **Regime weights are smoothed and in-sample.** These are descriptive statistics, not forecasts. They show where a correlation channel exists, not whether the model improves forecasts.
- **Correlations rise in high-volatility regimes partly by construction** (Forbes & Rigobon 2002). The positive shifts for risk assets are therefore an upper bound on true contagion.
- **Block-bootstrap CIs hold the regime weights fixed.** They ignore uncertainty in the HMM fit, so they are narrower than the true uncertainty.
- **VFINX/VUSTX are mutual funds used as proxies.** They are not ETFs, they price once a day, and VUSTX tracks long Treasuries rather than IEF.
- **No forecasting backtest has been run on any new spec yet.**

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
