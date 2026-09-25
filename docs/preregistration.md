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
- **G2-G6**: not yet evaluated — require WP2 (simulation power study), WP3
  (real-data pilot), and WP4 (reproducibility check), which have not been run
  yet as of this commit.
