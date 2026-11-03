# Prompt: execute the thesis plan through to a submission-ready thesis

Paste everything below the line into a fresh Claude Code session at the repo root.

---

You are completing my honours thesis ("Regime-Switching Risk Models for ETF Portfolios", BSc Data Science and Economics, NUS, supervisor Prof. Seo) in this repo. `docs/THESIS_PLAN.md` is the agreed plan. Execute it phase by phase, without stopping except at the one gate in Phase 5, until a submission-ready thesis exists.

**HOLD-OUT GO-AHEAD: NOT YET GIVEN**
(Stop at the Phase 5 gate. Replace this line with `GIVEN` only to run the hold-out without stopping once its checklist passes.)

## 1. Decisions already made

Do not ask me about these again.

| Item | Decision |
|---|---|
| Primary test | RSC_P_N vs CCC_S_N, alpha = 5% tail level, one-sided 5% test: reject H0 if t < -1.6449. Do not reopen, whatever the 1,508-day simulation shows. |
| "Significantly worse" | t > +1.96, labelled as separate from H0/H1. Two-sided 95% CI and both p-values always reported. |
| Smallest effect of interest | Declare 0.002 FZ0 as a one-sided bound (outcome O3), derived by script, and state in advance that O3 is unlikely to be reached. Never claim equivalence. |
| Power at hold-out length | Run it: 1,508 test days, 500 replications x 4 scenarios. |
| Frozen specification | Go ahead and write and freeze it, then prepare it for Prof. Seo with a 3-working-day window (Phase 5). |
| MDE | 2.8016 x SE in all tables; add 2.4865 x SE for the primary. Label every table's sidedness. |
| Portfolio | Keep the code. Correct the text to "constant weights, rebalanced daily". |
| Secondary analyses | The plan's section 4.9 list, including SPA vs GARCH-t. Nothing else is scored. No Model Confidence Set on the hold-out. |
| Writing order | Chapters 3-6 are written and committed before the hold-out is opened. |
| OSF deposit | Skip. Disclose the preregistration as self-registered (git tag). |
| Title | Plan option 1: "Regime-Switching Risk Models for ETF Portfolios: Do Market-State Shifts Improve Tail-Risk Forecasting?" |
| Course, format, deadline | Do not block on these. Follow section 7's conventions. Spend at most 15 minutes looking for official NUS requirements; log what you find. If an official rule turns up, it overrides section 7. |
| Scope | No new models, universes, regime signals or robustness checks. New ideas go in the future-work section. |

## 2. Hard rules

**Hold-out discipline (until the Phase 5 gate clears):**
- Do not run `scripts/confirm_00_run.py holdout`.
- Do not load, compute on or display returns after 2019-12-31. Counting dates and hashing files is allowed.
- Do not open or print: `data/processed/*`, `data/raw/pilot_etf_yahoo_2010_2025.csv`, `notes/pilot_eda.md`, `notebooks/01_pilot_data_and_eda.ipynb`, `outputs/`, or lines 100-165 of `tests/test_returns.py`. That test file hard-codes hold-out returns; a broad `grep` already printed them once by accident, so use `grep -l` or narrow patterns on it. Read `data/raw/spy_ief_gld_raw_2026-09-26.csv` only through code that truncates at 2019-12-31 before computing, or with dates only.
- Never run the three pilot-data tests in `tests/test_returns.py` before the gate clears.

**Evidence:**
- Every number in the thesis must trace to a result file. Numbers marked *computed today* in the plan are not yet evidence: re-create them with repo scripts first.
- Report weak and null results plainly. Never fabricate or round in a flattering direction.
- Pre-declare before scoring: anything new that will be tested goes in `docs/decisions_log.md` before its result is seen.
- No invented citations (section 6). Mark anything unchecked `[UNVERIFIED]`, and remove every such mark before the final build, either by verifying the source or by cutting the claim.
- The plan may contain mistakes. Verify it against code and results. Where it is wrong, follow the evidence and log the correction in `docs/EXECUTION_LOG.md`.

**Authorship and external actions:**
- Do not write in my voice as if it were my own learning record. Leave `notes/thesis_notebook.md` empty for me; put explanatory material in `notes/viva_prep.md` (Phase 11).
- Do not email anyone, post anything or submit anything. Write outgoing messages to `notes/outbox/` for me to send.
- Commits: you may commit at the points named below, on the current branch, staging named files only. Do not push. No Claude co-author or footer lines in any commit (standing instruction for this repo).

## 3. CPU and heat limit: never more than 5 of the 10 cores

This applies to every command in every phase.

**Start every compute command with:**
```
export LOKY_MAX_CPU_COUNT=5 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
```

- **New parallel scripts** take a required worker count and pass it as `Parallel(n_jobs=N)`, with `N <= 5` enforced by an assertion. Never use `n_jobs=-1`.
- **Existing scripts that default to all cores:** `explore_16_power_garch.py`, `explore_10_power_routes.py`, `wp2_run_simulation.py`, `wp4_reproducibility_check.py`, and `src/wp2_simulation.py`. Do not run them unless necessary; if you must, pass `n_jobs=5` where the script allows it and keep the exports above.
- **One heavy job at a time.** Never start a second compute job while one is running. Do not run tests, builds or subagent compute alongside it.
- **Subagents** are read-only reviewers. Run them one at a time, and never while a simulation is running.
- **Long jobs:** run with `nice -n 10` in the background and wait for the completion notice. Do not poll in a tight loop.
- **Verify the limit.** Within the first minute of any parallel job, count the workers with `ps -axo pid,pcpu,comm,args | grep -E "loky|explore_21" | grep -v grep`, and record the count in the log. If more than 5 are busy, stop the job (`pkill -f popen_loky_posix`), fix the cause and restart.
- **Heat.** Check `pmset -g therm` when a long job starts and about every 30 minutes during it. If `CPU_Speed_Limit` falls below 100, stop the job, wait 15 minutes and resume at 4 workers. Jobs must be resumable: write each replication as it finishes and skip finished ones on restart.
- **Be efficient.** Time a small sample first and estimate the total before any job over 10 minutes. Do not recompute results that exist unless a check requires it.

## 4. Working method

Read, in this order, before acting: `docs/THESIS_PLAN.md` (all of it), `docs/decisions_log.md`, `thesis/01_design_and_methods.md`, `output/SUPERVISOR_DRAFT_2026-10-27.md`, `scripts/confirm_00_run.py`, `src/explore_routes.py`, `src/explore_ladder.py`, `src/explore_wf.py`, `src/engine.py`, `scripts/explore_14_score_ladder.py`, `scripts/explore_16_power_garch.py`, `scripts/explore_17_spa_mcs.py`, `scripts/explore_18_gw_conditional.py`, `scripts/explore_20_score_power.py`, `output/explore/ladder/*.csv`, `output/explore/routes/routes_dm_table.csv`, `output/explore/EXPLORATION_SUMMARY.md`, `docs/literature_briefing.md`.

Keep `docs/EXECUTION_LOG.md` as your state file. After each phase record: status, files changed, commands run with their duration and worker count, checks passed, corrections to the plan, and the next step. **If this file already exists, read it first and resume from the recorded step; never redo or rerun a completed one-shot step.**

Each phase ends with a gate. Do not start the next phase until its gate passes. If a check fails, fix the cause, not the check. If something truly blocks progress, record it and continue with whatever is independent of it. Stop only at the Phase 5 gate or if a hard rule would otherwise be broken.

Give me one short status line per phase.

## 5. Phases

### Phase 0: Setup
1. Read the files in section 4. Summarise the state in about 10 lines.
2. Run the tests excluding the three pilot-data tests:
   `.venv/bin/python -m pytest tests -q -p no:cacheprovider -k "not on_pilot_data"`. Expect 59 passed.
3. Set up the thesis toolchain. This machine has no `pandoc` or LaTeX. Install `tectonic` and `pandoc` with Homebrew. Do **not** install or upgrade anything in `.venv`: its numerical packages are pinned and must stay as they are through the freeze. If Homebrew fails, log it and use the best available route to a clean PDF with properly typeset equations.

**Gate:** tests pass, the toolchain can build a one-page test PDF with an equation and a citation.

### Phase 1: Corrections and housekeeping (plan phase 1, 2.E, 3.8)
1. Copy the two as-sent PDFs from `~/Downloads/ilovepdf_converted/` to `docs/sent/` and record their hashes.
2. Correct `thesis/01_design_and_methods.md` using the plan's replacement table (2.A.3) and errors E1-E15, and regenerate its PDF. Correct `output/SUPERVISOR_DRAFT_2026-10-27.md` the same way into a new dated file; do not overwrite the original.
3. Write `notes/outbox/01_correction_note.md` from the draft in plan 2.E, checking each claim against the files.
4. Record her feedback verbatim in `notes/supervisor_feedback_2026-11.md`.
5. Update `README.md` (title, stage, rebalancing wording, stale decisions list). Update `notes/decision_log.md` and `notes/supervisor_questions.md`.
6. Add the decisions-log entries the plan lists in 5.1, including the correction of the "1992-2009" label. Keep earlier entries unchanged; add corrections as new entries.
7. Write `scripts/check_wording.py` from the banned list in plan 2.B.1 and run it on the corrected documents.

**Gate:** wording check is clean on corrected documents. Commit.

### Phase 2: Requirements and conventions (plan 5.2)
Time-box the official search to 15 minutes. Write `notes/requirements.md`: what was found with links, what was not, and the defaults in section 7 being used. Check for an NUS or course policy on generative-AI use in theses and record what it says. Write `notes/outbox/02_requirements_questions.md` with the plan's six questions for the programme office.

**Gate:** file exists. Do not wait for replies.

### Phase 3: Pre-freeze technical work (plan phase 3, 3.3, 3.6, 3.10, section 4)

**Step 1: Declare, then simulate power.** First add the decisions-log entry: 1,508 test days, 500 replications per scenario, seeds, one-sided and two-sided reporting, the low-power rule, and "the test does not change".
Then write `scripts/explore_21_power_holdout_length.py` as a new file. Do not change `explore_16_power_garch.py`, `config/pilot.yaml`, `src/dgp_garch.py` or the existing power folder. It uses `test_days = 1508`, a seed offset distinct from the earlier study (`+3_000_000`), a required `--workers` argument with `assert workers <= 5`, resumable JSONL output in `output/explore/ladder/power_1508/`, and a `--time` mode. Run `--time`, estimate the total, then run in the background with 5 workers under the section 3 rules. My rough estimate is 2 to 3 hours; use your measured time.
Write the matching summary script producing `output/explore/ladder/power_1508_summary.csv`: one-sided and two-sided rejection rates, upper-tail rates, binomial CIs, mean difference with Monte Carlo SE, and the standard error of the loss difference. Also add two-sided columns for the 2,520-day study to a new file, leaving `power_summary.csv` unchanged.

**Step 2: Code changes needed before the freeze.** Forecasts must remain numerically identical.
- `run_rs_corr`: count PSD repairs per refit and state; count margin-fit fallbacks instead of swallowing them; save per-refit SPY-IEF correlations and GARCH parameters, and daily mixture parameters for the two primary arms.
- `fit_dcc`: count the fallback to `a = b = 0`.
- `confirm_00_run.py`: fix the `freeze_tag` value; save the 64 returns before the first forecast day (for the lagged correlation); save `pip freeze` output and raw-file SHA-256; assert the expected forecast-day count (1,508 in holdout mode); assert finite values and `ES <= VaR < 0` for primary arms before writing output.
- `tests/test_returns.py`: mark the three data tests `holdout_data` (register the marker) and exclude them by default. Do not read their values while doing this.
- Correct the misleading docstring in `src/returns.py`.
- Add tests on synthetic data for every change.
- Check: keep a renamed copy of `output/confirm/pseudo_forecasts.pkl`, re-run `pseudo`, and confirm V and E are bit-identical to the copy for every arm. If they differ, stop and find out why.

**Step 3: Scripts that turn the plan's "computed today" items into evidence** (each writes a result file under `output/confirm/`):
- `confirm_02_pair_repair_audit.py`: repairs, eigenvalues and regime correlations through 2019.
- `confirm_03_vendor_check.py`: the two downloads through 2019.
- `confirm_04_sesoi.py`: analytic FZ0 penalty of proportional VaR/ES scale errors, no market data. The declared value is the 3% penalty, to one significant figure. If this does not give 0.002, use what it gives and log the difference.
- Dry-run comparison against the exploration path (plan 4.11).
Compare each output with the plan's figures and log any differences.

**Step 4: `scripts/confirm_01_score.py`**, taking `pseudo` or `holdout`, with the same code path for both. It validates the run first (plan 4.10), then computes:
- The primary result: mean difference, HAC SE (lag rule from `engine.dm_test`, 7 lags at T = 1,508), t, one-sided p, two-sided p, 95% CI, one-sided 95% bound, both MDEs, the SESOI comparison, the outcome label O1-O4 and the matching frozen sentence from plan 4.8 with numbers filled in.
- Calibration: hit rates, Kupiec, Christoffersen independence, conditional coverage, and Acerbi-Székely Z2 with a simulation p-value from each model's predictive distribution (5,000 draws, fixed seed). Verify the Z2 sign convention and state it.
- Every secondary analysis in plan 4.9, and a descriptive plot of cumulative `d_t` with 2022 marked.
- Repair and fallback counts. Tables and figures are written automatically to `output/confirm/<mode>/`, with no manual steps.
It scores only declared arms: not the Kendall arms, HS or EWMA.
Add `tests/test_confirm_score.py` with synthetic data and known answers, including each of the four outcomes and the one-sided sign.

**Step 5: Dry run.** Run the scorer on `pseudo`. Rows that overlap existing exploration results must agree within the known path difference; explain any that do not. The dry-run result is a pipeline check and goes in no argument for the hypothesis.

**Gate:** all tests pass, the worker count was verified at or below 5 for each parallel job, and the dry-run tables generate from a single command. Commit code and summaries.

### Phase 4: Write the pre-hold-out chapters (plan phase 8, 2.A, 2.C, section 6)
Write chapters 3 (data), 4 (methodology), 5 (evaluation and inference) and 6 (exploration and ladder results) to the standard in section 7, plus the literature chapter as far as Phase 6 has reached. These two tracks may interleave.
- Regenerate the forest figure with step labels that do not imply nesting and with both control variants available for the appendix.
- Use plan 2.A.1's table in chapter 4 after re-verifying each cell against the code.
- Chapter 6 follows the storyline (plan 2.C.1) and exhibit map (2.C.2), and includes the D-vs-B size finding (2.C.4), the missed pre-declared bar, and the real-data RSC_P vs CCC row from `routes_dm_table.csv`, which was never in the update.
- Add a placeholder for chapter 7's results; do not write its interpretation.

**Gate:** wording check clean on all chapters. Commit, and create the tag `prewrite-v1` so the commit history shows this framing predates the hold-out.

### Phase 5: Freeze, gate, hold-out (plan phases 4-5, section 4, 5.5)
1. Write `docs/preregistration_confirmatory.md` from plan section 4, with the decisions in section 1 applied, every **DECIDE** resolved, the real power results, and the full disclosure list including the accidental display.
2. Log the secondary list and specification in `docs/decisions_log.md`.
3. Commit, then create the annotated tag `spec-freeze-v1`. Verify `check_freeze()` passes without running the hold-out.
4. Write `notes/outbox/03_frozen_spec_note.md` for Prof. Seo: short, with the hypothesis, sidedness, exact SPY-IEF specification and expected power, and stating the run will proceed after 3 working days absent objections.
5. **GATE.** Unless the go-ahead line at the top says `GIVEN`, **stop here.** Tell me to send notes 01 and 03, and that I reply "go" when the window has passed. If she objects, any change means a new log entry and tag `spec-freeze-v1.1` before running.
6. On go: run the pre-run checklist (plan 5.5). Then, once:
   `.venv/bin/python scripts/confirm_00_run.py holdout`
   followed by `.venv/bin/python scripts/confirm_01_score.py holdout`.
   It is single-threaded and takes about a minute; the section 3 exports still apply.
7. Run the after-run checklist. Record the pickle's SHA-256. Only then run the `holdout_data` tests.
A crash before output is written follows plan 4.10 item 7. **Never re-run a completed hold-out, whatever the result.**

**Gate:** valid run confirmed, hashes logged, outcome label recorded. Commit tables and log. Do not commit the pickle if it is large; keep its hash.

### Phase 6: Literature (plan 6.2-6.4); runs alongside Phases 3-4
Work from themes in plan 6.3, building an argument, not a paper-by-paper list. Follow section 6 for verification, and record each source in `notes/literature_matrix.csv`.
Resolve first: what Ardia et al. (2018) actually conclude, since the repo's two descriptions conflict with the abstract; delete whichever claim is unsupported, in every document. Then the unsourced claims listed at the end of plan 6.2.

**Gate:** the citation audit table is complete and no chapter relies on an unread claim.

### Phase 7: Results, discussion, conclusion
1. Chapter 7: use the frozen wording for the outcome that occurred, with no softening or strengthening. Report power prominently. Secondary results follow, labelled. Anything not preregistered is marked **POST HOC** and carries no inferential weight.
2. Chapter 8: what each result does and does not show; limitations (plan 3 and 4.11); why a volatility-regime signal and a rolling 1,260-day window may be slow to reflect a change such as 2022, stated as a design limit and not as a rescue of the result; future work.
3. Chapters 9 and 1, then the abstract, last. Chapters 3-6 may be corrected for errors only, not reframed in light of the hold-out; log any such edit against `prewrite-v1`.

**Gate:** full first draft builds to PDF.

### Phase 8: Reproducibility package (plan phase 9)
Create `scripts/build_all.py`, rebuilding every thesis table and figure from saved result files with `n_jobs <= 5`, and document the full-recompute route and its run time in an appendix. Copy the repo to a temporary clean clone (result files and raw data included), run the build there, and compare outputs. List package versions from `requirements.txt` and machine details.

**Gate:** clean-clone rebuild matches.

### Phase 9: Verification
Run all of these and fix what they find. Repeat until clean.
1. **Number trace.** Create `thesis/numbers.yaml` mapping every number in the thesis to file, row and column, plus `scripts/check_numbers.py`, which recomputes each and fails on a mismatch. Numbers in the prose must be generated or checked by this script.
2. **Citation check.** Every in-text citation is in the bibliography and vice versa; every entry has a verified status.
3. **Wording sweep** with `check_wording.py`, plus a manual read for meaning, since phrases can overstate without being banned.
4. **Consistency.** Same model names, notation, sign convention ("richer minus baseline; negative means better"), sample sizes and sidedness labels everywhere. All cross-references resolve; every figure and table is cited in text.
5. **Code-vs-text.** Re-derive each methods statement from the code: formulas, window, refit schedule, mixture weights, smoothed vs filtered, mean, df estimation.
6. **Discipline audit.** Commit dates show tag, then run, then chapter 7. Every test in the thesis is pre-declared or marked. All disclosures are present.
7. **Render check.** Convert each PDF page to an image and inspect it for broken equations, overflowing tables, bad figures and missing fonts.

**Gate:** all pass. Run the full test suite, now including the `holdout_data` tests.

### Phase 10: Independent review
Run these as separate read-only subagents, one after another, each starting cold with the thesis PDF and repo:
1. **Hostile econometrics examiner:** inference validity, nesting claims, power, preregistration, anything a viva would attack.
2. **Literature reviewer:** does each citation say what the text claims, and is the argument well positioned?
3. **Clarity reader:** a smart economics student unfamiliar with the project. Can each element be followed; are terms defined; is the storyline coherent?
4. **Error hunter:** arithmetic, tables vs text, figure vs table, typos, formatting.
Verify each finding yourself before acting; reviewers can be wrong. Fix what stands, log what you reject and why, then re-run Phase 9. Do at most three rounds. Anything still open goes in the final report as a known issue.

**Gate:** no open high-severity finding.

### Phase 11: Submission package
1. Final PDF in `thesis/final/`, an editable export, and `notes/submission_checklist.md`.
2. `notes/viva_prep.md`: plain-language explanations of each method and model, the 20 hardest likely questions with honest answers and where the evidence lives, so I can understand and defend all of it.
3. A draft AI-assistance statement in the front matter or `notes/`, consistent with whatever Phase 2 found, describing truthfully how AI was used. I decide its final wording.
4. `notes/outbox/04_full_draft_note.md`: a short note for sending the full draft to Prof. Seo.
5. Final commit and tag `thesis-submission-candidate`. Do not push or submit.

**Final report to me:** one page with the result in plain language, the outcome label, known issues, every assumption made in place of an official rule, and a list of what only I can do: send the outbox notes, confirm official format and deadline, confirm the title change, finalise the AI statement, read the thesis, submit.

When Prof. Seo's comments arrive, I will paste them into a new session with this prompt; treat them like feedback in plan section 2, without touching the frozen specification or re-running the hold-out.

## 6. Literature and citation standard

- For each source record its level of verification: **registry** (Crossref or publisher record checked), **abstract**, or **full text**.
- Cite a specific finding only if you read it at that level in this work. Use open-access versions where they exist: publisher, author page, repository, NBER, SSRN, arXiv. Do not rely on search summaries or secondary descriptions for what a paper found.
- Paywalled, full text not reachable: either state only what the abstract supports, or list it in `notes/outbox/05_library_requests.md` for me to fetch from the NUS library, and keep the claim out until it is read. Do not write around the gap.
- The plan lists journal details "from memory" for several works. Confirm each against a registry or publisher page.
- Methods claims that matter most need full text or a strong primary source: what Giacomini-White (2006) establish about rolling windows and nested models; Clark-McCracken (2001) and Clark-West (2007); McCracken (2020); the FZ0 definition in Patton, Ziegel and Chen (2019); the Z2 definition and critical values in Acerbi-Székely (2014).
- Keep the novelty claim modest: "I did not find" rather than "no study has".

## 7. Thesis standard

Use these unless an official rule overrides them (log which applied).

**Format:** LaTeX source in `thesis/tex/`, one file per chapter. A4, 12pt, 1.5 line spacing, 2.5 cm margins. Author-date citations in AER/Chicago style with a BibTeX bibliography. Target about 12,000 words excluding front matter, references and appendices, as a planning figure; do not pad or cut substance to hit it. Front matter: title page, abstract (up to 250 words, stating question, method, the numerical result and its uncertainty), acknowledgements placeholder, contents, list of tables and figures, list of abbreviations and notation.

**Chapters:** the outline and shares in plan 6.1.

**Econometric reporting:**
- State every model with equations and consistent notation, including exactly what is estimated, when, and on what window. A reader must be able to reimplement the study from the text.
- Separate clearly: estimand, estimator, test, decision rule, interpretation. Separate the tail level from the test level everywhere.
- Every comparison table: estimate, SE, 95% CI, n, labelled p-value, MDE, sign convention in the note. Report in consistent decimals, without significance stars as a substitute for intervals.
- Distinguish preregistered, secondary and post hoc results visibly.
- Distinguish statistical from economic significance: translate FZ0 differences using the scale-error derivation.
- Figures: readable in greyscale, labelled axes with units, a caption saying what it shows and its source file, no chart junk.
- Explain each concept at first use for a reader who knows econometrics but not this project. Every table and figure gets a sentence on what it shows and why it matters.
- Prose: direct, active, precise; no filler or hype; claims no stronger than the evidence; plain statement of limits.

**Acceptance test for every claim:** does it say what the comparison actually isolates (plan 2.A.2), is it distinguished from evidence of no effect (plan 2.B), and does it trace to a file?

## 8. If things go differently from the plan

- **Power lower than projected:** follow the pre-declared rule. Run the test and report power prominently.
- **Size failure in the 1,508-day S0 row** (one-sided rate with a CI wholly above 5%): keep the primary as declared and report the size prominently alongside a simulated critical value as a labelled sensitivity.
- **Bug found before the freeze:** fix, test, re-run what it affects, log it.
- **Bug found after the hold-out:** report the frozen result and the corrected result side by side, with the bug explained. The frozen one stays the primary record.
- **An earlier result turns out wrong:** correct it, log it, and add it to the note for Prof. Seo if she has seen it.
- **Any result you dislike, including an inconclusive hold-out:** report it as it is. The thesis is designed for this outcome.

Begin with Phase 0.
