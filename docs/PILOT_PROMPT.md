You are running a PILOT STUDY for my one-semester honours thesis (B.Sc. Data Science
& Economics). I have 5 weeks left. The pilot must tell me, with evidence I can show
my supervisor (Prof. Seo, financial econometrics / dependence modelling), whether the
full thesis is (1) feasible, (2) able to detect the effect it is looking for,
(3) reproducible, and (4) meaningful. Then it must say which direction to take.

Start in PLAN MODE: read everything listed under CONTEXT, then propose a plan and
file structure and wait for my approval before writing code.

================================================================
CONTEXT (read first)
================================================================
- docs/literature_briefing.md: literature review, data sources, positioning.
- starter/pilot_core.py, starter/simulate.py, starter/analyze.py,
  starter/pilot_real_data.py: a working prototype from an earlier session.
  REUSE it, but review it critically first. Fix bugs, don't rewrite for style.
  Known things to verify in the starter code:
    * mixture VaR/ES assumes zero means;
    * the HMM warm-starts from the previous refit;
    * GARCH is refit every 63 days and filtered daily in between;
    * the oracle "B" model uses calm correlation in both states.

================================================================
THE THESIS QUESTION
================================================================
For a fixed equal-weight SPY / IEF / GLD portfolio: when tail risk rises in stressed
regimes, does letting cross-asset CORRELATIONS change by regime improve out-of-sample
one-day VaR and Expected Shortfall forecasts BEYOND letting only VOLATILITIES change?
Plain version: is it assets getting more volatile, or diversification breaking
down, that matters for forecasting portfolio losses?

================================================================
CORE DESIGN (do not change without telling me)
================================================================
- Regimes: ONE 2-state Gaussian HMM fitted on SPY daily returns only. States are
  ordered by variance (state 0 = calm). Use only FILTERED / one-step-predictive
  probabilities for forecasts, never smoothed probabilities from beyond the
  forecast date.
- Rolling 1260-day estimation window, refit every 21 trading days.
- Four covariance variants that share the SAME state probabilities:
    A pooled covariance (no regimes)
    B regime-specific volatilities, pooled correlation
    C pooled volatilities, regime-specific correlation
    D regime-specific volatilities AND correlations
  State-specific moments are probability-weighted by the in-window state
  probabilities. Forecast = 2-component normal mixture of the portfolio return;
  VaR by root-finding on the mixture CDF, ES in closed form.
- PRIMARY CONTRAST: D vs B (isolates the correlation channel).
  Secondary contrasts: B vs A, C vs A, and D and B vs GARCH-t.
- Benchmarks:
    * historical simulation (500 days);
    * EWMA lambda=0.94 on the portfolio return;
    * GARCH(1,1) Student-t on the portfolio return (arch package);
    * NEW, to add: multivariate EWMA (full covariance, lambda=0.94) vs univariate
      EWMA of the portfolio. This is the smooth, non-regime analogue of D vs B.
- Levels: alpha = 5% (primary) and 2.5% (Basel/FRTB, secondary).
- Scoring:
    * FZ0 joint VaR/ES loss (Patton, Ziegel & Chen 2019):
      L = -1{y<=v}(v-y)/(alpha*e) + v/e + log(-e) - 1, with v and e negative;
    * Diebold-Mariano tests with Newey-West HAC errors;
    * Kupiec unconditional coverage;
    * Christoffersen independence;
    * the Acerbi-Szekely unconditional ES test (Z2), implemented and unit-tested.

================================================================
DATA RULES (research integrity: non-negotiable)
================================================================
- Download SPY, IEF, GLD daily prices once with yfinance, auto_adjust=False
  (keep both Close and Adj Close), from 2004-11-18 to today.
  Save the raw file to data/raw/ with the download date in the filename and a
  SHA-256 hash in data/raw/MANIFEST.txt. Never re-download; always read the
  archived file.
- Data audit report:
    * missing dates, zero or duplicate prices;
    * returns beyond 8 standard deviations;
    * dividend days (where adjusted and raw returns differ) per ticker;
    * a spot-check of 3 IEF dividend dates against the raw data.
- LOCKED TEST PERIOD 2016-01-01 onwards: the pilot must NEVER compute any forecast,
  loss, regime estimate or statistic on it. Enforce this in code with an assertion
  on every real-data function (data truncated at 2015-12-31), and add a unit test
  that fails if post-2015 data reaches the pipeline. The pilot uses only:
    * 2004-11 to 2009-12 for estimation;
    * 2010-01-01 to 2015-12-31 as the pilot forecast window (my validation period).

================================================================
PILOT WORK PACKAGES (commit after each, clear messages)
================================================================
WP0  Setup
  - Repo structure: src/, tests/, config/, data/raw/, output/, docs/.
  - requirements.txt with pinned versions.
  - config/pilot.yaml holding every parameter and random seed.
  - README with one-command reproduction: `make pilot` or `python -m src.run_pilot`.

WP1  Correctness tests (pytest). Must pass before anything else runs.
  - Mixture VaR/ES vs large Monte Carlo draws (1e6), within 1%.
  - Mixture with identical components reproduces normal VaR/ES exactly.
  - FZ0: the true VaR/ES gives lower expected loss than a biased one, on
    simulated data.
  - HMM recovers the parameters of a simulated 2-state series; label ordering is
    stable.
  - No-look-ahead test: perturb returns after day t; forecasts at t are unchanged.
  - Locked-period test (see data rules).
  - Acerbi-Szekely Z2 approximately 0 under a correct model.

WP2  Simulation power study (the core pilot question: can this design detect the
     effect at all with about 10 years of daily data?)
  - Data-generating process: 2-state Markov-switching multivariate Student-t
    (df=6).
      * Calm daily vols (SPY-like, IEF-like, GLD-like): 0.75%, 0.30%, 0.90%.
      * Stress daily vols: 2.0%, 0.50%, 1.6%.
      * P(calm->calm)=0.99, P(stress->stress)=0.97.
      * Calm correlations (eq-bond, eq-gold, bond-gold): -0.30, 0.05, 0.30.
    These are ASSUMED stylised values. Also calibrate an alternative DGP to the
    2004-2015 real data (in-sample HMM-weighted moments) and run it as a second
    calibration.
  - Scenarios for stress correlations:
      S0 vol-only (same as calm): measures false positives / test size;
      S1 moderate breakdown (0.00, 0.20, 0.30);
      S2 strong breakdown (0.40, 0.40, 0.30);
      S3 flight-to-quality (-0.55, -0.10, 0.40).
  - Each replication: 1260 burn-in + 2520 test days, full walk-forward, all
    models, plus ORACLE models that know the true regime and parameters (the
    upper bound on detectable gain).
  - Replications: run 10 per scenario first and report timing. Then 200 per
    scenario at alpha=5% and 100 at 2.5%, parallelised with joblib across all
    cores, checkpointing each replication to disk so a crash does not lose work.
  - Report per scenario:
      * power of the one-sided D<B DM test at 5%, with binomial confidence
        intervals;
      * false-positive rate in S0;
      * wrong-sign rate;
      * oracle power;
      * mean FZ0 difference with standard errors;
      * regime classification accuracy;
      * average hit rates;
      * Kupiec rejection rates;
      * how often each regime model beats GARCH-t and multivariate EWMA.
  - Extra: power vs test length (5, 10 and 15 years) for S1, so I know how much
    data the effect needs.

WP3  Real-data pilot (2010-2015 only)
  - In-sample descriptive (2004-2015): regime-conditional annualised vols and
    correlations; expected regime durations; portfolio-vol attribution calm ->
    stress into volatility vs correlation shares (Shapley average of the two
    orderings).
  - Walk-forward 2010-2015 for all models at both alphas: the full scoring table
    and DM tests.
  - Stability diagnostics:
      * how often refits flip or collapse states;
      * the distribution of the stress share across refits;
      * sensitivity of the D-B result to window (756 / 1260 days) and refit
        frequency (5 / 21 / 63 days).
      Report these as sensitivity checks, NOT as tuning.
  - Episode diagnostics inside 2010-2015: 2011 US downgrade / euro crisis, 2013
    taper tantrum (a rates shock like 2022, useful as a preview of whether an
    equity-based regime misses bond-driven stress), 2015 August sell-off.
  - Figures (clean, labelled, 300 dpi, saved to output/figures):
      1. SPY price with predictive stress probability;
      2. rolling 63-day pairwise correlations;
      3. regime-conditional correlation bars;
      4. cumulative FZ0 loss differences D-B and B-GARCHt;
      5. power curves from WP2;
      6. VaR/ES forecast bands vs realised returns for B and D.

WP4  Reproducibility check
  - Re-run the entire pilot from a clean environment with the fixed seeds and
    confirm identical numbers (diff the result files).
  - Re-run WP2 with a different master seed and confirm conclusions hold within
    Monte Carlo error.
  - Record runtime and machine specs.

WP5  Literature grounding (short)
  - Using docs/literature_briefing.md, write output/literature_positioning.md
    (about 1 page) mapping each pilot finding to the closest published result:
      * Santos et al. 2013 and Fortin et al. 2023 (split evidence);
      * Paolella et al. 2019 (closest regime-correlation study);
      * Ardia et al. 2018 (regime volatility, univariate);
      * Forbes & Rigobon 2002 and Kinlaw et al. 2021 (correlation measurement).
  - Only cite works in the briefing. If you use web search to check a claim,
    give the URL. NEVER invent citations, numbers or findings. Mark anything
    unverified as [UNVERIFIED].

================================================================
PRE-REGISTERED GO / NO-GO CRITERIA
================================================================
Write these into docs/preregistration.md and commit BEFORE running WP2/WP3. Judge
the results against them honestly afterwards.
  G1 Pipeline correctness: all WP1 tests pass.
  G2 Test size: false-positive rate for D<B in S0 is at most 10%.
  G3 Detectability: power of D<B is at least 50% in S1 OR S2 with 10 years of
     data. If power is below 30% even in S2 -> the correlation question is
     under-powered.
  G4 Regime stability on real data: the HMM identifies a persistent stress state
     (expected duration of at least 5 days, stress share 10-40%) in at least 90%
     of refits, without label flips.
  G5 Reproducibility: WP4 reproduces identical numbers.
  G6 Feasibility: the full thesis run (2016-2025, both alphas, all models) is
     estimated to take under 2 hours on my machine.
Decision rules:
  - All pass -> PROCEED with the full design (Option B).
  - G3 fails, others pass -> REFRAME: keep the design but make the thesis an
    honest power-aware attribution study, with the volatility-only regime model
    vs GARCH-t as the primary forecasting test.
  - G4 fails -> FALLBACK: reduce to SPY/IEF, use a 1-state vs 2-state volatility
    comparison, or switch to a smooth-correlation (EWMA/DCC) contrast.
  - G1, G5 or G6 fails -> fix before anything else.
Do NOT change the criteria after seeing results. If you think one is badly
chosen, say so in the report, but judge against the original.

================================================================
FINAL DELIVERABLE: output/PILOT_REPORT.md (3-4 pages, supervisor-ready)
================================================================
Sections:
 1. Question and why a pilot (3 sentences)
 2. What was run (design summary, one paragraph + one table)
 3. Results
    a. correctness;
    b. simulation power (table + power figure);
    c. real-data 2010-2015 (descriptive + forecasting table);
    d. stability;
    e. reproducibility.
 4. Go/no-go scorecard: each criterion, pass/fail, evidence.
 5. What this means: recommended direction and why (proceed / reframe /
    fallback), including an honest statement of the smallest effect the design
    can detect.
 6. Limitations of the pilot:
      * simulation assumptions;
      * a short validation window;
      * Gaussian mixture vs fat tails;
      * equity-only regime signal.
 7. Next steps: a 4-week plan with weekly deliverables and the decisions I need
    from Prof. Seo.
Also export PILOT_REPORT.pdf (pandoc or similar) with figures embedded.

================================================================
WORKING RULES
================================================================
- Show me the plan first. Then pause after WP1, and again after the 10-rep WP2
  timing run, with a 5-line status each time.
- Never tune any parameter to improve a result. All choices come from config and
  are fixed before the runs.
- Report nulls and failures plainly. A clear negative result is a success for a
  pilot.
- Numbers in the report must be read from the result files, not typed by hand.
  Generate the tables programmatically.
- Keep code readable: docstrings, type hints, no notebook-only logic (a notebook
  in notebooks/ for exploration is fine).
- If something is ambiguous, pick the conservative option, write it into
  docs/decisions_log.md with a one-line reason, and continue.
