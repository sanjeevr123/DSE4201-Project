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

- **Ladder / equal-mean control (Oct 2026, declared before any new result was scored; data <= 2019-12-31)**:
  thesis reframed from "does correlation switching help?" to a controlled ablation of WHERE regime information
  helps: ladder A (pooled) -> B (regime vols) -> D (regime vols + corr) -> CCC (GARCH margins, pooled corr) ->
  RSC (GARCH margins, regime corr) -> DCC -> GARCH-t, one shared sample and one shared SPY-HMM regime signal.
  Allocation/economic-value extension dropped from scope (supervisor-facing title to be narrowed).
  New arms (`src/explore_ladder.py`): static arms with an EQUAL (pooled) mean in every regime, and zero-mean
  versions of the static and GARCH-margin arms, each with Gaussian and Student-t components (t df fitted by ML on
  in-window standardised portfolio returns). Reason: the earlier margin-effect contrast (RSC vs D) also changed
  the mean treatment (regime means vs constant mean), so it was not a clean test of the volatility treatment.
  Pre-declared PRIMARY family: GARCH-margin effect under matched means = RSC_S_N vs D (pooled-mean), alpha 5%,
  full forecast window, SPY HMM, universes U1, U3, U8, U10, Holm over the four. Pre-declared SECONDARY (unadjusted,
  Holm within universe x chain where stated): each ladder step in the Gaussian and Student-t chains; zero-mean
  versions; alpha 2.5%; sub-periods 2010-2012 / 2013-2015 / 2016-2019 (HYG universes start 2012, so their first
  sub-period is partial). Decision gate: if the primary margin effect is negative in all four universes and
  Holm-significant in at least two, the ladder is the primary thesis; otherwise the thesis is reframed as a
  detectability study and the margin effect is reported as suggestive. GARCH-t / DCC benchmarks keep their own
  fitted means (not re-run zero-mean); stated as a limitation.

- **Gate result for the ladder primary family (Oct 2026, data <= 2019-12-31)**: GARCH-margin effect under matched
  means (RSC_S_N vs D pooled-mean, 5%, full): U1 -0.026 (p 0.135), U3 -0.041 (0.117), U8 -0.040 (0.075),
  U10 -0.076 (0.0006); Holm 0.23 / 0.23 / 0.22 / 0.0025. Negative in 4/4 but Holm-significant in 1/4, so the
  pre-declared gate (>= 2) is NOT met: the margin effect is reported as suggestive, not established, and the thesis
  framing is "decomposition with detectability" (every ladder step is reported next to its minimum detectable
  difference), not "margin confound proven". The equal-mean control did not change the size of the effect
  (U1 -0.0259 pooled vs -0.0263 regime-mean), so the mean treatment is not the explanation.
- **Replication on the 1992-2009 fund sample (declared before it was run; data <= 2019-12-31)**: the primary contrast
  (RSC_S_N vs D pooled-mean, alpha 5%) is repeated once on the VFINX/VUSTX 50/50 sample, SPY-role HMM, forecasts
  1992-2019 (7,053 days, 2 assets). Single pre-declared test on the full sample; sub-periods 1992-99, 2000-09,
  2010-19 and the other ladder steps are secondary and unadjusted. 1992-2009 is independent of the ETF samples
  (2010-2019 overlaps them in time). Proxy caveats as in output/explore/EXPLORATION_SUMMARY.md.

- **GARCH-DGP power study (declared before it was run)**: `src/dgp_garch.py` simulates a 2-state Markov-switching
  multivariate Student-t DGP whose margins ALSO follow GARCH(1,1) (a = 0.08, b = 0.90, stylised, not estimated; the
  GARCH recursion runs on the regime-scaled return), with the pilot's calm vols, transition matrix, df = 6 and
  scenarios S0 (null) / S1 / S2 / S3 for the stress correlation. 200 replications per scenario, 1260 burn-in + 2520
  test days, same HMM-on-asset-0 regime signal as the pilot, both alphas. Reported per ladder step: rejection rate
  (one-sided, 5%), 95% binomial CI, wrong-sign rate, mean FZ0 difference and its Monte Carlo SE. Pre-declared
  primary power question for the GARCH layer: RSC vs CCC (does regime correlation add anything once margins are
  GARCH?), alpha 5%, Gaussian chain, pooled mean. Size is read from S0. The DGP is an assumption: its numbers
  describe this DGP, not markets.
  Addendum (declared before any GARCH-DGP result existed; the first partial run was discarded and restarted): the
  single-pair variant RSC_P (only SPY-IEF correlation switches, pair fixed by theory) is added to the power study
  as `pair_with_margins` (RSC_P vs CCC). Reason: the choice of the confirmatory correlation test (RSC vs CCC, or
  RSC_P vs CCC) is made from simulated power on the GARCH DGP, before the hold-out is opened.

- **Family-wise tests for "does any regime model beat the smooth benchmark" (declared before running)**: Hansen's SPA
  (arch package, stationary bootstrap, studentised, 2,000 reps, seed 0), per universe, alpha 5%, full window, FZ0 loss,
  Student-t chain, pooled mean: benchmark GARCH-t (and separately DCC-t); candidate set = regime models B, D, RSC, RSC_P.
  Plus the model confidence set (R method, size 10%) over all t-chain rungs. These replace unadjusted one-by-one
  comparisons for the "regimes vs smooth benchmark" claim. The Giacomini-White conditional test (instruments: a
  constant and the lagged 63-day stock-bond correlation) is SECONDARY, run on the long-history sample, where the
  correlation sign varies, for the step RSC vs CCC; ETF samples have almost no positive-correlation days.
  The whole-pipeline bootstrap of HMM estimation uncertainty was NOT built (cost); the null-scenario rejection
  rate of the GARCH-DGP power study (which includes HMM estimation) stands in as the size check, and the gap
  is stated as a limitation.

- **GARCH-DGP power study: results (800 of 800 replications; `output/explore/ladder/power_summary.csv`)**. One-sided 5% DM
  rejection rates, 2,520 test days, alpha 5%, Gaussian chain. Size (S0): RSC vs CCC 4.5% (95% CI 1.6-7.4), RSC_P vs CCC
  4.5%, static D vs B 11.0% (6.7-15.3, slightly above nominal under GARCH). Power for RSC vs CCC: S1 22.5%, S2 38.0%,
  S3 3.5%. Power for RSC_P vs CCC (single SPY-IEF pair): S1 27.0%, S2 53.5%, S3 5.5%; at alpha 2.5% S2 is 19.5% vs 9.0%.
  GARCH margin effect (CCC vs B, RSC vs D): 91-97% in every scenario (mean FZ0 difference about -0.09 under this DGP).
  Null wrong-sign rates about 8% for the correlation steps. Selection rule declared earlier (choose the confirmatory
  correlation test by simulated power): RSC_P vs CCC has equal size and higher power (S2 +15.5 points, S1 +4.5, within
  Monte Carlo error in S1), so RSC_P vs CCC is the PROPOSED primary confirmatory test. Not yet frozen. Caveats: the
  simulated stress shifts are largest in the SPY-IEF pair by construction; the power study used 2,520 test days while the
  2020-2025 hold-out has about 1,510, so its power is lower and has not been simulated at that length.
