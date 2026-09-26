# WP5: Literature Positioning

Maps each pilot finding to the closest published result. Citations are
restricted to `docs/literature_briefing.md` plus the two entries verified
via web search and logged in `docs/decisions_log.md` (Ardia et al. 2018;
Forbes & Rigobon 2002). Anything not directly traceable to a pilot result
or the briefing is marked [UNVERIFIED].

## Santos, Nogales & Ruiz (2013) vs Fortin, Simonato & Dionne (2023)

The pilot's evidence sits between these two camps rather than confirming
either outright, and the split maps onto *which* result you look at.

WP2's simulation shows the D-vs-B ablation has real statistical power to
detect a correlation-channel improvement **when the DGP genuinely contains
a correlation-breakdown regime**: 52.5% power in the strong-breakdown
scenario (S2, stylised DGP, n=200, alpha=0.05), 42.0% under the
real-data-calibrated DGP. This is consistent with the Santos et al. camp
— changing correlation *can* add detectable value to VaR/ES forecasts,
given a big enough regime shift and enough data.

But WP3's real-data backtest (2010-2015, the locked-safe pilot window)
finds no significant difference between D and B (DM t=-0.469, p=0.639).
This null lands squarely in the Fortin et al. camp. The pilot's own
descriptive attribution explains why: the Shapley decomposition of the
calm-to-stress portfolio-vol increase over 2010-2015 assigns a **negative**
correlation share (-13.1%) — in this window, stress made SPY/IEF/GLD
correlations *more* diversifying (equity-bond correlation moved from -0.33
calm to -0.51 stress), not less. There simply wasn't a correlation
breakdown for D to detect. Fortin et al. attribute their null partly to
data frequency (weekly vs daily); the pilot's daily, multi-asset null
adds a second, complementary explanation — the null can also be a
property of *which regime the sample happens to contain*, not just of
frequency. Both explanations point the same direction: a null result on
one window is not evidence the correlation channel never matters.

## Paolella, Polak & Walker (2019)

This is the closest published relative — Markov-switching correlation
dynamics for tail-risk forecasting — but their model does not separate
the volatility and correlation channels, which is exactly what the
pilot's simple A/B/C/D ablation is built to do.

The pilot's version of their question gives a more qualified answer than
their headline result implies. Simulated power for the correlation channel
alone (D<B) tops out at 52.5% even in the *strongest* breakdown scenario
with 10 years of data (S2, stylised) — a real but not overwhelming effect,
and one that requires a substantial regime shift to detect reliably.
On real 2010-2015 data, where the correlation channel's Shapley share was
negative, D and B are statistically indistinguishable. This suggests
Paolella et al.'s strong result may depend on either a longer/more
volatile sample, a different (more breakdown-prone) asset universe, or the
combined-with-volatility specification pooling a genuinely strong
volatility effect with a weaker correlation effect. The pilot's simple
decomposition is offered as exactly that: the transparent, weaker-but-
interpretable version of their finding, not a replication of it.

## Ardia, Bluteau, Boudt et al. (2018)

(https://www.sciencedirect.com/science/article/pii/S0169207018300840) —
a large-scale performance study finding regime-switching GARCH does not
uniformly dominate single-regime GARCH across assets and periods.

The pilot's univariate regime-volatility comparison (B/D vs GARCHt)
reproduces this same pattern of inconsistent dominance, and does so even
inside the simulation where the true DGP *is* a two-regime volatility
process: power for B beating GARCHt is only 31.5% in S0 (vol-only,
n=200) and falls to 6.0% in S2 (strong breakdown, where GARCH-t's smooth
adaptation apparently captures much of the same signal). On real
2010-2015 data, B-GARCHt and D-GARCHt are both statistically
indistinguishable (p=0.66, p=0.72). This is consistent with Ardia et
al.'s broad conclusion: even when a plausible regime structure exists,
regime-switching does not reliably beat a well-specified single-regime
GARCH-t benchmark by a wide margin.

## Kinlaw, Kritzman, Page et al. (2021)

Their caution — that naive conditional-correlation measures (e.g.,
correlation computed only across joint-decline days) can overstate crisis
correlation and mislead about what actually matters for a portfolio — is
directly illustrated by the pilot's descriptive regime-conditional
correlations. The naive story ("stocks and bonds correlate more in
crises") does not hold in this sample: equity-bond correlation moves from
-0.33 (calm) to -0.51 (stress) — *more* negative, i.e. more hedging, not
a breakdown. Together with Forbes & Rigobon (2002) — cited here only for
their motivating point that raw crisis-correlation comparisons are an
unreliable way to measure changing dependence — this is exactly why the
thesis design tests the correlation channel through *forecast accuracy*
(the D-vs-B ablation) rather than by comparing conditional correlations
directly. The pilot's real-data finding is a concrete instance of the
problem Kinlaw et al. warn about: a period that looks calm by one
correlation measure can still be forecastable or not forecastable in ways
a raw correlation number would not reveal.

## Summary

| Finding | Camp / source | Pilot result |
|---|---|---|
| Correlation channel has real detectable power given a strong regime shift | Santos et al. (2013) | WP2 S2: 52.5% power (stylised) |
| No significant real-data difference, 2010-2015 window | Fortin et al. (2023) | WP3: DM t=-0.469, p=0.639 |
| Simple ablation gives a weaker, more qualified version of regime-correlation gains | Paolella et al. (2019) | Power caps at ~50%; real-data null |
| Regime-volatility does not uniformly beat single-regime GARCH-t | Ardia et al. (2018) | Sim power 6-32%; real-data p=0.66-0.72 |
| Naive crisis-correlation framing can mislead; forecast accuracy is the right lens | Kinlaw et al. (2021); Forbes & Rigobon (2002, motivating point only) | Real-data eq-bond correlation *more* negative in stress, not less |

[UNVERIFIED]: No claim above extends beyond what is directly computed in
`output/tables/wp2_summary.json`, `wp3_descriptive.json`, and
`wp3_walk_forward.json`, or stated in `docs/literature_briefing.md`.
