# Pilot Decisions Log

Ambiguous choices made while executing docs/PILOT_PROMPT.md, picked
conservatively and logged here per that document's working rules ("If
something is ambiguous, pick the conservative option, write it into
docs/decisions_log.md with a one-line reason, and continue"). This is
separate from `notes/decision_log.md`, which tracks broader thesis-level
methodology decisions outside the pilot's scope.

- **`output/` vs `outputs/`**: created a new `output/` (singular) directory
  for all pilot (WP0-WP5) deliverables, left the pre-existing `outputs/`
  (plural) untouched for the unrelated Day-1 EDA pipeline. Confirmed with
  the user before WP0.

- **Zero-mean bug in `mix_var_es`**: fixed before WP1, by threading the
  regime-conditional mean through `build_variants` into `mix_var_es`
  (`src/engine.py`), rather than leaving A/B/C/D/Oracle zero-mean while
  GARCH-t/HS remain mean-aware. Confirmed with the user before WP0.

- **EWMA vs EWMA_MV are mathematically identical for this design**: for a
  *fixed*-weight portfolio, `w' (lam*Cov + (1-lam)*r r') w == lam*(w'Cov*w) +
  (1-lam)*(w'r)^2`, i.e. the multivariate EWMA's portfolio-projected
  variance recursion is algebraically identical to the univariate EWMA
  recursion on the portfolio return series directly. Confirmed numerically
  (WP3 real-data table: EWMA and EWMA_MV rows are identical to floating-point
  precision). This does not affect the B/D vs EWMA_MV comparisons, which
  remain meaningful (regime models vs. a smooth, non-regime benchmark) —
  but it means the univariate/multivariate EWMA *distinction itself* adds
  no information here, and is not, on its own, a further test of the
  correlation channel the way D vs B is. Reported plainly in the final
  report rather than treated as a redundant "extra confirmation."

- **WP4 "re-run from a clean environment"**: interpreted as re-running each
  deterministic step from its saved inputs (fixed seeds, the archived raw
  data) on the same single development machine, and diffing outputs
  numerically — not provisioning a second physical machine, which is out of
  scope for a one-person pilot on a laptop. Machine specs and package
  versions are recorded so this claim is at least auditable.

- **Data-audit missing-dates check** (`src/audit.py::missing_dates`): uses a
  plain business-day calendar, not an NYSE holiday calendar, so it
  over-counts genuine market holidays as "missing." Conservative in the
  sense that it never under-reports; the audit report is read alongside
  this caveat rather than the check being made holiday-aware, which would
  add an external dependency (a market-calendar package) for a pilot-stage
  audit.

- **Ardia et al. (2018) citation** (named in docs/PILOT_PROMPT.md's WP5 list
  but not present in docs/literature_briefing.md): verified via web search
  rather than left as a bare, unchecked name. Confirmed as Ardia, Bluteau,
  Boudt et al. (2018), "Forecasting risk with Markov-switching GARCH
  models: A large-scale performance study," *International Journal of
  Forecasting* 34(4), 733-747
  (https://www.sciencedirect.com/science/article/pii/S0169207018300840) —
  matches the "regime volatility, univariate" description in the prompt.

- **Forbes & Rigobon (2002)**: only briefly named in
  docs/literature_briefing.md (motivating why the thesis tests correlation
  via forecast accuracy rather than raw crisis-correlation comparisons), not
  described in detail there. Cited only for that motivating point in WP5's
  output/literature_positioning.md, not for specific numeric findings, since
  the briefing gives no further detail and it was not independently
  re-verified.

- **Exploratory vs. confirmatory split (added after the pilot, Oct 2026)**:
  following the supervisor's instruction to explore broadly (alternative
  regime definitions, other ETF types), all post-pilot exploration is
  restricted to data through 2019-12-31 (`src/explore.py` asserts this;
  `scripts/explore_00_download.py` never downloads later data). 2020-2025
  — which contains the 2022 stock-bond correlation reversal motivating the
  thesis — is the confirmatory hold-out: nothing there is looked at until
  the specification(s) to be tested have been fixed and logged. Every
  specification tried in exploration (regime definitions, universes) is
  reported in `output/explore/`, including the unpromising ones, so the
  number of specs tried is auditable. Exploration results are descriptive
  (in-sample smoothed regime weights, block-bootstrap CIs) and are NOT
  evidence for or against the thesis hypothesis.

- **Exploration backtests (Oct 2026)**: generalised walk-forward engine
  (`src/explore_wf.py`) validated against the pilot's WP3 table (all 14
  loss entries within 5e-6) before use. Ran 10 ETF universes x 10 regime
  definitions (+ long-history VFINX/VUSTX x 7), 2 alpha levels, with
  DCC-GARCH benchmarks; adds bond-aware regime signals (^TNX yield vol, ^MOVE,
  IEF vol, SPY+IEF HMM). All specs reported in `output/explore/backtest_*.csv`.
  Result: no detectable correlation-channel gain (0/214 Holm-significant) and
  no regime model beats GARCH-t/DCC-t. 2020-2025 still untouched.

- **Total-correlation check (Oct 2026, <=2019 data)**: rolling 63-day Gaussian
  total correlation (-0.5 log det R) on SPY/IEF/GLD is exactly invariant to
  flipping an asset's sign, was highest in calm 2012H1 (0.40, SPY-IEF rho
  -0.63) and lowest in the 2013 taper tantrum (0.08, rho -0.04). Judged
  unsuitable as the primary dependence measure for the stock-bond question;
  kept as a descriptive summary only. One additional exploratory spec.

- **Exceedance-correlation check (Oct 2026, <=2019 data)**: on SPY/IEF
  (3,804 days) the joint lower-tail version has n=22 (10%) and n=6 (5%), so
  it is unusable; conditioning on the SPY lower tail only gives rho -0.32
  (n=381, 10%) and -0.28 (n=191, 5%, 90% block-bootstrap CI -0.49 to -0.10)
  against a bivariate-normal-implied -0.19 at 10%. Conditioning on a tail
  shrinks correlation toward zero by construction, so values must be
  compared with a normal-implied null. Descriptive use only. One additional
  exploratory spec.

- **Plan steps 1, 2, 2B implemented (Oct 2026, <=2019 data)**: `src/explore_routes.py`
  adds (i) Route M, a weighted Kendall's-tau correlation matrix with nearest-correlation
  repair; (ii) Route P, only the SPY-IEF pair switching (pair fixed in advance by theory,
  not by scanning); (iii) layer 2, GARCH(1,1) margins + constant (CCC) or regime-switching
  (RSC) correlation of the standardised residuals, Gaussian and Student-t innovations, same
  margins in every arm. Validation: layer-1 B and D reproduce the saved pilot-universe
  backtest bit for bit; the power harness reproduces the pilot's WP2 D-vs-B t statistics to
  1e-6 on the same simulated datasets; 9 new unit tests. Pre-declared primary tests: D_M vs B
  and D_P vs B, alpha = 5%, full 2010-2019, provider HMM_SPY2, Holm over the two. Everything
  else (alpha = 2.5%, sub-periods, within-estimator contrasts, the RULE_RV75 sensitivity
  provider, layer 2) is secondary and unadjusted. Specs added: 2 providers x (5 layer-1 + 10
  layer-2 arms) x 2 alphas on one universe, plus 5 arms x 4 scenarios x 200 reps x 2 alphas
  in the power study.

- **Confound check on U3, U8, U10 (Oct 2026, declared before the results were scored)**:
  hypothesis from the U1 result: giving the regime model GARCH margins removes most of the
  gap to GARCH-t/DCC. Pre-declared primary family: RSC_S_N vs D (GARCH margins vs static
  regime covariance, both with regime-switching sample correlation), alpha = 5%, full
  forecast window, SPY HMM, Holm over the three universes. Everything else is secondary and
  unadjusted. Route M / Route P arms are not scored on these universes (the single pair is
  only meaningful for SPY-IEF). HYG-containing universes (U3, U10) start in 2012.
  Result (confound check): GARCH-margin effect -0.039 (U3, p 0.13), -0.036 (U8, p 0.11),
  -0.073 (U10, p 0.001; Holm 0.003); old significant gaps to GARCH-t shrink to within
  +/-0.016, p > 0.12. Direction supports the confound explanation; statistical confirmation is
  strong in one of three universes.
