# Pilot Pre-Registration

Transcribed verbatim from `docs/PILOT_PROMPT.md` ("PRE-REGISTERED GO / NO-GO
CRITERIA"), committed before WP2/WP3 begin. These criteria are judged
honestly against the results once WP2/WP3 are run — see that section's
instruction: "Do NOT change the criteria after seeing results. If you think
one is badly chosen, say so in the report, but judge against the original."

## Criteria

- **G1 Pipeline correctness**: all WP1 tests pass.
- **G2 Test size**: false-positive rate for D<B in S0 is at most 10%.
- **G3 Detectability**: power of D<B is at least 50% in S1 OR S2 with 10
  years of data. If power is below 30% even in S2 -> the correlation
  question is under-powered.
- **G4 Regime stability on real data**: the HMM identifies a persistent
  stress state (expected duration of at least 5 days, stress share 10-40%)
  in at least 90% of refits, without label flips.
- **G5 Reproducibility**: WP4 reproduces identical numbers.
- **G6 Feasibility**: the full thesis run (2016-2025, both alphas, all
  models) is estimated to take under 2 hours on my machine.

## Decision rules

- All pass -> **PROCEED** with the full design (Option B).
- G3 fails, others pass -> **REFRAME**: keep the design but make the thesis
  an honest power-aware attribution study, with the volatility-only regime
  model vs GARCH-t as the primary forecasting test.
- G4 fails -> **FALLBACK**: reduce to SPY/IEF, use a 1-state vs 2-state
  volatility comparison, or switch to a smooth-correlation (EWMA/DCC)
  contrast.
- G1, G5 or G6 fails -> fix before anything else.

## Status

- **G1**: PASS. Evidence: `pytest tests/ -v` — 41/41 tests pass (7 new WP1
  correctness test files, plus the pre-existing `test_returns.py` and
  `test_date_alignment.py` unmodified), run on 2026-09-26 against
  `src/engine.py` (the reviewed-and-fixed copy of `starter/pilot_core.py`).
- **G2**: PASS. Evidence: `output/tables/wp2_summary.json`, S0_vol_only
  (no correlation breakdown), one-sided D<B Diebold-Mariano test at nominal
  5%, n=200 replications per DGP. Stylised DGP: 5.0% rejection rate (95% CI
  [2.0%, 8.0%]) — essentially exact nominal calibration. Calibrated DGP:
  2.0% (95% CI [0.1%, 3.9%]) — conservative (under-rejects). Both well under
  the 10% ceiling.
- **G3**: PASS (primary DGP). Evidence: `output/tables/wp2_summary.json`,
  D<B power at alpha=0.05, n=200/scenario. Stylised DGP (primary
  calibration): S1_moderate_breakdown 25.5%, S2_strong_breakdown 52.5% —
  S2 clears the 50% bar. Calibrated DGP (secondary, real-data-fitted
  parameters): S1 16.5%, S2 42.0% — neither clears 50% under this DGP,
  though S2 stays above the 30% under-powered floor. Judged against the
  primary (stylised) DGP per the criterion as written; the calibrated-DGP
  shortfall is carried forward as a report caveat, not used to fail G3.
- **G4**: PASS (marginal). Evidence: `output/tables/wp3_stability.json`,
  72 monthly refits over the 2010-2015 real-data window. 0/72 collapsed
  refits, 0/72 large stress-share jumps between refits (no label flips).
  Expected stress-state duration ranges 44.6-96.8 days per refit (all far
  above the 5-day floor). Stress share in-window: mean 17.6%, range
  [7.7%, 24.2%]. Joint criterion (duration >=5d AND stress share in
  [10%,40%] AND no flip from previous refit): met in 65/72 refits = 90.3%,
  clearing the 90% bar by 0.3 points. The 7 failing refits fail only on the
  stress-share band (a few points below 10%), not on duration or flips.
- **G5**: PASS. Evidence: `output/tables/wp4_reproducibility.json`. WP1:
  41/41 tests pass on rerun. WP3: full rerun (descriptive, walk-forward,
  episodes) numerically identical to the committed tables (tolerance
  1e-9). WP2: a 5-replication-per-scenario subset recomputed directly
  (bypassing the checkpoint) is bit-identical to the checkpointed values
  (0 mismatches, rtol 1e-8). A reduced 50-replications-per-scenario batch
  under a different master seed (999,999 vs the main run's 0) gives the
  same qualitative ranking across scenarios (S2 strongest, S0/S3 near-null)
  and stays within the pre-declared wide tolerance (|power diff| < 0.25)
  for all 4 scenarios — a genuine independent recomputation, not a
  checkpoint replay (an earlier version of this check accidentally reused
  the main run's checkpoint file, since `checkpoint_path` keys only on
  `(dgp, scenario, alpha, T)` and not on seed; fixed in
  `scripts/wp4_reproducibility_check.py` to call `one_rep` directly,
  bypassing that cache). Honest scope caveat (already logged in
  `docs/decisions_log.md`): single-machine reproducibility only, not
  multi-machine.
- **G6**: PASS. Evidence: the full real-data pipeline analogue (descriptive
  stats + primary walk-forward backtest + full window/refit sensitivity
  sweep of 6 combinations + 3 episode diagnostics + all 6 figures) measured
  at 25.9s wall-clock, single-threaded, over the 2010-2015 window (~6 years
  / 1512 test days, 3-asset universe) on this machine. Linearly
  extrapolating by test-day count to the final 2016-2025 window (~10 years
  / 2520 test days) gives ~43s. Even under a generous 50x safety margin
  for a larger final ETF universe and/or additional models, the estimate
  stays at roughly 36 minutes — well under the 2-hour bound. Basis is a
  single non-simulated backtest run, not a Monte Carlo replication (WP2's
  per-replication cost is not the relevant analogue for this criterion).

## Decision

All six criteria (G1-G6) PASS. Per the decision rules above: **PROCEED**
with the full design (Option B). G3 and G4 both pass only marginally
(G3 fails to clear 50% under the secondary calibrated DGP; G4 clears the
90% bar by 0.3 percentage points) — these are reported as-is per "if you
think one is badly chosen, say so in the report, but judge against the
original," not adjusted after seeing results. See `output/PILOT_REPORT.md`
for the full discussion and honest minimum-detectable-effect statement.
