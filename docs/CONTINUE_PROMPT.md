# Prompt: continue the thesis work from where the last session stopped

Paste everything below the line into a fresh Claude Code session at the repo root.

---

You are continuing work on my honours thesis ("Regime-Switching Risk Models for ETF Portfolios") in this repo. Read, in
this order, before doing anything: `output/THESIS_PROGRESS_RECAP.md` (state before the last session),
`docs/decisions_log.md` (the last ~6 entries are the pre-declarations made in the last session),
`thesis/01_design_and_methods.md`, `output/explore/ladder/` (results), `git status`.

## Hard rules
- **2020-2025 is a one-shot confirmatory hold-out. Do not run `scripts/confirm_00_run.py holdout`, and do not load or
  compute anything on data after 2019-12-31, until I explicitly say so in this session.** The runner refuses without the
  git tag `spec-freeze-v1`; do not create that tag until the preregistration file is written and I have approved it.
- Pre-declare before scoring: any new test family goes into `docs/decisions_log.md` BEFORE its results are looked at.
- Report weak or null results plainly; numbers come from result files; no invented citations; mark unverified as [UNVERIFIED].
- Do not commit unless I ask. If I ask, add no Claude co-author or footer lines (my memory note for this repo).

## Reframed thesis (agreed)
A controlled ablation of WHERE regime information helps one-day VaR/ES forecasts, with detectability reported for every
step. Ladder: A (pooled) -> B (regime vols) -> D (regime vols+corr) -> CCC (GARCH margins, constant corr) -> RSC (GARCH
margins, regime corr) -> DCC -> GARCH-t. Allocation is out of scope. Primary spec choice may change if well warranted.

## What is done (data through 2019-12-31 only; all validated, 62 tests pass)
- `src/explore_ladder.py` (static arms with pooled/zero/regime mean, Gaussian and Student-t), `src/explore_inference.py`
  (Giacomini-White), `src/dgp_garch.py` (GARCH-margin DGP), `run_rs_corr(..., zero_mean=)` in `src/explore_routes.py`.
- Scripts `explore_13..19`: ladder runs (4 ETF universes + 1992-2019 fund sample), scoring, SPA/MCS, conditional test,
  GARCH-DGP power study, forest figure `output/figures/ladder_forest.png`.
- Confirmatory runner `scripts/confirm_00_run.py`; the dry run on 2016-2019 passed (`output/confirm/pseudo_forecasts.pkl`).
  It matches the exploration forecasts closely (median |diff| ~1e-5; larger gaps come from HMM warm-start path and refit
  anchoring, not a bug).
- Methods chapter draft: `thesis/01_design_and_methods.md`.

## Results so far (see output/explore/ladder/*.csv)
- Matched-mean control: the GARCH-margin effect (RSC vs D, 5%) is unchanged (U1 -0.0259 pooled vs -0.0263 regime-mean).
  Per universe: U1 -0.026, U3 -0.041, U8 -0.040, U10 -0.076; Holm p 0.23/0.23/0.22/0.0025. Pre-declared gate (Holm-
  significant in >=2) NOT met -> reported as suggestive. Replication on funds 1992-2019: -0.031, p=0.12 (same sign/size).
- Ladder: regime volatility large and significant in 3/4 universes; correlation switching on GARCH margins -0.004 to
  -0.0055, about half the minimum detectable difference (~0.007-0.013); DCC ~ RSC; static models are too conservative
  (hit 3-4% at 5%), GARCH-margin arms ~5%.
- SPA: no regime model beats GARCH-t or DCC-t on any sample (p 0.13-0.96). MCS drops static models in U3, U10, funds.
- Conditional (secondary, unadjusted): regime corr helps when lagged stock-bond corr is positive (GW p=0.047, funds).
- Data check: two Yahoo downloads agree to <=2.5e-6 (same vendor; no second vendor yet).

## What was running when stopped: the GARCH-DGP power study (INCOMPLETE)
`scripts/explore_16_power_garch.py`: 4 scenarios (S0 null, S1 moderate, S2 strong, S3 flight-to-quality) x 200 reps, ~32 s per
rep per core, results in `output/explore/ladder/power/<scenario>.jsonl`. Done: S0 200/200, S1 20/200, S2 0, S3 0 (220/800).
Resumable: it skips finished replications and seeds are deterministic. Do NOT change `src/dgp_garch.py`, its parameters,
the PAIRS in the script or `config/pilot.yaml` before finishing, or delete the power folder and restart.
Resume (about 1 hour on 10 cores):
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/explore_16_power_garch.py 200`
Run it in the background and wait for completion; do not poll. If you stop it, also `pkill -f popen_loky_posix`.

## Next steps, in order
1. Finish the power study. Write a scoring script (rejection rate at one-sided 5%, binomial 95% CI, wrong-sign rate, mean
   FZ0 difference +/- Monte Carlo SE, per scenario and step; size from S0). Primary power question (pre-declared):
   RSC vs CCC. Also `pair_with_margins` (RSC_P vs CCC) decides whether the single SPY-IEF pair is the better confirmatory test.
2. Choose the single confirmatory test from that simulated power, and write `docs/preregistration_confirmatory.md`:
   universe SPY/IEF/GLD equal-weight, SPY 2-state HMM, 1260/21/63, forecasts 2020-01-01..2025-12-31, the ONE primary test,
   secondary tests (ladder steps, GW conditional with lagged 63-day SPY-IEF corr, SPA vs GARCH-t, 2022 episode,
   minimum detectable difference next to every result), and the note that the dry-run path differs slightly from the
   exploration path. Write `scripts/confirm_01_score.py` (referenced by the runner's freeze check) and dry-run it on
   `output/confirm/pseudo_forecasts.pkl`.
3. Show me the preregistration. Only after I approve: commit (if I ask), tag `spec-freeze-v1`, and STOP to ask me before
   running the holdout.
4. After the hold-out (only with my go-ahead): run once, score with the frozen script, label any post-hoc analysis as such.
5. Write throughout: results chapter for the ladder/power, literature positioning (Ardia et al. gains larger for simple
   baselines; Pelletier 2006; Santos 2013; Fortin 2023, findings [UNVERIFIED]), limitations (equity-only regime signal,
   no whole-pipeline HMM bootstrap, same-vendor data, benchmarks keep their own means), fill the empty `notes/` templates.

## Known open items
Second data vendor (Tiingo/CRSP) not done; whole-pipeline HMM bootstrap not built (null-scenario size stands in);
Prof. Seo's reply to the supervisor brief is not recorded in `notes/`; README stage text and the stale "open decisions"
list need updating after the supervisor meeting; nothing has been committed since 2026-10-13.

Start by summarising the state in 10 lines, confirm the power-study counts from the .jsonl files, then resume step 1.
