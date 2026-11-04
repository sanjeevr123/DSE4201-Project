# Prompt: turn the supervisor's feedback into a complete plan for the rest of the thesis

Paste everything below the line into a fresh Claude Code session at the repo root.

---

You are helping me finish my honours thesis ("Regime-Switching Risk Models for ETF Portfolios") in this repo. My supervisor has reviewed my design and my progress update and approved the direction. Your job in this session is to **analyse her feedback in full and write a concrete, detailed plan for everything from now to submission**, covering data, code, models, evaluation, literature and writing.

This session produces a plan. It does not run the hold-out, write the thesis or change any code.

## Hard rules

- **2020-2025 is a one-shot confirmatory hold-out.** Do not run `scripts/confirm_00_run.py holdout`. Do not load, compute on or display returns after 2019-12-31. Do not create the git tag `spec-freeze-v1`. Checking file hashes and counting trading dates is allowed; looking at returns or any statistic built from them is not.
- Anything new that will be tested must be pre-declared in `docs/decisions_log.md` before its results are looked at. In this session, propose those entries in the plan rather than writing them.
- Every number must come from a result file, and you must name that file. Report weak and null results plainly.
- Do not invent citations. Check each one against a primary source, and mark anything you could not check as [UNVERIFIED].
- Do not commit unless I ask. If I do, add no Claude co-author or footer lines.
- Do not widen the scope. My supervisor said no additional macro-regime models or robustness checks are needed. Any new idea goes in a "future work" list unless the plan shows the thesis cannot be defended without it.

## Read first, in this order

1. `~/Downloads/ilovepdf_converted/Thesis_Update1.pdf`, the update as sent (source: `output/SUPERVISOR_DRAFT_2026-10-27.md`)
2. `thesis/01_design_and_methods.pdf`, the methods draft as sent (source: `thesis/01_design_and_methods.md`)
3. `docs/decisions_log.md`, especially the last ~6 entries
4. `docs/CONTINUE_PROMPT.md` and `output/THESIS_PROGRESS_RECAP.md`
5. `output/explore/ladder/*.csv` and `output/explore/EXPLORATION_SUMMARY.md`
6. `scripts/confirm_00_run.py`, `src/explore_routes.py`, `src/engine.py`, `src/returns.py`, `scripts/explore_14_score_ladder.py`, `scripts/explore_20_score_power.py`
7. `docs/literature_briefing.md`, `output/literature_positioning.md`, `notes/literature_matrix.csv`
8. `git status`, `README.md` and the `notes/` folder

## The supervisor's feedback (verbatim)

> I think you can proceed with your current approach without major changes. The overall direction looks good, and I can see that you have put considerable thought and effort into the project.
>
> The ladder-plus-detectability framework is appropriate, and a thesis centered on negative results is perfectly acceptable. I support proceeding with the 2020–2025 hold-out analysis. I do not think additional macro-regime models or robustness checks are necessary at this stage. And regarding your questions: You don't need CRSP at this stage (or: check if NUS library has it), and yes, you can narrow the title since you dropped the allocation extension.
>
> When writing the thesis, please be careful not to overstate what each model comparison isolates, as the models are not all strictly nested. Also, distinguish between a lack of statistically significant improvement and evidence of no improvement, especially given the limited power. Finally, focus on presenting a coherent story rather than including every exploratory result.
>
> The proposed confirmatory test looks appropriate. Please clearly specify the hypothesis, whether the test is one-sided or two-sided, and the exact SPY–IEF specification before running the hold-out analysis. Remember that a non-significant result does not imply the absence of an effect.
>
> For the thesis format and length, please check whether there are any official requirements. If not, I have no particular preferences.

## Part 1: Analyse the feedback

Build a table with one row per point she made, including the short ones. Columns: what she said; what it commits me to; what she did not say or leaves open; what must change in the repo or chapters; how we will know it is done.

Then work through each of these in depth.

**A. "The models are not all strictly nested."** For every ladder step, state from the code exactly what differs between the two arms: volatility, correlation, mean, distribution and refit schedule. Classify each step as strictly nested, nested only in the correlation matrix, or non-nested, and write the most that each comparison can honestly claim. Starting points to verify, not conclusions to copy:
- The GARCH margins in `fit_margins` (`src/explore_routes.py`) appear to have no regime dependence. If so, CCC vs B and RSC vs D replace regime-specific static volatility with a single-regime GARCH. They do not add dynamics "within a regime", which is how ingredient (ii) is described in section 1 of the methods draft.
- The methods draft calls this a nested ladder that "attributes the improvement to a single ingredient". The update repeats that language. List every sentence that overstates, with replacement wording.
- DCC vs RSC and GARCH-t vs the portfolio models are non-nested as well.
- Work out what this means for inference. Compare the Giacomini-White (2006) framework for rolling-window forecast comparison with the Clark-McCracken problems for nested models under expanding or population-level nulls. State what the DM test is actually testing here.

**B. "No significant improvement" vs "evidence of no improvement".** Her warning appears twice, so treat it as central. The plan must include:
- Wording rules for the thesis, with banned phrases and approved phrases, and a sweep of existing drafts. For example, question 6 of my update says "well-powered null", which contradicts the reported power of 38-53.5% for a strong shift. Replace it.
- A reporting standard for every comparison: point estimate, two-sided confidence interval, standard error and minimum detectable difference.
- A recommendation on whether to pre-specify a smallest effect size of interest and use an equivalence-style reading (TOST; Lakens 2017). It would be fixed using data through 2019 only. Say how a value in FZ0 units could be justified, and what happens if no defensible value exists.
- A clear line between the minimum detectable difference, which is design-based and legitimate, and post-hoc "observed power", which is not (Hoenig & Heisey 2001).

**C. "A coherent story rather than every exploratory result."** Propose the storyline in one paragraph. Then map each thesis claim to the single exhibit that supports it, and sort every existing result into main text, appendix or omitted. Keep the honesty requirement intact: the number of specifications and tests tried must still be disclosed (214 headline tests, 10 universes, 10 regime definitions) even where the details are cut, and the log stays available.

**D. Ambiguous or unanswered items.** Flag these and give a recommendation for each.
- "You don't need CRSP at this stage (or: check if NUS library has it)" contains two alternatives and looks like an unedited draft. Recommended reading: not required, keep the same-vendor limitation, and do a quick library check only if it costs almost nothing.
- She gave no milestones or form for the next update, which was my question 7. The plan must propose them, and I need to confirm them with her.
- She did not say whether she wants to see the frozen specification before the run. Recommend whether to send it.
- Secondary analyses I listed in section 7.3 of the update (2022 episode, conditional test) vs her "no additional robustness checks". State which stay, and why they are not new robustness checks.
- The single-pair power study has a known circularity: the simulated shifts are concentrated in SPY-IEF by construction, and the test was chosen by that power. She approved the test, so do not reopen the choice, but state how the thesis should disclose this.

**E. Errors in what was sent to her.** Check the documents she received against the sources and list every discrepancy. One is known: page 3 of the methods PDF says "8.800% power ... 2 x SE" where the source says "80% power ... 2.80 x SE". Recommend how to correct it with her, and draft a short note.

## Part 2: Audit the current state against what the hold-out needs

Report what exists, what is missing and what is inconsistent. Check at least:

- `docs/preregistration_confirmatory.md` and `scripts/confirm_01_score.py` do not exist yet, and the runner's freeze check refers to both.
- Power at the real hold-out length has not been simulated. Confirm the length by counting dates (about 1,510) and work out the run time. `scripts/explore_16_power_garch.py` previously took about an hour on 10 cores at 2,520 days. Decide the replication count, and pre-declare what happens if power is very low. My recommendation is to run the test anyway and report the power prominently, not switch tests. Also state whether a reversal of the RSC vs RSC_P ranking at 1,510 days would change anything.
- Sidedness is inconsistent. The minimum detectable difference uses two-sided 5% (`Z = 2.8016` in `scripts/explore_14_score_ladder.py`), while the power study uses one-sided 5% (`scripts/explore_20_score_power.py`). Find how each number in the chapters was produced and resolve the conflict. The one-sided equivalent multiplier is about 2.49.
- `src/returns.py` and the methods draft say "equal-weighted without rebalancing", but the variance formula and the "fixed-weight portfolio" wording imply constant weights, which is daily rebalancing. Determine what the code does and correct the description.
- `pair_variant` passes the matrix through `nearest_corr`. Check how often that repair fires on data through 2019 and whether it alters entries other than SPY-IEF, because that affects the "exact SPY-IEF specification".
- The static D vs B test has size 11.0% (CI 6.7-15.3) under the GARCH DGP, per the decisions log. This was not in the update table. State what it implies for how the thesis presents D vs B results, including the pilot and the 214-test exploration.
- `thesis/01_design_and_methods.docx` and `.pdf` are untracked and differ from the `.md`. Pick one master.
- README stage text, the title, `notes/` templates (`literature_matrix.csv`, `decision_log.md`, `thesis_notebook.md`) and whether the raw file covers 2025-12-31, checked by date and hash only.
- Whether the 62 tests still pass. Running them is allowed provided no test reads post-2019 returns; check this first.

## Part 3: Draft the confirmatory specification

She asked for this explicitly. Write it in near-final form as a section of the plan, to become `docs/preregistration_confirmatory.md` once I approve it. Leave nothing to be decided after the data are seen:

- **Hypotheses:** H0 and H1 written in terms of expected FZ0 loss, with the direction of the loss difference stated.
- **Sidedness:** one-sided or two-sided, with your recommendation and reasoning. Cover consistency with the power figures, what a result in the "wrong" direction would mean, and how the two-sided interval is reported either way.
- **Models:** RSC_P vs CCC. Give the exact definition of each: formula, pooled vs regime-weighted correlation estimator, weights, which entry switches, how the PSD repair is handled, how the mixture forecast is formed, Gaussian vs Student-t chain, and mean treatment.
- **Regime signal:** HMM on SPY, number of states, filtered probabilities through t-1, state ordering, window 1,260, refit 21, margin refit 63, and warm-start behaviour.
- **Portfolio and data:** universe, weights, return definition, raw file and SHA-256, forecast dates, and the holiday and missing-data rule.
- **Test:** VaR/ES tail level, kept clearly separate from the test's significance level (my update says "5% level", which is ambiguous). Also the loss function, DM statistic, HAC kernel and lag rule, any small-sample correction, and critical value.
- **Decision rule and interpretation:** write the wording for each possible outcome in advance: significant improvement, inconclusive, effect small enough to rule out a meaningful gain (only if a smallest effect is declared), and significantly worse. No outcome may be phrased as "no effect".
- **Secondary analyses:** the short list, labelled as secondary and unadjusted, with no p-value cited as confirmation. Include the Giacomini-White conditional test, the 2022 episode, the ladder steps with minimum detectable differences, and SPA vs GARCH-t only if they stay in.
- **Calibration:** hit rates, Kupiec, Christoffersen and Acerbi-Székely, reported alongside the loss.
- **Run protocol:** the order of freeze, commit, tag, run and score. What counts as a valid run, what happens on a crash or a numerical failure, how deviations are logged, and how post-hoc analyses are labelled.
- **Disclosure:** descriptive EDA and the data audit showed 2010-2025 summary statistics before the freeze; the test was selected from simulation; the dry-run path differs slightly from the exploration path (median absolute difference about 1e-5).

## Part 4: The workflow

Lay out the phases in order. For each one give the goal, exact tasks, files and scripts to create or change, inputs, outputs, tests or checks, how long it should take, who must approve it, and the gate that ends it. Show dependencies and which work can run in parallel. At minimum:

1. **Corrections and housekeeping:** correction note to supervisor, choose master documents, update the README, record her feedback in `notes/`, and log her decisions in `docs/decisions_log.md`.
2. **Requirements:** official format, length, deadline and title-change process. Find these from NUS or department sources where possible, and list exactly what you could not confirm and what I need to ask. Propose 2-3 narrowed titles without the allocation clause.
3. **Pre-freeze technical work:** power at hold-out length, resolve the Part 2 issues, write `scripts/confirm_01_score.py` with tests, dry-run the whole chain on `output/confirm/pseudo_forecasts.pkl`, and confirm the output tables and figures generate automatically from the pickle.
4. **Freeze:** preregistration, my approval, optionally her review, then commit and tag. Stop and ask me before any run.
5. **Hold-out:** one run with my explicit go-ahead, then frozen scoring. Include a checklist to use just before and just after.
6. **Interpretation:** apply the pre-written wording, then label anything further as post hoc.
7. **Literature review:** see Part 5.
8. **Writing:** chapter order, with methods revised first, then results for the exploration and ladder written *before* the hold-out is opened, so the hold-out cannot shape how they are framed.
9. **Reproducibility package and final checks:** one-command rebuild of every table and figure, a check that every number in the thesis traces to a result file, citation check, and wording sweep.
10. **Submission:** supervisor review rounds and buffer time.

Also give: a calendar worked backwards from the deadline (ask me for it if you cannot find it), a list of the top risks with mitigations, and the next five actions I should take this week.

## Part 5: Thesis structure and literature

- Propose the chapter outline with a purpose, target length (subject to official requirements), contents and key exhibit for each chapter. Include where each of these lives: research question, data, methodology, evaluation, results, discussion, limitations, conclusion, appendices.
- Plan the literature review around the thesis argument, not paper by paper. Suggested themes, to be checked and revised: regime-switching volatility and risk forecasting; regime gains relative to baseline complexity (Ardia et al. 2018); correlation modelling and multivariate vs univariate VaR (Santos et al. 2013; Fortin et al. 2023; Pelletier 2006; Paolella et al. 2019); stock-bond correlation sign and its drivers; forecast evaluation and elicitability; negative results and statistical power in forecasting research.
- Audit existing citations. Some are flagged [UNVERIFIED] in the repo, so list each one with its status and the step needed to verify it. Say which claims lack a source.
- State the contribution precisely, in one paragraph, without overclaiming: a decomposition under comparisons that are not all nested, with detectability reported for each. Name the closest existing work and how this thesis differs.

## Part 6: Check against established methods

For each main method, state the accepted practice, whether the current implementation follows it, and any gap and whether it is worth closing. Verify each source before relying on it. Start from: Diebold & Mariano (1995); Harvey, Leybourne & Newbold (1997); Newey & West (1994); Giacomini & White (2006); Clark & McCracken (2001); Fissler & Ziegel (2016); Patton, Ziegel & Chen (2019); Holm (1979); Hansen (2005); Hansen, Lunde & Nason (2011); Kupiec (1995); Christoffersen (1998); Acerbi & Székely (2014); Lakens (2017); Hoenig & Heisey (2001); Nosek et al. (2018) on preregistration.

Rank gaps by whether an examiner would care. Recommend fixes only where they are worth the time, given her steer not to expand scope.

## Deliverable

Write the plan to `docs/THESIS_PLAN.md`. Structure:

1. One-page summary: where the thesis stands, what she decided, what changes, and what happens next
2. Feedback analysis (Part 1)
3. State audit (Part 2)
4. Draft confirmatory specification (Part 3)
5. Workflow, calendar, risks and this week's actions (Part 4)
6. Thesis structure and literature plan (Part 5)
7. Methods check (Part 6)
8. Decisions I need to make, each with your recommendation and the consequence of choosing otherwise
9. Questions to send my supervisor, drafted and kept short

Be specific: name files, functions, formulas and numbers. Where you verified something from code or a result file, cite it. Where you are assuming, say so. If you find something in this prompt or my documents is wrong, say so plainly instead of working around it.

## How to work

Start by confirming you have read the files, then summarise in about 10 lines the current state and what you take her feedback to mean. Next ask me only the questions you cannot answer from the repo or the web, such as my deadline. Then do the analysis and write the plan. When it is done, give me the summary and the list of decisions, and stop. Do not begin any phase until I approve the plan.
