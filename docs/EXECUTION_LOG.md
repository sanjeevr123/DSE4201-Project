# Execution log

State file for `docs/THESIS_EXECUTION_PROMPT.md`. If this file exists, resume from "Next step" and never rerun a completed one-shot step.

**Next step:** Phase 3 step 2 (code changes before the freeze). Phase 2 and Phase 6 web work is on hold (web searches were rejected earlier; ask before retrying).

## Hold-out status
Not run. `HOLD-OUT GO-AHEAD: NOT YET GIVEN`. Tags: none yet.

## Standing constraints added by the user
- 2026-11-03: use only established, trusted packages and install methods, verified before use. If the instructed route is unavailable, ask.
- 2026-11-03: thermal policy from the user replaces section 3's, implemented in `scripts/thermal_watch.sh` (tests: `tests/test_thermal_watch.py`, 5 passed), pausing by PID and logging to `power_1508/thermal.log`. Pause at once: thermal state 2 or 3. Pause if sustained: speed limit < 90 for 2 min, 90-99 for 5 min, non-zero warning for 2 min, GPU >= 90% for 10 min together with heat or throttling. Logged only: state 1; GPU use alone. Resume when state 0, limit 100 and no warning hold for 5 min; no fixed wait. Sampled each minute. State 3 pauses rather than ends the job: load drops to zero and the job stays resumable. Die and ambient temperature are not read (no unprivileged reading). The watcher's test ran during the power job; it is `sleep` and shell calls only.
- 2026-11-03: user asked to focus on the power job first; Phase 2 and Phase 6 web work is on hold, not skipped. Web searches were rejected at the time.

## Corrections to the plan
| Plan ref | Plan says | Evidence | Action |
|---|---|---|---|
| 3.8 | `.gitignore` ignores `output/confirm/pseudo_forecasts.pkl` | `git ls-files` lists it as tracked; `git check-ignore` returns nothing | The dry-run pickle has git history. Keep the tracked copy until the Phase 3 bit-identity check is done. Decide on the hold-out pickle by size at the time. |
| 2.E | Correction email has 5 items | E4 and E11 also bear on how results are read | Note has 7 items, including mean treatment and the D-vs-B size. |
| 2.A.3 | "Margin and volatility steps 91-100%" not listed as an error | `power_summary.csv`: maximum is 99.5% | Corrected draft shows per-scenario ranges with 99.5%. |

## Parallel jobs
| Job | Started | Workers verified | Thermal | Status |
|---|---|---|---|---|
| `explore_21_power_holdout_length.py --workers 5`, `nice -n 10`, `--time`: 19 s per rep, estimate 2.1 h | 2026-11-03, about 21:10 SGT | 5 busy at 98% CPU (`ps` at 21:13); parent and tracker at 0% | `pmset -g therm`: no warning recorded | **Restarted at about 22:00 with 4 workers at the user's request** (5-worker run stopped with 275 reps saved; resumed from them; `LOKY_MAX_CPU_COUNT=4`). 4 workers busy at 98% CPU each (`ps` after 20 s; PIDs 38170-38173), thermal watcher re-attached to parent PID 38162. **22:38: paused at the user's request until told to continue** (SIGSTOP on PID 38162 and children 38168-38173; 709 reps saved: S0 500, S1 209; watcher killed with SIGKILL so it cannot resume the job). Resumed at the user's request later the same evening (SIGCONT, watcher restarted on PID 38162); see `power_1508/thermal.log` for times. Earlier history of the 5-worker run: paused 21:32-21:42 at the user's request (felt hot; thermal state was 0 throughout), resumed automatically after 5 stable-state checks. At 21:56: 265 of 2,000 reps, about 7.4 reps/min with 5 workers (half the rate implied by `--time`), so about 4 h more, finishing around 02:00 |

## Phase 0: Setup. Status: DONE (gate passed 2026-11-03)
- **State.** Exploration through 2019 is complete. Ladder, routes, power (2,520 days) and SPA/GW results exist. Methods and update drafts contain errors E1-E15, verified in the as-sent PDFs for the phrases searched. Missing: preregistration, `confirm_01_score.py`, 1,508-day power, chapters, literature audit. No `EXECUTION_LOG.md` existed; fresh start. Branch `pilot-study`.
- **Tests.** `.venv/bin/python -m pytest tests -q -p no:cacheprovider -k "not on_pilot_data"`: 59 passed, 3 deselected, 15.6 s, single process.
- **Toolchain.** Homebrew was absent. A first attempt to fetch release binaries directly was rejected by the user; nothing was installed by it. The user chose Homebrew and ran the official installer. `brew install --formula tectonic pandoc` (homebrew/core, poured from bottles): tectonic 0.17.0_1, pandoc 3.13, 29 s. `.venv` untouched.
- **Gate check.** One-page test PDF with equation and natbib/`aer` citation built with tectonic (first run 3 min 22 s, downloading tectonic's package bundle to its cache).
- **Machine.** Apple M5, 10 cores, arm64, macOS 26.6.2.

## Phase 1: Corrections and housekeeping. Status: DONE (gate passed 2026-11-03)
- **As-sent PDFs** copied to `docs/sent/`:
  - `01_design_and_methods_as_sent.pdf` SHA-256 `1689e6f5e8b56e5a51cdab8d7955d1e6958d608a028144b825e2677b8f6e6533`
  - `Thesis_Update1_as_sent.pdf` SHA-256 `467a81edf834da0c4ad9790663b2c2c1833eb41cd56e0887090fda87c9826f04`
- **Superseded local versions** kept before regenerating: `docs/sent/superseded/01_design_and_methods_handedited_2026-10-27.docx` (SHA-256 `6eaace07...cb36f9`), `01_design_and_methods_repo_2026-10-27.pdf` (`4575d2b1...63553`).
- **Files changed.** `thesis/01_design_and_methods.{md,pdf,docx}`; new `output/SUPERVISOR_DRAFT_2026-11-03.{md,pdf}` (original untouched); `notes/outbox/01_correction_note.md`; `notes/supervisor_feedback_2026-11.md`; `README.md`; `notes/decision_log.md`; `notes/supervisor_questions.md`; `docs/decisions_log.md`; `scripts/check_wording.py`; `tests/test_check_wording.py`; `scripts/thesis_fig_forest.py` and `output/figures/forest_comparisons_{pooled,zero,regime}.png`.
- **Figure.** Regenerated early (Phase 4 task) because the old forest plot's title used "rung" and printed p=0.00, and the corrected draft is an attachment to the note. Greyscale; labels state what each comparison changes.
- **Ardia et al.** The unsourced sentence is removed from the corrected draft pending Phase 6.
- **Gate check.** `scripts/check_wording.py` clean on corrected methods, corrected update, correction note (one paragraph carries `wording-ok` because it quotes the errors) and README. The original draft gives 14 hits, showing the check catches them. Tests: 63 passed, 3 deselected.

## Phase 3 step 1: power at 1,508 days. Status: DONE (2026-11-04)
- **Declared** in `docs/decisions_log.md` before the run (1,508 days, 500 reps x 4 scenarios, seeds +3,000,000, one- and two-sided reporting, low-power rule, "test does not change").
- **Files.** `scripts/explore_21_power_holdout_length.py` (`--workers` required, `assert workers <= 5`, `--time`, resumable JSONL), `scripts/explore_22_power_summary.py`, `output/explore/ladder/power_1508/*.jsonl`, `power_1508_summary.csv`, `power_2520_twosided.csv` (new; `power_summary.csv` unchanged, same MD5 before and after). `src/dgp_garch.py`, `config/pilot.yaml`, `explore_16_power_garch.py` untouched.
- **Commands.** `--time`: 19 s per rep on one process. Main run 5 workers `nice -n 10`, then restarted with 4 workers at the user's request after 275 reps saved; 5 and 4 workers verified busy by `ps`. About 11 reps/min at 4 workers. Thermal state stayed 0 at every logged check apart from two brief state-1 readings (21:28, 22:28), which cleared. The run was paused several times at the user's request.
- **SHA-256 of the result files (first 16 hex):** S0 `62420a5ce4f46322`, S1 `c6b1f5d6d09e4f73`, S2 `a9918e8e26ab87b5`, S3 `064442a805d91862`.
- **Results** in `docs/decisions_log.md`. Primary RSC_P vs CCC one-sided: S0 3.6%, S1 18.2%, S2 35.2%, S3 2.4%; two-sided S2 24.2%. Projection in the plan (normal approximation) said about 20% and 38%; the simulation gives 18.2% and 35.2%. Differences from the plan: none that change a decision. New finding: simulated SE of the primary difference (0.0006 under S0) is under half the real-data SE (0.0013-0.0015).
- **Note on process.** I told the user a job would stop at 1,800 replications without checking the count first; it had already passed 1,800, so it paused at 1,898. No data issue.

## Phase 3 step 2: pre-freeze code changes. Status: DONE (2026-11-04)
- **Changes.** `src/explore_routes.py`: `needs_repair`, `pair_variant(..., repairs=None)`, `run_rs_corr` returns `diag` (per-refit PSD repair flags per state, margin parameters, SPY-IEF pooled/regime/RSC_P correlations, margin-fallback refit dates, daily mixture weights, SDs and mean of RSC_P_N and CCC_S_N). `src/explore_wf.py`: `fit_dcc` returns `fallback`, `run_benchmarks` returns `diag` with DCC refit and fallback counts. `scripts/confirm_00_run.py`: `freeze_tag_commit()` (`rev-parse --verify --quiet`, None without the tag), 64 prior returns and dates saved, `pip freeze`, Python version and raw-file SHA-256 saved, `validate_output` (expected 1,006 days in pseudo and 1,508 in holdout; finite, VaR < 0, ES <= VaR for RSC_P_N and CCC_S_N at both tail levels) run before the pickle is written. `src/returns.py` docstring corrected (constant weights, rebalanced daily, turnover ignored). `tests/test_returns.py`: the three `_on_pilot_data` tests marked `holdout_data` by inserting a decorator line only (contents not read). New `pytest.ini` registers the marker and sets `addopts = -m "not holdout_data"`.
- **Tests.** New `tests/test_prefreeze_changes.py` (18, synthetic data). Full suite: 86 passed, 3 deselected (`pytest tests -q`, 56 s). 59 before + 5 thermal watcher + 4 wording + 18 new = 86.
- **Bit-identity check (plan: stop if different).** `output/confirm/pseudo_forecasts.pkl` copied to `pseudo_forecasts_pre_hygiene.pkl` (SHA-256 `3c667fc83d45577a...`), original moved aside, `confirm_00_run.py pseudo` re-run (17 s, single process). Compared V and E for all 84 arm x quantity arrays in the S, L2 and B blocks: byte-identical, 0 differing. Returns, dates and stress probabilities also identical. New keys only: `prior_returns`, `prior_dates`, `pip_freeze`, `raw_sha256`, `python`, plus `diag`.
- **Facts from the pseudo run (these are results of the diagnostics, not forecasts).** PSD repair fired 0 of 96 RSC_P component matrices (48 refits x 2 states; the plan's 98 was for a chain anchored one refit earlier). Margin-fit fallbacks: none. DCC: 16 refits, 0 fallbacks to a = b = 0. Raw-file SHA-256 `0ab8c7f353a7223e...` matches `data/raw/MANIFEST.txt` and the plan. `freeze_tag` is `None` (no tag yet).
- **To redo.** The pseudo pickle must be re-run once more from the clean committed code at the freeze (plan D12; the pickle's `git_head` here is the commit before this change).
