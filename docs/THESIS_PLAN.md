# Thesis plan: from supervisor feedback to submission

**Regime-Switching Risk Models for ETF Portfolios.** Written 2026-11-03. Planning document only: no code was changed, no commit was made and the hold-out was not run. One breach of the display rule occurred; see "What I did not do" below.

**Evidence labels used throughout.**
- *(result file)*: number read from a named file in the repo.
- *(computed today)*: number I computed in this session from files dated 2019 or earlier or from simulation outputs. The script is in the session scratchpad and not in the repo; each such item is listed in section 1.4 so it can be turned into a repo script.
- *(inference)*: my reading, not a verified fact.
- **[UNVERIFIED]**: not checked against a primary source.

**What I did not do.** I did not run `confirm_00_run.py holdout`, load or compute on returns after 2019-12-31, or create the tag `spec-freeze-v1`. For the hold-out period I only counted dates (text-level and `usecols=[0]` reads) and checked for empty cells (textually). I ran the test suite without the three tests that read `data/processed/pilot_*.csv` (see 3.9).

**Breach to disclose.** While searching the tests for data paths, a `grep` printed the literal expected values hard-coded in `tests/test_returns.py:113-124`: single-day SPY, IEF and GLD returns and portfolio returns for 2020-03-10 and 2023-11-01. This was unintended, the values were not used, and no specification depends on them. It is in the disclosure list (4.11).

---

## 1. One-page summary

### 1.1 Where the thesis stands
- **Evidence so far** (data through 2019 only). Regime-dependent volatility improves FZ0 loss a lot against a pooled normal in three of four ETF universes (B vs A: -0.166, -0.181, -0.159; U1 -0.020, p 0.41) *(`ladder_dm_table.csv`)*. Replacing static regime variance with GARCH(1,1) margins improves it further by 0.025 to 0.080, but this is "suggestive, not established" because the pre-declared bar (Holm-significant in at least 2 of 4 universes) was missed (1 of 4: U10, adjusted p 0.0025) *(`decisions_log.md`)*. Regime-switching correlation on top of GARCH margins (RSC vs CCC) gives -0.004 to -0.006 on ETFs, with minimum detectable differences of 0.007 to 0.014 *(`ladder_dm_table.csv`)*. That is **inconclusive, not "no effect"**.
- **Code and tests.** 62 tests exist; 59 pass with the three post-2019-reading tests excluded.
- **Missing.** `docs/preregistration_confirmatory.md`, `scripts/confirm_01_score.py`, power at the real hold-out length, all results chapters, the literature chapter, and any record of the official thesis requirements.
- **Hold-out.** The raw file has exactly **1,508** forecast dates, 2020-01-02 to 2025-12-31 *(date count; SHA-256 matches `data/raw/MANIFEST.txt`)*.

### 1.2 What Prof. Seo decided
Proceed with the ladder-plus-detectability framing; a negative-results thesis is acceptable; run the 2020-2025 hold-out; no extra macro-regime models or robustness checks; CRSP not needed (her sentence contains an unedited alternative, see 2.D); the title may be narrowed. Three cautions: do not overstate what each comparison isolates (not strictly nested), separate "no significant improvement" from "evidence of no improvement", and tell a coherent story instead of listing every exploratory result. She also asked for the hypothesis, the sidedness and the exact SPY-IEF specification **before** the run.

### 1.3 What changes
1. **The nested-ladder language goes.** B vs A is nested in volatility. D vs B, RSC vs CCC, RSC_P vs CCC and DCC vs CCC are nested only in the correlation matrix. CCC vs B and RSC vs D (my **primary margin family**), DCC vs RSC and GARCH-t vs DCC are non-nested: the GARCH margins in `fit_margins` have no regime dependence (confirmed from code, 2.A).
2. **Several statements I sent are wrong or overstated** (list in 2.E). The most consequential: "8.800% power ... 2 x SE" on page 3 of the methods PDF; the "1992-2009" label on a result that is 1992-2019; "static regime models are too conservative" (true for ETFs, not for the fund sample); and "the mean treatment does not explain the margin effect" (true for pooled vs regime means, but the zero-mean control changes the size).
3. **Sidedness is inconsistent in what I sent.** The power table is one-sided 5% (multiplier 2.49); the minimum detectable difference is two-sided 5% (2.80). Recommendation: one-sided primary test, two-sided intervals everywhere, both multipliers reported for the primary.
4. **A previously unreported fact belongs in the thesis.** The static D-vs-B test is oversized under GARCH margins (size 11.0%, CI 6.7-15.3; two-sided 17.0% at |t| > 1.96) *(`power_summary.csv`, scenario S0)*. The 37/214 raw rejections (17.3%) match that two-sided rate, so the raw count is not evidence of an effect (2.C).
5. **Writing order.** Methods first, then exploration and ladder results *before* the hold-out is opened.

### 1.4 What happens next (critical path)
Correct the record and fix the documents (1 day) -> confirm requirements and deadline (parallel) -> power at 1,508 days (background, about 1 to 2 hours) -> write `confirm_01_score.py`, small code hygiene fixes and the dry run (4 to 6 days) -> preregistration, your approval, optional supervisor look, commit, tag (1 to 2 days) -> **stop, you give the go** -> one hold-out run (about 1 minute) and frozen scoring -> pre-written interpretation. Literature and writing run in parallel throughout.

**Facts computed today that need a repo script before they are cited** (all pre-2020 or simulation-only):
| Item | Value | Script to create |
|---|---|---|
| PSD repair frequency, SPY/IEF/GLD, 2010 chain and 2016 chain | 0 of 242 and 0 of 98 matrices; last pre-hold-out window also 0 | `scripts/confirm_02_pair_repair_audit.py` |
| Dry-run vs exploration forecasts, VaR | median abs diff 1.3e-5 to 1.4e-5, max 4.2e-4 | in `confirm_01_score.py --dryrun-compare` |
| Two Yahoo downloads, daily returns through 2019 | max abs diff 2.49e-6, same 3,804 dates | `scripts/confirm_03_vendor_check.py` |
| FZ0 penalty of a proportional VaR/ES scale error (SESOI derivation) | see 2.B | `scripts/confirm_04_sesoi.py` |
| Two-sided and upper-tail rejection rates from `power/*.jsonl` | see 3.3 | extend `explore_20_score_power.py` |

### 1.5 Blocking unknown
**The deadline.** The pilot prompt of 26 Sep said "5 weeks left" *(`docs/PILOT_PROMPT.md:2`)*, which would already have passed. I could not find an official deadline (section 5.2). The calendar in section 5 is therefore written in working days before submission, with two worked examples. Please tell me the real date.

---

## 2. Feedback analysis (Part 1)

### 2.0 Point-by-point table

| # | What she said | What it commits me to | What she left open | What must change | Done when |
|---|---|---|---|---|---|
| 1 | "Proceed with your current approach without major changes." | No redesign. Freeze and run. | Whether "current approach" includes the single-pair choice (see #10). | Nothing structural. | Plan approved by you. |
| 2 | "Ladder-plus-detectability is appropriate; a thesis centred on negative results is acceptable." | Keep the ladder; headline is detectability, not a positive effect. | What counts as "negative" if the hold-out is inconclusive. | Rewrite the headline claim in every draft as "inconclusive/limited power" where that is the case (2.B). | Wording sweep passes (2.B.1). |
| 3 | "I support proceeding with the 2020-2025 hold-out." | One run, after freeze. | Whether she wants to see the frozen spec first. | Preregistration (section 4); decide whether to send it (2.D.3). | Tag exists, run logged. |
| 4 | "No additional macro-regime models or robustness checks." | No new models or new sensitivity grids. | Whether secondary analyses (2022, conditional test) count as "robustness checks". | Keep secondary list short and labelled (2.D.4). New ideas go to future work. | Secondary list in the preregistration has at most six items. |
| 5 | "You don't need CRSP at this stage (or: check if NUS library has it)." | Keep Yahoo; state same-vendor limitation. | Contains two alternatives; looks unedited (2.D.1). | Limitation text; optional one-line library check. | Limitation in chapter 8; one line in the log. |
| 6 | "You can narrow the title since you dropped the allocation extension." | New title. | Process for changing a registered title is unknown. | Titles in 5.3; README title. | Official title confirmed. |
| 7 | "Do not overstate what each comparison isolates; not all strictly nested." | Per-step "what differs" table and claim limits (2.A). | None. | Rewrite methods section 1, update-style summaries, README. | Overstatement list in 2.A.3 fully replaced. |
| 8 | "Distinguish lack of significant improvement from evidence of no improvement, given limited power." | Wording rules, CI-first reporting, MDE (2.B). | Whether she wants an equivalence test (2.B.3). | Sweep of all drafts; reporting standard in code. | Sweep clean; every results table has CI + MDE. |
| 9 | "Coherent story, not every exploratory result." | Main / appendix / omitted sorting (2.C). | How much of the exploration she wants shown. | Chapter map in 6. | Every claim maps to one exhibit. |
| 10 | "The proposed confirmatory test looks appropriate." | RSC_P vs CCC is frozen. Do not reopen. | Her approval rests on my description, which contained the 5% ambiguity and the circular power argument. | Disclose circularity (2.D.5). | Disclosure paragraph in preregistration. |
| 11 | "Specify hypothesis, one- or two-sided, exact SPY-IEF specification before running." | Section 4 of this plan, then a frozen file. | Which sidedness she prefers. | `docs/preregistration_confirmatory.md`. | File committed and tagged. |
| 12 | "A non-significant result does not imply absence of an effect." (repeat of #8) | Pre-written outcome wording with no "no effect" outcome. | None. | Section 4.8. | Outcome table frozen. |
| 13 | "Check official format and length; otherwise no preference." | Find requirements. | Not found by me (5.2). | Ask programme office. | Written requirements on file in `notes/`. |
| (unanswered) | My Q7: milestones and next-update format. | I must propose them and she must accept. | Everything. | Section 5.4 proposal. | Her reply recorded in `notes/`. |

### 2.A "The models are not all strictly nested"

#### 2.A.1 What each ladder step actually changes (from code)

Read from `src/explore_ladder.py`, `src/explore_routes.py`, `src/explore_wf.py`, `src/engine.py`. "Static arms" = A, B, D (`run_static_ladder`, mean mode `pooled`). "GARCH arms" = CCC_S, RSC_S, RSC_P (`run_rs_corr`).

Facts that drive everything below:
- **GARCH margins have no regime dependence.** `fit_margins` fits one Gaussian-QML GARCH(1,1) per asset on the whole window. The HMM enters only through the correlation matrices `R_k` and the mixture weights. In RSC the volatility vector is the same in both mixture components.
- **CCC does not use the regime signal at all.** `sets["CCC_S"] = [Rs_pool]` and `pm = [1.0]`: one Gaussian component.
- **Static arms hold volatility fixed within a 21-day block** (only the mixture weights move daily). GARCH arms update volatility daily from realised returns with parameters refitted every 63 days.
- **Correlation inputs differ.** B uses the pooled correlation of *raw returns*; CCC/RSC use the correlation of *GARCH-standardised residuals*.
- **"Pooled mean" is not the same number in the two families.** Static arms use the window sample mean (`means["A"][0]`). GARCH arms use the QML constant mean `params[0]/100`. Both are constant across regimes, but not equal.
- **The t-chain df is estimated differently.** Static arms: smoothed in-window mixture standardisation (`_in_window_nu`). GARCH arms: in-window pooled-correlation standardisation.
- **In-window regime weights are smoothed probabilities** (`predict_proba` = forward-backward within the window; no data after the window end). The forecast-day mixture weights are filtered and propagated one step.

| Step (richer vs baseline) | Volatility | Correlation | Mean | Distribution | Refit / update | Class |
|---|---|---|---|---|---|---|
| B vs A | Regime-specific SDs (mixture) vs single pooled | same pooled raw-return correlation | pooled in both | 2-component vs 1-component | both 21-day | **Nested** in volatility (A = B with equal SDs). Best-isolated step. |
| D vs B | same regime SDs | regime-specific raw-return correlations (all pairs) vs pooled | pooled in both | same | same | **Nested in the correlation matrix.** Clean contrast, but static: SDs fixed in-block. |
| CCC vs B | GARCH(1,1), one regime vs regime-switching static SD | correlation of standardised residuals vs raw-return correlation | QML mean vs sample mean | 1 component vs 2 | daily vol update, 63-day parameters vs 21-day | **Non-nested.** Changes volatility model, correlation input, mean estimator, mixture. |
| RSC vs D (*primary margin family*) | single-regime GARCH vs regime-specific static SD | regime-specific, on standardised residuals vs raw | QML vs sample mean | 2 components both | as above | **Non-nested.** A model-class comparison, not "adding GARCH dynamics within a regime". |
| RSC vs CCC | identical | regime-specific vs pooled, same z | identical | 2 components vs 1 | identical margins | **Nested in the correlation matrix only.** Cleanest contrast on the ladder. |
| RSC_P vs CCC (*frozen confirmatory test*) | identical | only (SPY, IEF) entry regime-specific | identical | 2 components vs 1 | identical margins | **Nested in one correlation entry.** |
| DCC vs CCC | identical GARCH fit | DCC(1,1) recursion vs constant | identical (QML) | Gaussian (N chain) | DCC refit 63 days | Nested in parameter space (CCC = DCC with a = b = 0, on the boundary). |
| DCC vs RSC | identical GARCH | smooth recursion vs regime-weighted | identical | N chain: single normal vs 2-component mixture | different | **Non-nested.** |
| GARCH-t vs DCC (t chain) | univariate GARCH on portfolio return vs multivariate | implicit | own fitted mean | own df | own fit | **Non-nested**, different information set (portfolio vs components). |

#### 2.A.2 The most each comparison can honestly claim
- **B vs A:** "Allowing the volatility to take two regime-specific levels, with the HMM mixture, lowers expected FZ0 by X relative to a pooled normal."
- **D vs B:** "Letting all correlations be regime-specific (static) changes expected FZ0 by X." Add the size caveat from 2.C.
- **CCC vs B and RSC vs D:** "A single-regime GARCH(1,1) volatility model with daily updating and standardised-residual correlation performs better/worse than regime-specific static covariance." It cannot be called "the effect of volatility dynamics", because it also removes regime dependence from the volatility and changes the correlation input, the mean estimator and the mixture. The zero-mean control shows the mean part is not negligible (margin effect U1 -0.0259 pooled, -0.0339 zero) *(`ladder_dm_table.csv`)*.
- **RSC vs CCC and RSC_P vs CCC:** "Given the same GARCH margins and standardised residuals, letting the correlation matrix (or one entry) switch with the HMM regime changes expected FZ0 by X." This is the only step that supports the sentence "isolates the correlation channel", and only within this volatility model.
- **DCC vs RSC:** a comparison of two ways of letting correlation move, not of one ingredient.

#### 2.A.3 Sentences that overstate, with replacements

| Where | Current text | Replace with |
|---|---|---|
| Methods §1; update §2 | "a nested 'ladder' ... Differences in forecast loss between adjacent rungs then attribute the improvement to a single ingredient." | "a sequence of comparisons that share data, regime signal and estimation window. Two of them (D vs B, RSC vs CCC) differ in the correlation matrix only; others also differ in how volatility is modelled and are interpreted as comparisons between model classes." |
| Methods §1 table, row CCC | "replaces static within-regime variance by volatility dynamics" | "replaces regime-specific static variance by a single-regime GARCH(1,1) (no regime dependence)" |
| Methods §1 table, "relative to the rung below" | Implies CCC is D plus something. | Add a column "compared with" (CCC vs B; RSC vs D; RSC vs CCC). |
| Methods §1 (ii) | "volatility evolve within a regime" | "volatility follow GARCH(1,1) dynamics (not regime-specific in the present specification)" |
| Methods §5 | "the static and GARCH-margin arms differ only in how volatility is modelled" | "differ in the volatility model; the constant mean is estimated differently (window mean vs QML), which the zero-mean variant addresses" |
| Update §2 | "Mean control ... so the comparison isolates volatility." | "... so the comparison does not depend on regime-specific means." |
| Update §4c | "The mean treatment does not explain the margin effect. On the pilot universe it is -0.0259 with pooled means and -0.0263 with regime means." | Report all three mean sets: pooled -0.0259, regime -0.0263, zero -0.0339 (U1) *(`ladder_dm_table.csv`)*; say the size depends on the mean treatment while the sign does not. |
| Methods §3 | "Smoothed probabilities ... are never used for forecasting." | "Regime moments in each window are weighted by smoothed in-window probabilities (data up to the window end only). Forecast-day mixture weights are filtered probabilities propagated one step." |
| Update §2 | "Only filtered probabilities through day t-1 are used to forecast day t" | same replacement |
| Methods §6 | "Newey-West (Bartlett) errors and automatic lag selection" | "Bartlett kernel with lag floor(4(T/100)^(2/9)) (7 at T = 1,508), the Newey-West (1994) rule of thumb, not their data-driven selection" |
| Methods §2; `src/returns.py`; README | "equal-weighted without rebalancing" | "equal-weighted with constant weights (1/3 each), i.e. rebalanced daily" (3.5) |
| Update §4c | "about half of what the design could detect" | "between a third and a half of the minimum detectable difference (0.36, 0.52, 0.39, 0.46 for U1, U3, U8, U10, *computed from `ladder_dm_table.csv`*); the 95% interval is the inference" |
| Update/recap | "Regime vs smooth correlation (DCC vs RSC) is indistinguishable" | "no significant difference in the four ETF universes (p 0.16 to 0.99; the minimum detectable difference is 0.018 to 0.030)" |
| README/recap | "the correlation channel is not detectable" | "not detected; the design could detect about 0.007 to 0.014" |

#### 2.A.4 What this means for inference
- **What the DM test tests here.** Each model is a forecasting *procedure*: the model, the 1,260-day rolling window, the refit schedule and the HMM warm-start chain. The Diebold-Mariano statistic tests whether two procedures have the same expected FZ0 over the evaluation sample, with a HAC variance for serial dependence in the loss difference. That is the Giacomini-White (2006) "equal predictive ability of the forecasting methods" reading with a finite rolling window, in which estimation uncertainty does not vanish. It is **not** a test of whether the larger model's extra parameters are zero in the population.
- **Why Clark-McCracken is the relevant warning, not the relevant test.** For nested models under a population null (the restricted model is true), expanding-window out-of-sample statistics have non-standard limiting distributions, and DM with normal critical values is typically too conservative (Clark & McCracken 2001; the Clark-West 2007 adjustment gives approximately normal tests). Those results do not carry over directly to a fixed rolling window with a nonvanishing-estimation-error null. I verified bibliographic details and abstract-level content only; derivations are **[UNVERIFIED]**. In the simulation, the null behaviour is what Clark-McCracken would predict qualitatively: under S0 the richer model is slightly *worse* on average (mean t +0.079 for RSC vs CCC, +0.243 for RSC_P vs CCC; mean FZ0 difference +0.0001) *(computed today from `power/S0_vol_only.jsonl`)*, so the one-sided "richer is better" test is conservative or exact (size 4.5%), while the upper tail is not (below).
- **McCracken (2020) and Zhu-Timmermann.** Abstract-level evidence (search summaries, not full texts): McCracken (*Econometrica* 88(4), 1753-1754) gives a counterexample to asymptotic normality of a DM-type statistic under the null; a working paper by Zhu and Timmermann argues the null cannot hold under rolling windows for many processes. Both are **[UNVERIFIED]** beyond abstracts. Practical consequence: size must be demonstrated by simulation, which the power study does (S0 rows), and the thesis should say so rather than cite asymptotics.
- **Sidedness of the size check.** Under S0 with 2,520 days: RSC vs CCC rejects "richer better" at t < -1.645 in 4.5% of reps, and "richer worse" at t > +1.645 in 8.0%; for RSC_P vs CCC 4.5% and 8.0% *(`power_summary.csv`, `wrong_sign` column)*. At |t| > 1.96 the upper tail is 4.5% for both *(computed today)*. This is why section 4 uses t > +1.96 for "significantly worse".
- **No whole-pipeline HMM bootstrap exists.** The null-scenario rejection rate stands in; this is already a stated limitation.

### 2.B "No significant improvement" vs "evidence of no improvement"

#### 2.B.1 Wording rules and sweep

**Banned** (unless a pre-declared equivalence test passed): "no effect", "no correlation channel", "correlation does not matter", "does not help", "no gain", "no improvement", "adds nothing", "ruled out", "rules out", "well-powered null", "confirms the absence", "indistinguishable" (without an interval), "evidence that regimes do not ...", "the null result shows".

**Approved patterns:**
- "We do not detect an improvement (estimate X, 95% CI [a, b], minimum detectable difference M)."
- "The data are consistent with effects between a and b; effects larger than M would have been detected 80% of the time."
- "The estimated difference is X; this is inconclusive for effects below M."
- "Not statistically distinguishable at the 5% level" **only** with the interval in the same sentence.
- For power: "power was P% (95% simulation CI) against the stated simulated shift", never "well-powered".

**Sweep hits (from the grep over README, update, methods, exploration summary, recap, decisions log, source docstrings):**
| File:line | Text | Action |
|---|---|---|
| `output/SUPERVISOR_DRAFT_2026-10-27.md:128` | "a well-powered null (no detectable gain ..., with the power reported)" | Replace: "a thesis whose main result is an inconclusive or limited-power finding on correlation switching, reported with confidence intervals and minimum detectable differences". Power was 38.0% and 53.5% in the strong-shift scenario *(`power_summary.csv`)*, not well-powered. |
| `output/SUPERVISOR_DRAFT_2026-10-27.md:8` | "I find no detectable gain from letting correlations switch" | Acceptable only with CI/MDE; rewrite as "I do not detect ...; the design could detect about 0.007 to 0.014". |
| `output/SUPERVISOR_DRAFT_2026-10-27.md:77` | "Correlation switching adds little" | "Estimated effects are -0.004 to -0.006, smaller than the minimum detectable difference". |
| `output/SUPERVISOR_DRAFT_2026-10-27.md:80` | "indistinguishable in four of five samples" | add intervals |
| `output/explore/EXPLORATION_SUMMARY.md:9` | "has no correlation channel to detect, and neither does any diversified one" | "shows correlations that fall in stress rather than rise, so the 'breakdown' this test targets is absent in the sample" (a descriptive statement about the sample) |
| `output/explore/EXPLORATION_SUMMARY.md:37` | "statistically indistinguishable in 9 of 11 samples" | add CI/MDE or move to appendix |
| `output/THESIS_PROGRESS_RECAP.md:13,132,163` | "no detectable ... cannot rule out"; "plain null" | the recap is internal; keep but do not copy into thesis |
| `output/FURTHER_EXPLORATION_RESEARCH.md` | "honest null", "clean, honest out-of-sample null" (recap row 3) | do not reuse |
| `README.md` stage text | "letting correlations switch gives no detectable gain ... even in the 1992-1999 era" | rewrite after the hold-out |

Run the sweep as a script before every draft goes out: `scripts/check_wording.py` with a banned-phrase list (30 lines).

#### 2.B.2 Reporting standard for every comparison
Every row of every comparison table contains: **mean loss difference (richer minus baseline), HAC standard error, 95% two-sided CI (d ± 1.96 SE), t and the p-value labelled (one-sided/two-sided), n, and MDE = 2.8016 x SE** (two-sided 5%, 80% power). For the primary test also report 2.486 x SE (one-sided). The ladder tables already hold `mean_diff`, `se`, `t`, `p`, `mde80` *(`ladder_dm_table.csv`)*; only the CI column and a sidedness label are new.
Never write "power" about an observed result (2.B.4).

#### 2.B.3 Smallest effect of interest and an equivalence reading (Lakens 2017)
**Recommendation: declare one reference value, use it as a one-sided bound, do not promise equivalence.**
- **Justification in FZ0 units, from information available before 2020.** FZ0 is the expected score. If the forecaster's VaR and ES are both scaled by a factor c relative to a correctly specified distribution, the expected-loss penalty is approximately k (c-1)^2. For a standard normal at alpha = 5% *(computed today, analytic, no market data)*: an overstatement of 5% costs +0.0043, 2% costs +0.0007, understatement of 5% costs +0.0051, of 10% +0.0222. For unit-variance Student-t with 6 df the numbers are about 20% lower (+5%: 0.0034). So a loss reduction of **0.002** corresponds to removing a proportional VaR/ES scale error of roughly 3%. That is a defensible "smallest improvement a risk manager would care about" only as an argument, not a fact; **[assumption: 3% capital-scale error is economically meaningful]**.
- **What the design can show.** Expected hold-out SE for RSC_P vs CCC is about 0.0013 to 0.0015 (SE was 0.00133 on 1,510 days and 0.00147 on 1,006 days in `routes_dm_table.csv`, `RSC_P_N` vs `CCC_S_N`, alpha 5%). The one-sided lower bound d - 1.645 SE is about d - 0.0021, so ruling out an improvement larger than 0.002 requires d >= 0 almost exactly. Probability is low. A symmetric TOST with margin 0.002 is out of reach (90% CI half-width 0.0021 alone exceeds the margin).
- **Therefore:** declare SESOI = 0.002 (to be re-derived by `confirm_04_sesoi.py` and frozen), define outcome O3 (4.8) as "the lower 95% one-sided bound exceeds -0.002", and state in the preregistration that this outcome is expected to be unlikely. If you do not accept the 3% argument, do not declare a SESOI: report CI and MDE only and use no equivalence wording. Either is honest; declaring none is simpler and costs nothing in credibility.

#### 2.B.4 MDE vs "observed power"
- **MDE is design-based:** 2.8016 x SE, or 2.486 x SE one-sided, depends on the standard error, which in turn depends on n and loss variance. It says what the test would detect with 80% probability. It is legitimate to report next to a result.
- **"Observed power" is post hoc:** power computed at the observed estimate is a monotone function of the p-value and carries no extra information (Hoenig & Heisey 2001, *The American Statistician* 55(1), 19-24, bibliographic record checked). Never write "the test had X% power to detect the observed difference". Rule: power is reported only for stated effect sizes (scenario shifts, SESOI, or MDE), never for the observed estimate.
- Analytic illustration with an assumed SE of 0.0014 *(computed today, not a result)*: one-sided power is about 18% for a true d of -0.001, 41% for -0.002, 69% for -0.003, 80% for -0.0035. The assumed SE might be wrong in 2020 (COVID) and 2022.

### 2.C "A coherent story rather than every exploratory result"

#### 2.C.1 Storyline (one paragraph)
*Where does regime information help one-day tail-risk forecasts for a diversified ETF portfolio, and how large an effect could this data ever reveal?* Using a sequence of comparisons that share data, regime signal and estimation window, I find that giving the volatility model a regime dependence lowers FZ0 loss substantially against a pooled normal, and that a single-regime GARCH(1,1) model class improves on static regime covariance by a further 0.025 to 0.080 (suggestive: the pre-declared replication bar was missed). The correlation channel is the ingredient the literature and my motivating stock-bond reversal point at, and it is also the smallest: estimated gains from regime-dependent correlation on GARCH margins are -0.004 to -0.006, below the 0.007 to 0.014 the design can detect, and a simulation study over 2,520 test days puts one-sided power for the correlation step at 22.5% to 27.0% for a moderate simulated shift and 38.0% to 53.5% for a strong one. A single pre-specified test of switching the SPY-IEF correlation on the 2020-2025 hold-out, which contains the 2022 reversal, is reported with its confidence interval, minimum detectable difference and simulated power. The contribution is a detectability-aware decomposition, not a better model.

#### 2.C.2 Claim -> exhibit map

| # | Claim | Single exhibit | Source |
|---|---|---|---|
| 1 | Regime volatility improves on a pooled normal | Table: B vs A across five samples | `ladder_dm_table.csv` |
| 2 | A single-regime GARCH model class improves on static regime covariance (suggestive) | Forest plot, rows CCC vs B and RSC vs D with MDE | `output/figures/ladder_forest.png` |
| 3 | The pre-declared replication bar was not met | One-row table in the text, 4 universes Holm | `ladder_dm_table.csv` (`p_holm_primary`) |
| 4 | Correlation switching on GARCH margins: estimated effects are small relative to what is detectable | Forest plot row RSC vs CCC | same figure |
| 5 | The design has limited power for correlation shifts | Power table at hold-out length (new) | new `power_1508` output |
| 6 | The motivating regime is absent from 2010-2019 | Share of days with positive 252-day stock-bond correlation by era | `longhistory_summary.json` |
| 7 | Static regime-correlation p-values are anti-conservative under GARCH margins | S0 size row, static D vs B | `power_summary.csv` |
| 8 | Hold-out result of the one frozen test | Result table with CI, MDE, power, hit rates | new scoring output |
| 9 | Calibration: static arms too conservative on ETFs, GARCH arms near nominal | Hit-rate table | `ladder_loss_table.csv` |

#### 2.C.3 Where everything goes

| Result | Place | Disclosure that must survive |
|---|---|---|
| Ladder (5 samples, 8 steps, MDE) | Main text | — |
| Power with GARCH DGP (original 2,520 days and the 1,508-day rerun) | Main text | DGP is an assumption; shift concentrated in SPY-IEF |
| Pilot go/no-go scorecard | Main text, one table | Two criteria were marginal |
| Stock-bond correlation sign by era | Main text (motivation) | Fund proxies, mutual funds |
| Hold-out test | Main text | Preregistration; deviations |
| Zero-mean and regime-mean controls | Appendix | Size of the margin effect depends on the mean treatment |
| Student-t chain, alpha 2.5%, sub-periods | Appendix | Secondary, unadjusted |
| 214-test D-vs-B grid | Appendix, one table + counts | 214 tests, 37 raw rejections (18 favour D, 19 favour B), none Holm-significant (smallest 0.141) *(`backtest_dm_table.csv`, computed today)*; size distortion (2.C.4) |
| 10 universes, 10 regime definitions, regime-definition comparison | Appendix summary | "10 universes, 10 regime definitions, 214 headline tests were tried; the log lists all" |
| SPA / MCS | Appendix | p 0.13 to 0.96 (consistent), unadjusted for other families |
| Giacomini-White conditional on funds (p 0.047) | Appendix, labelled hypothesis | One of several secondary tests; absent in 1992-1999; N = 2 so RSC_P = RSC there |
| Route M (Kendall), exceedance correlation, total correlation | Omitted from text; counted in disclosure | Listed in decisions log |
| 3-/4-state HMMs, bond-aware regime signals | Omitted from text; counted | Same |
| Universe screen (correlation moves) | Appendix, one figure | Descriptive, in-sample, smoothed weights |

**Honesty requirement kept:** chapter 4 states in one sentence: "Exploration comprised 10 ETF universes, 10 regime definitions, two tail levels and a long-history fund sample (214 headline tests); every specification is logged in `docs/decisions_log.md`, and no specification was dropped."

#### 2.C.4 What the 11.0% size of the static D-vs-B test implies
Under the GARCH-margin DGP with no correlation change (S0), the static D-vs-B DM test rejects at one-sided 5% in 11.0% of replications (CI 6.7-15.3) and at two-sided |t| > 1.96 in 17.0% *(`power_summary.csv`; two-sided computed today from `S0_vol_only.jsonl`)*. Wrong-sign rate is 14.0%. The exploration grid has 37 of 214 raw two-sided rejections = 17.3% *(computed today)*. The match is suggestive, not proof (stylised DGP, tests not independent). Consequences:
1. The D-vs-B p-values (pilot and the 214-test exploration) are anti-conservative whenever the data have volatility clustering. Their Holm adjustment is not valid, but nothing was significant after it, so the "no significant effect" statement is unaffected. What must not be written is "37 of 214 tests were significant, more than the 11 expected by chance".
2. D-vs-B should be presented with its interval and a note that the nominal size is unreliable. The RSC-vs-CCC step, with margins fixed, has size 4.5%.
3. The pilot report claimed size 5.0% for D vs B *(stylised DGP without GARCH)*. State that this was a different DGP.
4. This is an omission from the update I sent (2.E).

### 2.D Ambiguous or unanswered items

1. **CRSP.** "You don't need CRSP at this stage (or: check if NUS library has it)." *Recommended reading:* not required; keep the same-vendor limitation; the 1992-2019 fund sample is not a second vendor either. Spend at most ten minutes asking the library or checking its database list; do not let this slow the freeze. Log the answer.
2. **Milestones and form of the next update (my Q7).** She did not answer. Propose in 5.4; confirm by email.
3. **Show her the frozen specification before the run?** *Recommend yes, briefly.* She asked for it, the cost is a short wait, and a pre-run look makes the later "I followed the plan" defensible. Send the final preregistration, ask for objections within 3 working days, and state that absent a reply you will proceed on day 4. This does not make her approval a precondition. Do not send before you have approved it.
4. **Secondary analyses vs "no additional robustness checks".** Keep: (a) the 2022 episode of the *same* primary comparison; (b) the Giacomini-White conditional test on the *same* two forecast series; (c) ladder steps at hold-out with MDE (needed for the framing she approved; the forecasts already exist in the run); (d) alpha 2.5% and Student-t chain of the same comparison; (e) SPA vs GARCH-t (already declared). None adds a model, a universe, a regime definition or a data source. They are subsets or conditional views of forecasts the run produces anyway; she objected to new checks. Cap at six items (4.9), all unadjusted, none citable as confirmation.
5. **Circularity of the single-pair choice.** The power study simulates stress correlation shifts that are largest in SPY-IEF *by construction* (scenarios in `config/pilot.yaml`: S1 stress correlation [0.00, 0.20, 0.30], S2 [0.40, 0.40, 0.30] for (eq-bond, eq-gold, bond-gold) against calm [-0.30, 0.05, 0.30]), and the test was selected by that power. She approved the test; do not reopen. Disclosure text for the thesis and preregistration: *"The choice of RSC_P vs CCC over RSC vs CCC was made from simulated power on a process in which the stress-correlation change is largest in the SPY-IEF pair. The advantage of the single-pair test (power 27.0% vs 22.5% moderate, 53.5% vs 38.0% strong shift) therefore reflects that design. The pair was fixed in advance by the stock-bond hypothesis, not by scanning."*

### 2.E Errors in what was sent to her

Documents compared: `Thesis_Update1.pdf` (hash 467a81ed...) and the downloaded methods PDF (hash 1689e6f5...) against `output/SUPERVISOR_DRAFT_2026-10-27.md` and `thesis/01_design_and_methods.md`, plus the `.docx` in `thesis/`.

**Provenance finding.** Three versions of the methods chapter exist: the `.md` (committed 2026-10-27 16:14), the repo `.pdf` (16:23, matches the `.md`), and the `.docx` (16:42, hand-edited). The version she received was converted from the `.docx`. The `.docx` carries the "8.800%" error, which the `.md` and the repo PDF do not.

| # | Where | Sent | Correct / source | Severity |
|---|---|---|---|---|
| E1 | Methods p.3, "Reporting effect sizes" | "8.800% power ... 2 x SE" | "80% power ... 2.80 x SE" (`.md`; code `Z = 2.8016`) | **High**: a reader computes an MDE 29% too small |
| E2 | Update §3 | "replication on the 1992-2009 fund sample ... p = 0.12" | The p = 0.1216 test is the full 1992-2019 sample, n = 7,053 *(`ladder_dm_table.csv`, `L1_longhist`, `margin_effect`)*. A 1992-2009 subsample was not scored. The decisions-log title has the same slip. | **High**; also the "independent of the ETF samples" claim does not hold for the 2010-2019 part |
| E3 | Update §4c, calibration bullet | "Static regime models are too conservative (5% hit rates 2.8% to 4.2%)" | True for the four ETF universes (A 2.8-3.4%, B 2.8-4.2%, D 3.0-4.0%). For the fund sample B is 5.4% and D 5.3% *(`ladder_loss_table.csv`)*. | Medium |
| E4 | Update §4c | "The mean treatment does not explain the margin effect." | Zero-mean margin effect U1 -0.0339, U3 -0.0569, U8 -0.0504, U10 -0.0814, with smaller p-values; the RSC-vs-CCC step is about 0.000 in U1/U3 with zero mean vs -0.004 pooled *(`ladder_dm_table.csv`)*. | Medium: selective |
| E5 | Update §4d vs methods §6 | Power table "one-sided 5% test" but the minimum detectable difference "two-sided" (2.80) | Inconsistent sidedness, not flagged | Medium |
| E6 | Update §2; methods §1 | "nested models ... attribute an improvement to a single ingredient" | 2.A.3 | **High** (her point) |
| E7 | Methods §6 | "automatic lag selection" | fixed rule floor(4(T/100)^(2/9)) *(`src/engine.py:dm_test`)* | Low |
| E8 | Methods §3, update §2 | smoothed probabilities "never used" | smoothed in-window weights are used for regime moments | Medium |
| E9 | Methods §2 | "equal-weighted without rebalancing" | constant weights, rebalanced daily | Medium |
| E10 | Update §4c | "about half of what the design could detect" | 0.36 to 0.52 of the MDE (computed today) | Low |
| E11 | Update §4d | omits the static D-vs-B size of 11.0% and the 8% null wrong-sign rate for the correlation steps | In `decisions_log.md` and `power_summary.csv` | Medium |
| E12 | Update Q6 | "well-powered null" | power 38.0%/53.5% for the strong shift | **High** (her point) |
| E13 | Update §7.2 | "5% level" | ambiguous between tail level and test size | Medium |
| E14 | Methods (sent version only) | repo paths and "logged in docs/decisions_log.md" replaced by "stored internally" | harmless but the docx diverged from the md | Low |
| E15 | Methods §4 | "Student-t ... common degrees of freedom, estimated by maximum likelihood on in-window standardised portfolio returns" | The standardisation differs between static and GARCH arms (2.A.1) | Low |

Numbers I could not fault: the 20 ladder table cells (re-derived from `ladder_dm_table.csv`; all match after rounding), the MDE row (0.0110, 0.0073, 0.0139, 0.0120, 0.0162), 37/214 with 18 and 19, smallest Holm 0.141, 105/0, 0/96, 0/124, the power table, the SPA p-range 0.13 to 0.96 (consistent p), the GW numbers, 62 tests (59 + 3), and the 2.5e-6 download agreement (2.49e-6 *computed today*; the update cites no result file, so add `confirm_03_vendor_check.py`).

**Recommended handling.** One short email, sent soon, before the preregistration so she reads corrected numbers; attach corrected PDFs generated from the `.md`. Draft:

> Dear Prof. Seo, thank you for the feedback. While preparing the preregistration I found some errors in the two documents I sent, none of which changes the results. (1) Methods p.3: the minimum detectable difference is 2.80 x SE at 80% power (two-sided 5%); the PDF printed "8.800% power ... 2 x SE" due to a conversion error. (2) The fund-sample replication (p = 0.12) is the full 1992-2019 sample, not 1992-2009, and it overlaps in time with the ETF samples. (3) The "static regime models are too conservative" statement applies to the ETF universes, not to the fund sample. (4) The power table is one-sided 5% while the minimum detectable difference is two-sided; the confirmatory specification will state both. (5) I have also removed the word "nested" where models are not strictly nested, following your comment. Corrected versions are attached. I will send the frozen specification before running the hold-out and will not run it before [date]. Could you also confirm milestones for the next update? Best regards, Sanjeev

---

## 3. State audit (Part 2)

### 3.1 Missing artefacts
- `docs/preregistration_confirmatory.md` and `scripts/confirm_01_score.py` do not exist; `check_freeze()` in `scripts/confirm_00_run.py` diffs both against the tag. If the tagged commit lacks them, `git diff` shows them as added later and the check blocks a later addition, so both must be in the tagged commit.
- `docs/preregistration.md` is the pilot's, unchanged.
- No results chapters; no thesis draft beyond `thesis/01_design_and_methods.md`.

### 3.2 Hold-out length and run time
- Raw file `data/raw/spy_ief_gld_raw_2026-09-26.csv` has 5,497 dates (2004-11-18 to 2026-09-25). SHA-256 `0ab8c7f3...150e29` equals the MANIFEST entry.
- Hold-out dates: 2020-01-02 to 2025-12-31, **1,508** rows (253, 252, 251, 250, 252, 250 per year). 2025-12-31 is present. No empty adjusted-close cell in any of those rows (textual check). Rows through 2019: 3,805. The first 1,260-return window for the first forecast ends 2019-12-31.
- Data after 2025-12-31 exist in the file (to 2026-09-25) and are never read by the runner (`load` truncates at `last_data` before computing).
- **Runner time.** The dry run (1,006 days) took 37.9 s *(`pseudo_forecasts.pkl`, `runtime_s`)*, so the hold-out run is about 60 s *(inference)*.
- **Power simulation time.** The earlier study took about 32 s per replication per core at 2,520 test days and about an hour wall-clock on 10 cores *(`CONTINUE_PROMPT.md`)*. At 1,508 days there are about 72 refits instead of 120, so about 19 s per replication per core *(inference)*.

### 3.3 Power at the hold-out length
- **Replications.** 500 per scenario x 4 scenarios = 2,000 replications; about 1 to 2 hours *(inference; run `--time` first)*. 500 gives a binomial SE of 2.0 points at 40% power, against 3.5 points with 200. Do not go higher; the DGP is an assumption and more replications do not fix that.
- **Implementation.** Do not modify `explore_16_power_garch.py` or its outputs. Create `scripts/explore_21_power_holdout_length.py` as a copy with `test_days = 1508`, writing to `output/explore/ladder/power_1508/`, and extend the summary to report one-sided and two-sided rejection rates, upper-tail rate, and the standard error of the mean loss difference.
- **Interim projection** *(computed today, normal approximation, SE scaling as 1/sqrt(T), not a simulation)*: for RSC_P vs CCC one-sided power falls from 53.5% to about 38% (strong shift) and from 27.0% to about 20% (moderate); two-sided from 44.0% to about 29% and from 17.5% to about 12%. For RSC vs CCC strong: 38.0% to about 27%.
- **Pre-declared rule for low power:** run the test anyway and report the simulated power prominently, in the abstract and the results table. Do not switch tests. If simulated power in the strong-shift scenario is below 30%, the result chapter's first sentence says the hold-out cannot be expected to detect any simulated shift. Rationale: the supervisor approved the test; the thesis's contribution is the detectability analysis.
- **Would a reversal of the RSC vs RSC_P ranking at 1,508 days change anything?** No. The projected ordering is unchanged (RSC_P 38%, RSC 27% in the strong scenario; moderate-scenario gaps of about 3 points are below the Monte Carlo resolution of 500 replications). Switching after seeing a second simulation would be a second selection on the same DGP, using a result that cannot be independent of the first. State this in the preregistration: *the test is RSC_P vs CCC regardless of the 1,508-day simulation*.

### 3.4 Sidedness conflict: how each number was produced
| Quantity | Where | Convention |
|---|---|---|
| Power / size tables in the update (4.5%, 22.5%, 38.0%, 53.5% ...) | `explore_20_score_power.py`, `CRIT = 1.6449`, reject if t < -CRIT | **one-sided 5%** |
| Original pilot power (25.5%, 52.5%) | WP2 pipeline, "one-sided DM, 5%" per recap | one-sided 5% |
| Minimum detectable difference in `ladder_dm_table.csv` | `explore_14_score_ladder.py`, `Z = 2.8016` = 1.96 + 0.8416 | **two-sided 5%, 80%** |
| MDE in `routes_dm_table.csv`, `backtest_dm_table.csv` | `explore_09`, `explore_06`: `2.8 x SE` | two-sided 5%, 80% (rounded 2.8) |
| p-values in the DM tables | `dm_test`: `2*(1 - Phi(|t|))` | two-sided |

The mismatch is real but not an error in any single number. Resolution: keep the existing columns, label every table with its sidedness, report both multipliers for the primary test (2.8016 and 1.6449 + 0.8416 = 2.4865), and add two-sided power columns to the new simulation.

### 3.5 Portfolio return definition
`src/returns.py::calculate_equal_weight_portfolio_returns` computes `sum_i (1/n) r_it`, and the runner uses `R @ w` with `w = [1/3, 1/3, 1/3]` every day. That is **constant weights, i.e. rebalanced to equal weight every day**. The docstring says "fixed equal weights, no rebalancing logic", and the methods and README say "without rebalancing"; a reader will take that to mean buy-and-hold, which would let weights drift. The variance formula `w' D R D w` is correct for constant weights. Fix the text, not the code (all results use constant weights). Add one sentence on the implied turnover being ignored.

### 3.6 PSD repair in `pair_variant`
Diagnostic over every refit with data through 2019-12-31 *(computed today, `diag_psd_output.txt` in the scratchpad)*:
- 2010-start chain: 121 refits x 2 states = 242 matrices, **repair fired 0 times**; maximum change to any entry 5.6e-17 (floating point).
- 2016-start chain: 98 matrices, 0 repairs.
- The window ending 2019-12-31 (the first hold-out window): 0 repairs.
- Minimum eigenvalue of the modified matrices: 0.185 (2010 chain), 0.227 (2016 chain). The (SPY, IEF) entry is far from the PSD boundary: the admissible interval given the other entries has median about [-0.97, +0.99] (2010 chain; minimum upper bound 0.82).
- Regime-specific SPY-IEF correlations (2010 chain): calm median -0.39 (range -0.51 to -0.23), stress median -0.57 (range -0.77 to -0.43), pooled median -0.44. Neither state is positive in any refit.
- Because the repair rescales the *whole* matrix if it fires, it could alter other entries. In 2020-2025 it could plausibly matter (2022: stock-bond correlation turns positive, and a stress-state estimate near +0.8 would breach the upper bound). **Spec:** keep `nearest_corr` unchanged; add a counter of repair events per (refit, state) to the run output and record any nonzero count as a disclosed fact, not a deviation. Required code change before freeze: return the count from `run_rs_corr`.

### 3.7 Static D-vs-B size
See 2.C.4.

### 3.8 Documents
- **Master document: the `.md`.** The `.docx` and the sent PDF diverge from it (2.E). Regenerate PDF and docx from the `.md`; stop hand-editing the docx. Keep the as-sent PDFs in `docs/sent/` with hashes. Commit or delete the untracked `thesis/*.docx` and `*.pdf` per your instruction; I did not touch them.
- **README stage text** is stale (the stage paragraph says "awaiting supervisor input"; the Approved Thesis Title includes "and Risk-Controlled Allocation"; the open-decisions list still lists universe, regime count, benchmark set as open; "equal-weight ... (no rebalancing)"; the exploration paragraph says "2005-2019 is the development window").
- **`notes/` templates:** `literature_matrix.csv` is a header row only; `thesis_notebook.md` and `model_card_template.md` are empty templates; `supervisor_questions.md` contains pilot-era items; `decision_log.md` stops at 2026-09-04. No record of Prof. Seo's earlier replies or of this feedback.
- **`output/` vs `outputs/`:** still two directories; add one sentence to the reproducibility appendix.
- **`.gitignore`** ignores `output/confirm/pseudo_forecasts.pkl` (so the dry-run result has no provenance in git). The hold-out pickle is not ignored. Record its SHA-256 in the log rather than committing a large file.

### 3.9 Tests
`.venv` run with `OMP_NUM_THREADS=1`: **59 passed, 3 deselected** (15 s). The three deselected tests are `tests/test_returns.py::test_simple_returns_match_manual_calculation_on_pilot_data`, `...test_log_return_matches_manual_calculation_on_pilot_data` and `...test_equal_weight_portfolio_matches_manual_calculation_on_pilot_data`. They read `data/processed/pilot_*.csv` (2010-2025) and check the values for 2020-03-10 and 2023-11-01 *(`tests/test_returns.py:100-160`)*, so they compute on post-2019 returns. Every other test uses synthetic data (the 2020 dates in `test_date_alignment.py` are synthetic calendar dates). Consequence for disclosure: previous sessions ran all 62 tests, so those three assertions touched post-2019 returns; no values were displayed, but the preregistration's disclosure should say so. Mark the three with `@pytest.mark.holdout_data` so a pre-freeze run excludes them by default.

### 3.10 Other code and provenance findings (all worth fixing before freeze, none changes a result)
1. **Silent fallback in margin refits.** `run_rs_corr` catches any exception in `fit_margins` and keeps the old parameters with no record. Add a counter and log. The same applies to `fit_dcc` setting `a = b = 0` on a bad optimum.
2. **`freeze_tag` field.** In dry-run mode `rev-parse spec-freeze-v1^{commit}` returns the literal string (the pickle shows `'spec-freeze-v1^{commit}'`). Cosmetic; fix with a `rev-parse --verify` and `or None`.
3. **Dry-run provenance.** The pickle records `git_head f2b1fb1`, which predates the commit that added `src/explore_ladder.py` (843f0f2) *(inference: the run came from uncommitted code)*. Re-run the dry run from the clean frozen commit.
4. **Warm start.** The HMM chain starts cold at the first refit of each run and warm-starts afterwards. The hold-out chain therefore starts on a window ending 2019-12-31 with a cold HMM, unlike the exploration chain (warm since 2010). This is the "path difference" to disclose; the dry run (cold start at 2016) is the best evidence of its size (median VaR difference about 1.3e-5).
5. **Kendall arms are computed but not used.** The pickle contains `CCC_M`, `RSC_M`; the preregistration should say they are never scored.
6. **Holm families.** The primary family (four universes) is stated; the 214-test headline family uses a different Holm group. State both in the appendix.
7. **No Christoffersen conditional-coverage test and no Acerbi-Székely p-value.** `acerbi_szekely_z2` returns the statistic only; sign convention: positive means risk is underestimated (derived from `src/engine.py:243`). Add a simulation p-value in `confirm_01_score.py` (4.7). That requires the runner to save each primary arm's daily mixture parameters, since the pickle holds only VaR and ES.
8. **The conditional test needs pre-start returns.** The pickle stores `returns` from the first forecast day only, so the lagged 63-day SPY-IEF correlation (4.9, item 3) is undefined for the first 63 hold-out days unless the runner also saves the 64 returns before the start. Fix before the freeze.

### 3.11 Verified facts about the source documents
- Quantities repeated in the update and methods that I checked against files are listed at the end of 2.E.
- Pseudo-holdout (2016-2019) in the update is described as "doubles as a pseudo-holdout"; it is not independent of the development choices (specs were chosen after seeing 2010-2019 results), so it must not be presented as validation.

---

## 4. Draft confirmatory specification (Part 3)

*Near-final text for `docs/preregistration_confirmatory.md`. Items marked **DECIDE** need your decision (section 8). Everything else comes from code or logs.*

### 4.1 Hypotheses
Let `d_t = FZ0_t(RSC_P_N) - FZ0_t(CCC_S_N)` at tail level alpha = 5%, `t` = each forecast day in 2020-01-02..2025-12-31, and `mu = E[d_t]` the long-run mean of the loss difference of the two forecasting procedures (finite rolling window, Giacomini-White sense). Negative `d_t` means the regime-switching SPY-IEF model is better.
- **H0:** mu >= 0 (the model with a regime-switching SPY-IEF correlation does not have lower expected FZ0 loss than the constant-correlation model).
- **H1:** mu < 0.

### 4.2 Sidedness (recommendation: one-sided test, two-sided interval)
- **Primary decision:** one-sided at 5%: reject H0 if `t_DM < -1.6449`.
- **Reasons:** (a) the substantive question, "does letting the correlation switch help?", has one direction; (b) the size and power in the simulation (4.5%, 22.5%, 27.0%, 38.0%, 53.5%) were computed for exactly this rule, so the stated power applies; (c) a two-sided 5% test at 1,508 days has projected strong-shift power of about 29% against about 38%, and I see no reason to discard power for a direction that is not in doubt.
- **Wrong direction.** The one-sided test says nothing about harm. Pre-declare a separate rule: "significantly worse" means `t_DM > +1.96` (two-sided 5% upper tail). The simulated null upper-tail rate at 1.96 is 4.5% (at 1.645 it would be 8.0%, too high), *(computed today)*. This is a labelled secondary statement, not part of H0/H1.
- **Interval, always.** Report the two-sided 95% CI `d_bar ± 1.96 SE_HAC` and the two-sided p-value alongside the one-sided p-value, labelled.
- **Alternative (DECIDE).** Two-sided 5% as primary: cleaner to defend, about 9 points less power in the strong scenario. If you choose it, H0: mu = 0, rejection at |t| > 1.96, and the power figures to quote are the two-sided ones.

### 4.3 Models

**Common elements (code: `src/explore_routes.py::run_rs_corr`, called by `scripts/confirm_00_run.py`).**
- Assets: SPY, IEF, GLD, order (0, 1, 2); simple returns `r_t = P_t/P_{t-1} - 1` from `Adj Close`; portfolio `y_t = w' r_t` with `w = (1/3, 1/3, 1/3)` constant (daily rebalanced).
- Estimation window: the 1,260 returns before day t0; refit blocks of 21 days; margin parameters refit when `(t0 - start) % 63 == 0` (first block of the hold-out included, then every third block).
- Margins: for each asset a Gaussian-QML GARCH(1,1) with constant mean on `100 x r`, fitted with `arch` 7.2.0. Window re-filtered with the fitted parameters, initial variance equal to the window sample variance of the residuals; the one-step variance for each forecast day is updated daily from the realised residual with the fixed parameters.
- Standardised residuals `z_t = eps_t / sigma_t` over the window.
- Mean: portfolio mean `mu_P = w' mu_hat / 100` (QML constants), identical in both models and both components.
- Distribution: Gaussian (primary, "N" chain). Student-t chain is secondary.
- VaR/ES from the mixture by root-finding (`engine.mix_var_es`): VaR is the alpha-quantile of the mixture, ES the mixture tail mean, returns negative.

**CCC (baseline, `CCC_S_N`).** `R = weighted_corr(z, 1)`: the sample correlation matrix of `z` over the window with equal weights (MLE normalisation). One Gaussian component with `sigma_P,t^2 = a_t' R a_t`, `a_t = w ∘ sigma_t / 100`. No regime information is used.

**RSC_P (`RSC_P_N`).**
- State probabilities `gamma_k(s)` for s in the window: smoothed posterior probabilities of the two-state HMM fitted to the window (below).
- Regime correlation `R^(k) = weighted_corr(z, gamma_k + 1e-12)` (probability-weighted covariance of `z`, normalised to correlation).
- Component matrix `R_k = R` with the (SPY, IEF) entry replaced by `R^(k)_{01}`; every other entry stays pooled; then `nearest_corr`.
- **PSD repair:** `nearest_corr` returns the matrix unchanged if its smallest eigenvalue is at least 1e-8; otherwise it clips eigenvalues at 1e-8 and rescales to a unit diagonal, which can alter every entry. It did not fire in any of the 242 + 98 matrices through 2019 (3.6). The count of repairs over the hold-out is logged and reported.
- Forecast: two-component normal mixture. Component k has mean `mu_P` and variance `a_t' R_k a_t`. Component weights are the one-step-ahead predictive state probabilities `P(S_t = k | SPY_{1:t-1})`.

**Differences between the two models, in full:** (i) mixture over two components vs one; (ii) the (SPY, IEF) correlation entry is regime-specific vs pooled. Same margins, same `z`, same mean, same window, same refit dates.

### 4.4 Regime signal
- Two-state Gaussian HMM, `hmmlearn.GaussianHMM(2, covariance_type="diag")`, on SPY daily simple returns only, fitted on the trailing window.
- First fit: cold start, `n_iter=100`, `tol=1e-4`, startprob (0.5, 0.5), transmat [[0.98, 0.02], [0.05, 0.95]], means equal to the window mean, variances (0.5 v, 2.5 v) with v the window variance. Later fits: warm start from the previous fit, `n_iter=50`. Seed 0.
- State ordering by variance, state 0 = calm, state 1 = stress.
- Predictive probabilities for each forecast day use only SPY returns up to day t-1: the filtered probability at the window end is propagated by the transition matrix, and within a block `filtered_probs` is run with block returns up to t-1.
- Window 1,260, HMM refit every 21 days, margin refit every 63 days. The warm start chain begins cold at the first hold-out refit (3.10.4).

### 4.5 Portfolio and data
- Universe SPY/IEF/GLD, equal weights, as above.
- Raw file `data/raw/spy_ief_gld_raw_2026-09-26.csv`, SHA-256 `0ab8c7f353a7223e154cc3ee4cc3656c465dded45c19269fc24efba371150e29`; the runner uses columns `Adj Close_SPY/IEF/GLD`, truncated at 2025-12-31 before computation.
- Forecast dates: every date in 2020-01-02..2025-12-31 for which all three adjusted closes are present; **expected n = 1,508**. The run is void if the count differs.
- Missing-data rule: `dropna` over the three columns; returns are computed between consecutive available dates; no forward fill. At the time of writing no empty cell exists in the hold-out rows (textual check).
- Estimation windows use pre-2020 returns as needed (rolling).

### 4.6 Test
- **Tail level** alpha = 5% (VaR and ES). Secondary: alpha = 2.5%. This is a property of the forecast, not of the test.
- **Test significance level**: 5%, one-sided (4.2). The word "5% level" is not used alone anywhere.
- Loss: FZ0 of Patton, Ziegel and Chen (2019), `engine.fz0`: `-1{y<=VaR}(VaR - y)/(alpha ES) + VaR/ES + log(-ES) - 1`; lower is better.
- Statistic: `t = d_bar / sqrt(lrv/T)`, `lrv = gamma_0 + 2 sum_{L=1}^{7} (1 - L/8) gamma_L` (Bartlett kernel), `lags = floor(4 (T/100)^(2/9)) = 7` at T = 1,508, standard normal reference, no small-sample correction (the Harvey-Leybourne-Newbold factor is `sqrt((T-1)/T)` = 0.9997 at one step, irrelevant; the t(1507) 5% critical value is 1.6459 vs 1.6449).
- Critical value: -1.6449 one-sided; +1.96 for "significantly worse".
- Reported with it: `d_bar`, HAC SE, two-sided 95% CI, MDE (2.8016 x SE two-sided; 2.4865 x SE one-sided), SESOI comparison if declared (DECIDE).

### 4.7 Calibration (reported next to the loss, descriptive)
Hit rate and Kupiec p for both models at both tail levels; Christoffersen independence and the conditional-coverage test (add: LR_uc + LR_ind, chi-square 2); Acerbi-Székely Z2 with a simulation p-value from each model's own predictive distribution (to implement, 5,000 draws); mean ES-exceedance ratio. The calibration result does not modify the primary decision.

### 4.8 Decision rule and wording
Outcomes are exclusive, tested in this order. `d_bar` and the CI are always reported.
| Outcome | Condition | Wording (frozen) |
|---|---|---|
| O1 Significant improvement | `t <= -1.6449` | "The hold-out data provide statistical evidence at the one-sided 5% level that letting the SPY-IEF correlation switch with the regime lowers expected FZ0 loss relative to constant correlation (difference d_bar, 95% CI [a, b]). This is one test on one six-year sample containing a single stock-bond reversal; simulated power was P%." |
| O4 Significant worsening | `t >= +1.96` | "The hold-out data provide evidence that the switching specification has higher expected FZ0 loss (d_bar, 95% CI [a, b])." (no mechanism claimed) |
| O3 Bounded gain (only if SESOI declared) | not O1 or O4, and `d_bar - 1.6449 SE > -SESOI` | "The data are inconsistent, at the one-sided 5% level, with an improvement larger than SESOI = 0.002 FZ0 units. Improvements smaller than this, and any degradation, are not excluded." |
| O2 Inconclusive | otherwise | "The hold-out data neither establish an improvement nor exclude one. The estimate is d_bar (95% CI [a, b]); an improvement of at least M (the minimum detectable difference) would have been detected with 80% probability, and smaller improvements, including none, are consistent with the data." |

**No outcome is phrased as "no effect".** Hit rates, the 2022 view and all other statements are descriptive unless labelled otherwise.

### 4.9 Secondary analyses (labelled secondary, unadjusted; no p-value cited as confirmation)
1. Ladder steps on the hold-out forecasts (B/A, D/B, CCC/B, RSC/D, RSC/CCC, DCC/RSC), Gaussian chain, pooled mean, alpha 5%: estimate, SE, 95% CI, MDE.
2. 2022 calendar year (251 days): the primary difference, interval only, not tested.
3. Giacomini-White conditional test of RSC_P vs CCC with instruments {1, lagged 63-day SPY-IEF correlation of daily returns, computed from returns through t-1}, as in `explore_18_gw_conditional.py`; chi-square(2); report mean `d_t` when the lagged correlation is positive vs not.
4. alpha = 2.5% and Student-t chain (RSC_P_t vs CCC_S_t) of the primary comparison.
5. SPA with benchmark GARCH-t, candidates B, D, RSC, RSC_P (Student-t chain, pooled mean), as `explore_17_spa_mcs.py`, 2,000 bootstrap draws, seed 0 (**DECIDE**: keep or drop).
6. Hit rates and calibration tests (4.7).
Nothing else is scored. The pickle also contains Kendall-matrix arms and HS/EWMA benchmarks, which are not scored.

### 4.10 Run protocol
1. Fix all pre-freeze code (3.10), re-run tests (excluding the three data tests until the run is open), and re-run the dry run (`pseudo`) from the clean commit, then run the scorer on the pseudo pickle.
2. Write the preregistration with the SHA-256 of `raw` and of `confirm_00_run.py`/`confirm_01_score.py`; you approve.
3. Commit (when you ask) and create an annotated tag `spec-freeze-v1`. Any later change to `src/`, `scripts/confirm_*.py` or the preregistration blocks the runner by design.
4. Optional supervisor window (3 working days).
5. **You say "go".** Run `OMP_NUM_THREADS=1 .venv/bin/python scripts/confirm_00_run.py holdout` once; then `confirm_01_score.py holdout`.
6. **Valid run:** the runner finishes and writes the pickle; `git_head` equals the tag commit; n = 1,508; all VaR and ES of the primary arms are finite with `ES <= VaR < 0`. The scorer asserts these before computing anything.
7. **Crash or numerical failure** before the output is written reveals no performance information. A fix that touches only infrastructure (a path, a dependency) may be applied under a new tag `spec-freeze-v1.1`, with an entry in the log stating what failed and why it does not depend on results. A change to model numerics after any result has been seen is not allowed; if one becomes unavoidable, report both versions.
8. All deviations are recorded in `docs/decisions_log.md` with date, reason and effect.
9. Any analysis not in this list is labelled **POST HOC** in the table caption and text, and carries no inferential weight.
10. Record the SHA-256 of the output pickle and of the scoring tables in the log.

### 4.11 Disclosure (goes in the thesis and the preregistration)
- Descriptive EDA (Day-1) and the data audit displayed summary statistics for 2010-2025 before the freeze (`notes/pilot_eda.md`, `outputs/tables/supervisor_pilot_summary.csv`); three unit tests read 2010-2025 pilot returns and passed. `tests/test_returns.py` hard-codes single-day returns for 2020-03-10 and 2023-11-01, which were displayed once by accident during planning on 2026-11-03. No model was fitted or tuned on 2020-2025, but the 2022 stock-bond reversal is known to the author.
- The confirmatory test was selected from simulated power on a process in which the SPY-IEF shift is largest by construction (2.D.5).
- The dry-run path differs from the exploration path (HMM warm-start chain begins cold at the first refit and the margin-refit anchor starts at the first forecast day); median absolute VaR difference 1.3e-5 to 1.4e-5, maximum 4.2e-4, over 1,006 days *(computed today, `pseudo_forecasts.pkl` vs `U1_routes_HMM_SPY2.pkl`)*; the portfolio returns differ by at most 7.5e-7 because the two downloads differ by up to 2.49e-6.
- Same data vendor (Yahoo Finance via `yfinance`) for all ETF data.
- The static D-vs-B test is oversized under GARCH margins (2.C.4).
- HMM estimation uncertainty is not carried into the DM test (size 4.5% in simulation stands in).
- The primary hypothesis is about a procedure (window, schedule, HMM chain), not about population parameters.
- Number of specifications examined in exploration: 214 headline tests, 10 ETF universes, 10 regime definitions, plus the ladder, power and family tests in the decisions log.
- This is a self-registered, repository-based preregistration (git tag), not an independent registry entry. Optional: deposit a timestamped copy on OSF (**DECIDE**; outward-facing).

---

## 5. Workflow, calendar, risks and this week's actions (Part 4)

### 5.1 Phases

Durations are working days of effort, my estimates. "Approver" is who must say yes before the gate closes.

| # | Phase | Goal | Tasks and files | Inputs / outputs | Checks | Time | Approver | Gate |
|---|---|---|---|---|---|---|---|---|
| 1 | **Corrections and housekeeping** | Clean record before anything is frozen | Send the correction note (2.E); make the `.md` the master and regenerate PDF/docx; save as-sent PDFs to `docs/sent/` with hashes; update `README.md` (stage, title, rebalancing wording, open-decisions list); record her feedback verbatim in `notes/supervisor_feedback_2026-11.md`; add decisions entries (below); fill `notes/decision_log.md`, `thesis_notebook.md` (3 concepts), `literature_matrix.csv` | Her feedback, this plan -> corrected docs, notes | Wording sweep script passes | 1 | You | Note sent; README no longer stale |
| 2 | **Requirements** | Know format, length, deadline, title process | Email programme office/LumiNUS/module page (5.2); propose titles (5.3) | -> `notes/requirements.md` | — | 0.5 + waiting | You, programme office | Written requirements on file |
| 3 | **Pre-freeze technical work** (can overlap with 7, 8) | Everything that must exist and be tested before the tag | (a) `explore_21_power_holdout_length.py`, run in background; (b) code hygiene 3.10.1-3 and repair counter 3.6; (c) `confirm_01_score.py` + `tests/test_confirm_score.py`; (d) `confirm_02..04` scripts; (e) dry run from clean commit, score the pseudo pickle; (f) table/figure generation from the pickle, no manual steps | Pseudo pickle -> tables in `output/confirm/` | New tests on synthetic data; scorer on pseudo gives the same numbers as `explore` for overlapping rows (tolerance 1e-4); idempotent rerun | 4 to 6 | You | Dry-run scorer output reviewed |
| 4 | **Freeze** | Specification fixed | Write `docs/preregistration_confirmatory.md` from section 4; add the log entries; your approval; optional supervisor review (3 days); commit (only when you ask); annotated tag `spec-freeze-v1` | -> tagged commit | `git status` clean for frozen paths; `check_freeze` dry call | 1 to 2 | **You** (and optionally her) | Tag exists. **Stop and ask you.** |
| 5 | **Hold-out** | One run, frozen scoring | Pre-run checklist (5.5); run once; score; record hashes | Tagged commit -> `output/confirm/holdout_forecasts.pkl`, tables | Valid-run test (4.10) | 0.5 | **You, explicit go** | Scored tables saved, hashes logged |
| 6 | **Interpretation** | Apply pre-written wording | Select outcome O1-O4; fill the template; secondary analyses; label anything extra POST HOC | -> results text | Wording sweep | 1 | You | Chapter 7 drafted |
| 7 | **Literature review** | Chapter 2, citations verified | See 6.3; fill `literature_matrix.csv`; read primary sources via NUS library | -> chapter, bib | Citation audit table | 4 to 5 | You, supervisor | All cited works at least bibliographically verified; claims sourced |
| 8 | **Writing** (methods first) | Draft | Order: methods (chapter 4) -> data (3) -> evaluation (5) -> exploration/ladder results (6) *before phase 5 opens* -> literature (2) -> intro (1) -> hold-out result (7) -> discussion/limitations (8) -> conclusion (9) -> abstract | -> drafts | Claims-to-exhibits map; sweeps | 10 to 12 | You | Full draft |
| 9 | **Reproducibility and final checks** | One-command rebuild | `Makefile` or `scripts/build_all.py` that rebuilds all tables/figures from saved pickles; a script that checks every number in the thesis against a result file (a `numbers.yaml` with file and column per quoted number); citation check; wording sweep; `pytest` | -> package | All pass | 2 to 3 | You | Clean rebuild on a fresh clone |
| 10 | **Submission** | Review and submit | Supervisor review rounds (1 to 2, about a week each); fixes; format to requirements; buffer | -> final | Checklist | 5 to 7 + buffer | Supervisor, you | Submitted |

Dependencies: 3 -> 4 -> 5 -> 6 -> 8(ch.7) -> 9 -> 10. Parallel to 3-4: 1, 2, 7, 8 (methods, data, evaluation, exploration results). Waiting items: 2 (programme office), 4 (supervisor window).

**Log entries to propose** (to be written in `docs/decisions_log.md` after your approval): (1) supervisor feedback and decisions; (2) correction of sent documents; (3) the confirmatory specification; (4) power study at 1,508 days (500 reps, scenarios, two- and one-sided reporting, rule for low power); (5) SESOI (or the decision to declare none); (6) the secondary list and their labelling; (7) wording rules; (8) code hygiene changes pre-freeze; (9) the three data tests excluded from pre-freeze runs.

### 5.2 Requirements (what I found and could not find)
- **Found.** The DSE major requires at least one of DSE4288, any UPIP course, or any NOC internship course; DSE4288 appears in the AY2024/25-onwards requirements, while the AY2021/22 requirements list DSE4101/DSE4201 as Capstone I/II ([DSE requirements AY24/25-25/26](https://www.math.nus.edu.sg/wp-content/uploads/sites/4/2026/07/DSE_2425_2526_06072026.pdf), [AY21/22 and after](https://www.stat.nus.edu.sg/wp-content/uploads/sites/8/2024/06/120624-Major-Data-Science-and-Economics-Programme-Requirements-AY21-22-and-after.pdf)). The Economics department's EC4401 page states that the Economics honours thesis is no longer compulsory for Highest Distinction and is 8 units for cohort 2021 onwards ([FASS](https://fass.nus.edu.sg/ecs/economics-honours-thesis-independent-study-course)); search summaries differ on the unit count and I could not open the page (my fetch returned empty). The statistics department describes separate single-semester 8-unit honours project courses ([ST/DSA honours project](https://www.stat.nus.edu.sg/honours-project-fyp/)).
- **Semester dates (secondary, unconfirmed).** AY2026/27 Semester 1: exams 21 Nov to 5 Dec 2026, reading week 14 to 20 Nov, from a Law school and a B.Tech calendar ([Law](https://law.nus.edu.sg/ay2026-27-law-weekly-calendar-sem-1-acad-ver-20-july-2026/), [B.Tech](https://scale.nus.edu.sg/docs/default-source/btech-engineering/acadcalendar_btech-bit-spc_ay2026-27.pdf)). The official registrar calendar PDF was returned but not read for Semester 1.
- **Not confirmed.** Which course governs your thesis (repo name `DSE4201-Project`, your description "honours thesis"); word or page limit; format and referencing style; submission deadline and portal; whether a viva or presentation is required; title-change procedure; plagiarism/AI-use declaration requirements.
- **What to ask.** (1) The module code and the LumiNUS or handbook page for it; (2) the submission deadline and mode; (3) any length limit and whether appendices count; (4) citation style; (5) how to register a title change; (6) whether there is a viva/presentation date.

### 5.3 Narrowed titles (without the allocation clause)
1. *Regime-Switching Risk Models for ETF Portfolios: Do Market-State Shifts Improve Tail-Risk Forecasting?* (minimal change from the approved title)
2. *Where Does Regime Information Help? A Detectability-Aware Decomposition of Regime-Switching Tail-Risk Forecasts for an ETF Portfolio*
3. *Regime-Switching Volatility and Correlation in Tail-Risk Forecasting for ETF Portfolios: Evidence and Detectability*
Recommendation: 1 if title changes need paperwork (smallest change), 2 if you want the title to match the argument.

### 5.4 Proposed milestones with the supervisor (to confirm with her)
All dates relative to the real deadline D (which I do not have):
- **D-6 weeks:** correction note and this plan's summary sent; ask for milestones.
- **D-5.5 weeks:** frozen preregistration sent (3-day window).
- **D-5 weeks:** hold-out run and result summary (one page: result table, wording of the outcome, caveats).
- **D-4 weeks:** methods + data + evaluation + exploration results chapters (draft 1).
- **D-3 weeks:** literature + hold-out results chapters.
- **D-2 weeks:** full draft to supervisor.
- **D-1 week:** revised draft; final formatting.
- **D:** submit.
Form of updates: a one-page email, with the "what changed since last update", "what I need" list, not a long document.

### 5.5 Checklists
**Just before the hold-out run (all must be yes):**
1. Tag `spec-freeze-v1` exists and points at the commit you approved; `git status` is clean for `src/`, `scripts/confirm_*.py`, the preregistration.
2. The preregistration's SHA-256 values match `shasum -a 256` of the raw file and the two scripts.
3. Dry-run output and scorer on the pseudo pickle exist and are archived with hashes.
4. `pytest` passes without the data tests; the three data tests are not to be run yet.
5. Power at 1,508 days is finished, its numbers are in the preregistration.
6. `output/confirm/holdout_forecasts.pkl` does not exist.
7. You have said "go" in this session or in writing.
8. Disk space and power are fine; `OMP_NUM_THREADS=1`.

**Just after:**
1. The runner printed "holdout: 1508 forecast days 2020-01-02..2025-12-31".
2. Record SHA-256 of the pickle; copy it to a read-only location.
3. Run the scorer once; it asserts validity first (4.10.6).
4. Save tables and figures under `output/confirm/`; do not edit them by hand.
5. Log the result, the outcome label (O1-O4), repair-event and fallback counts.
6. Only then run the three data tests (`pytest -m holdout_data`) and the full `pytest`.
7. Anything else you want to look at is POST HOC and labelled.

### 5.6 Calendar (deadline unknown)
Two worked examples; replace with the real date.
| Phase | If deadline is 30 Nov 2026 (about 4 weeks, only if Semester 1 governs) | If deadline is 23 Apr 2027 |
|---|---|---|
| 1, 2 | 3-4 Nov | 4-6 Nov |
| 3 | 4-11 Nov (power run overnight 4 Nov) | 9-20 Nov |
| 4 | 12-13 Nov | 23-25 Nov |
| 5, 6 | 16-17 Nov | 30 Nov - 2 Dec |
| 7, 8 | 4-23 Nov in parallel | Nov-Feb in parallel; draft to supervisor mid-Feb |
| 9 | 24-25 Nov | Mar |
| 10 | 26-30 Nov (no supervisor round; one if she can turn it in 3 days) | Mar-Apr, buffer 2 weeks |
The first column leaves no buffer. If your deadline is that early, drop SPA from the secondary list and write less appendix, and tell me; I would then also not send the specification to the supervisor for a window.

### 5.7 Top risks
| Risk | Likelihood / impact | Mitigation |
|---|---|---|
| Deadline earlier than expected | Unknown / severe | Get the date this week; use the compressed column above |
| Hold-out inconclusive (very likely given 20-40% projected power) | High / medium | The thesis is framed around detectability; outcome O2 text is pre-written; report power prominently |
| A bug is found after the run | Low-medium / high | Dry run from clean commit; scorer tested on synthetic data; if a bug is found, report both versions and log it |
| Numerical failure in the run (HMM, GARCH) | Low / medium | Counters and assertions; rule 4.10.7 |
| Examiner objects to single-pair choice by simulated power | Medium / medium | Disclosure text (2.D.5); the pair was fixed by theory |
| Examiner objects to self-registered preregistration | Low / low | State it plainly; optional OSF timestamp |
| Citation errors (including ones in repo docs) | Medium / high | Citation audit 6.3; no citation enters the thesis unverified |
| Scope creep (new models, universes, signals) | Medium / medium | "Future work" list; supervisor said no |
| 2022 SE inflation widens the CI beyond expectations | Medium / low | Report as is |
| Supervisor does not reply to milestones | Medium / low | Propose and proceed |

### 5.8 Next five actions this week
1. **Tell me the deadline and ask the programme office the six questions in 5.2.**
2. **Decide D1-D5 in section 8** (sidedness, SESOI, send-spec, replications, master document).
3. **Send the correction note (2.E)** after you check it, with corrected PDFs generated from the `.md`.
4. **Start the 1,508-day power simulation in the background** once you approve `explore_21` (I write it; about 1 to 2 hours of compute).
5. **Start writing the methods chapter** from the corrected `.md` (2.A.3 replacements), and record her feedback in `notes/`.

---

## 6. Thesis structure and literature (Part 5)

### 6.1 Chapter outline
Target lengths assume about 12,000 words excluding appendices **[assumption; replace once the official limit is known]**; the percentages carry over.

| Ch. | Title | Purpose | Contents | Key exhibit | Share |
|---|---|---|---|---|---|
| 1 | Introduction | Question, argument, contribution | Motivation (stock-bond correlation reversal), research question, summary of design and findings, contribution paragraph, outline | none | 7% |
| 2 | Literature and positioning | Place the thesis against the closest work | 6.3 themes | Table: study, model, evaluation, finding, how this thesis differs | 15% |
| 3 | Data and sample design | Data, split, disclosure | ETFs, funds, returns, hashes, development/pseudo/hold-out, what was seen before the freeze | Sample-split timeline | 8% |
| 4 | Methodology | Models and what each comparison isolates | HMM, static models, GARCH-margin models, benchmarks, mean treatment, t chain; the per-step "what differs" table (2.A.1) | The table of 2.A.1 | 17% |
| 5 | Evaluation and inference | Loss, tests, power, reporting rules | FZ0, DM/GW reading, HAC, calibration tests, MDE, size and power study design, multiple testing | Power table | 11% |
| 6 | Results: exploration and ladder | What the pre-2020 data show | Ladder table and forest plot, calibration, controls, power results, summary of the 214 tests | Forest plot | 17% |
| 7 | Results: hold-out | The frozen test | Preregistered result with CI, MDE, power; secondary results labelled; calibration | Result table | 8% |
| 8 | Discussion and limitations | Interpretation and honesty | What each result does and does not show; limitations list (equity-only signal, single portfolio, same vendor, HMM uncertainty, DGP assumptions, one episode); future work (macro state, other pairs, other vendors, allocation) | none | 11% |
| 9 | Conclusion | Answer | 1 page | none | 3% |
| App. | A. Specification log (pointer to `decisions_log.md`); B. Exploration grid; C. Controls and sub-periods; D. Preregistration text; E. Reproducibility; F. Code listing pointers | | | | outside count |

Research question: ch. 1; data: ch. 3; methodology: ch. 4; evaluation: ch. 5; results: ch. 6-7; discussion, limitations: ch. 8; conclusion: ch. 9; appendices: A-F.

### 6.2 Existing citations and their status

Status key: **B** = bibliographic record matched to a registry (Crossref/EconPapers) in this session; **A** = abstract content seen in this session (search or fetch summary, not full text); **U** = **[UNVERIFIED]**. "Journal details from memory" means Crossref returned a working-paper or reprint record.

| Citation | Used for | Status | Note / action |
|---|---|---|---|
| Ardia, Bluteau, Boudt, Catania (2018), IJF 34(4), 733-747 | Regime vs single-regime GARCH risk forecasts | B + A | **The repo's characterisations conflict with the abstract.** The abstract says MSGARCH models yield more accurate VaR, ES and left-tail forecasts than single-regime counterparts (daily, weekly, ten-day equity returns). `output/literature_positioning.md` says the finding is that regime-switching "does not uniformly dominate", and the update says "regime gains are larger against simple baselines". The second claim I could not find in the abstract: **[UNVERIFIED]**. Read the full text before using either. |
| Santos, Nogales, Ruiz (2013), JFEC 11(2), 400-441 | Multivariate vs univariate VaR | B + A | Abstract: multivariate beat univariate out of sample; DCC with Student-t best. "Constant-correlation multivariate usually worse than univariate": **U**. |
| Fortin, Simonato, Dionne (2023), IJF 39(1), 314-331 | Univariate vs multivariate ES | B + A | Abstract: mostly no significant difference, one-week ES, factor portfolios. Whether they use joint VaR/ES scoring: **U**. |
| Paolella, Polak, Walker (2019), J Econometrics 213(2), 493-515 | Closest regime-correlation work | B | Content in the briefing (accuracy, capital) **U**; "does not separately test volatility vs correlation" **U**. |
| Pelletier (2006), J Econometrics 131(1-2), 445-473 | Regime switching for dynamic correlations | B | Content **U** (my search returned nothing on it); also my "Pelletier-style" model description. |
| Giacomini & White (2006), Econometrica 74(6), 1545-1578 | Conditional predictive ability | B + A | Nested/non-nested claim and rolling-window null: partial abstract only. |
| Diebold & Mariano (1995), JBES 13(3), 253-263 | DM test | B (NBER record) | Journal details from memory |
| Harvey, Leybourne, Newbold (1997), IJF 13(2), 281-291 | Small-sample DM correction | B | — |
| Newey & West (1994), REStud 61(4), 631-653 | Lag selection | B (NBER record) | Journal details from memory |
| Clark & McCracken (2001), J Econometrics 105(1), 85-110 | Nested model tests | B + A | — |
| Clark & West (2007), J Econometrics 138(1), 291-311 | MSPE-adjusted | B + A | — |
| McCracken (2020), Econometrica 88(4), 1753-1754 | Diverging tests | B + A | Counterexample details **U** |
| Zhu & Timmermann (2020), arXiv 2006.03238 | Critique of GW null | A (search only) | Check |
| West (1996), Econometrica 64(5), 1067-1084 | Estimation uncertainty in OOS tests | B | — |
| Fissler & Ziegel (2016), Ann Stat 44(4), 1680-1707 | Joint elicitability | B | — |
| Patton, Ziegel, Chen (2019), J Econometrics 211(2), 388-413 | FZ0 loss | B (SSRN record only) | Journal details from memory |
| Nolde & Ziegel (2017), Ann Appl Stat 11(4), 1833-1874 | Elicitability and backtesting | B | not yet cited |
| Holm (1979), Scand J Stat 6(2), 65-70 | Holm procedure | **U** (registry returned a later correction) | From memory; check |
| Hansen (2005), JBES 23(4), 365-380 | SPA | B (SSRN record) | Journal details from memory |
| Hansen, Lunde, Nason (2011), Econometrica 79(2), 453-497 | MCS | B (SSRN record) | Journal details from memory |
| Kupiec (1995), J Derivatives 3(2), 73-84 | Unconditional coverage | B | — |
| Christoffersen (1998), IER 39(4), 841-862 | Independence/conditional coverage | B | — |
| Acerbi & Székely (2014), Risk 27(11), 76-81 | ES backtest Z2 | **U** (not found) | Sign convention and critical values (the -0.70 figure) unconfirmed; a search found 0.7 and 1.8 as thresholds in another paper's convention |
| Lakens (2017), Soc Psychol Pers Sci 8(4), 355-362 | Equivalence tests | B (preprint record) | Journal details from memory |
| Hoenig & Heisey (2001), Am Stat 55(1), 19-24 | Observed power | B | — |
| Nosek et al. (2018), PNAS 115(11), 2600-2606 | Preregistration | B (preprint record) | Journal details from memory |
| Engle (2002), JBES 20(3), 339-350 | DCC | B (NBER working paper record: Engle & Sheppard 2001) | Journal details from memory |
| Bollerslev (1990), REStat 72(3), 498-505 | CCC | B (reprint chapter record) | Journal details from memory |
| Hamilton (1989), Econometrica 57(2), 357-384 | Markov switching | B | — |
| Ang & Bekaert (2002), RFS 15(4), 1137-1187 | Regime shifts and allocation | B | — |
| Forbes & Rigobon (2002), J Finance 57(5), 2223-2261 | Correlation vs volatility | B (NBER 1999 record) | Journal details from memory; `decisions_log.md` says it was not re-verified |
| Engle & Colacito (2006), JBES 24(2), 238-253 | Economic value of correlation timing | B | — |
| Pouliasis & Papapostolou (2018), J Futures Markets 38(11), 1407-1439 | Volatility and correlation timing | B | The briefing cites "Pouliasis (2018)"; add the second author |
| Chua, Kritzman, Page (2009), JPM 36(1), 26-35 | Crisis correlation | B | — |
| Kole, Markwat, Opschoor, van Dijk (2017) | Aggregation | B (SSRN 2016 record) | Published venue **U** |
| Brooks & Persand (2003), J Forecasting 22(1), 1-22; McAleer & da Veiga (2008), J Forecasting 27(3), 217-235 | "No clear preference" | B | The characterisation in the briefing is **U** |
| Kinlaw et al. (2021) | Conditional correlations | **U** (no registry match) | Check SSRN 3781844 |
| Itou & Yoshiba (2025) | Tail dependence and ES | **U** (no match) | Check or drop |
| Baele, Bekaert, Inghelbrecht (2010); Campbell, Pflueger, Viceira (2020); Campbell, Sunderam, Viceira (2017); Connolly, Stivers, Sun (2005) | Drivers of stock-bond correlation (theme 4) | B for the first three (NBER records), **U** for Connolly et al. | Not yet in the repo; propose for chapter 2, journal details from memory |
| Abadie (2020), AER: Insights 2(2), 193-208; Altman & Bland (1995), BMJ 311, 485; Ioannidis, Stanley, Doucouliagos (2017), EJ 127, F236-F265 | Negative results and power | B | Newly proposed |

Each "B" is a registry match for the title, authors, venue and year; the **content** characterisations are what need full-text reading. Process: NUS library access -> read the abstract, data and main table of each cited work -> fill one row of `notes/literature_matrix.csv` (header exists) -> only then cite.

**Claims without a source in the repo.**
- "That regime gains are larger against simple baselines is already known (Ardia et al. 2018)" (update §5).
- "The stock-bond correlation sign is a slow macro state" (limitations): needs Baele et al. / Campbell et al. or removal.
- "Same-vendor limitation" is fine, but the "two downloads agree" fact had no result file.
- "2022 was the first year since 1977 that both equities and bonds fell" (briefing): from secondary web commentary; do not use without primary data.
- "The unusual stock-bond positive era 1987-1999" is from fund proxies, result file `longhistory_summary.json`.

### 6.3 Literature review plan (themes, in the order of the argument)
1. **Regime-switching volatility and risk forecasting** (Hamilton 1989; Ang & Bekaert 2002; Ardia et al. 2018): what regime models are expected to give. Check what Ardia et al. actually conclude about the baseline.
2. **Gains relative to baseline complexity**: single-regime GARCH is a strong benchmark; regime benefit depends on the benchmark. Source after the full-text read.
3. **Correlation modelling and multivariate vs univariate VaR/ES** (Bollerslev 1990; Engle 2002; Pelletier 2006; Santos et al. 2013; Fortin et al. 2023; Paolella et al. 2019; Kole et al. 2017): the unsettled question.
4. **Stock-bond correlation sign and drivers** (Baele et al.; Campbell et al.; Connolly et al.): why the correlation channel is motivated and why a fast volatility regime may be the wrong tool.
5. **Forecast evaluation and elicitability** (Fissler & Ziegel 2016; Patton et al. 2019; Nolde & Ziegel 2017; Kupiec; Christoffersen; Acerbi & Székely) and **testing predictive ability** (DM, HLN, West, GW, Clark-McCracken, Clark-West, McCracken, Hansen SPA/MCS).
6. **Negative results, power and preregistration** (Hoenig & Heisey; Lakens; Abadie; Altman & Bland; Ioannidis et al.; Nosek et al.).

### 6.4 Contribution paragraph
This thesis provides a decomposition of tail-risk forecast gains from regime information into regime-dependent volatility, a GARCH-margin model class, and regime-dependent correlation, using comparisons that share data, regime signal and estimation window but are only partly nested, and it reports for every comparison the estimate, a confidence interval and the minimum detectable difference, supported by a simulation study of size and power and by one pre-specified out-of-sample test of a regime-switching stock-bond correlation on 2020-2025. The closest existing work is Paolella, Polak and Walker (2019) and Pelletier (2006), who model regime-switching correlation, and Ardia et al. (2018), who compare regime-switching and single-regime GARCH for risk forecasts; the thesis differs by separating the volatility and correlation treatments under a shared regime signal, and by making detectability explicit. A search of the literature did not reveal a study that does exactly this, but I did not verify that none exists (**[UNVERIFIED]**: novelty is not established). The thesis does not claim a better model, and where comparisons are not nested it claims only a comparison between model classes.

---

## 7. Methods check (Part 6)

Ranked by whether an examiner would care. "Gap" = difference from accepted practice; "Fix?" = recommendation given the instruction not to widen scope.

| Rank | Method | Accepted practice | Implementation | Gap | Fix? |
|---|---|---|---|---|---|
| 1 | **DM vs GW, nested and non-nested** (Diebold & Mariano 1995; Giacomini & White 2006; Clark & McCracken 2001; West 1996) | Match the null to the design; for nested models and expanding windows, nonstandard limits (Clark-McCracken) and adjusted tests (Clark-West) | Rolling fixed window, DM statistic with normal reference | The thesis called the ladder "nested" and cited no theory | Wording (2.A.4) plus simulation size. No new test. **Examiner-critical.** |
| 2 | **Size under the actual process** | Show size in simulation | Done: S0 rows | D-vs-B 11.0% not reported | Report (2.C.4). Free. |
| 3 | **Sidedness and the MDE multiplier** | State once, use consistently | Mixed (3.4) | Inconsistent labelling | Labelling and both multipliers (3.4). Free. |
| 4 | **Preregistration** (Nosek et al. 2018) | Hypothesis, test, rule, sample, analysis plan, timestamp before data | Git tag and file | Self-registered; no independent timestamp | Optional OSF deposit (D10). |
| 5 | **HAC variance** (Newey & West 1994) | Bartlett kernel; lag from a rule or a data-driven selector | `floor(4 (T/100)^(2/9))` | Described as "automatic selection" | Wording. Optional sensitivity: not added (no new robustness checks). |
| 6 | **Harvey-Leybourne-Newbold 1997** | Small-sample correction and t reference, mainly for multi-step | None | Irrelevant at one step and T = 1,508 (factor 0.9997) | State and move on. |
| 7 | **Elicitable joint score** (Fissler & Ziegel 2016; Patton et al. 2019) | FZ0 or FZG for (VaR, ES) | `engine.fz0` | None. Note FZ0 requires negative ES and is unit-free in scale | None. |
| 8 | **Backtests** (Kupiec 1995; Christoffersen 1998; Acerbi & Székely 2014) | Unconditional and conditional coverage; ES test with simulated critical values | Kupiec, independence only, Z2 as a raw statistic | No conditional-coverage joint test; no Z2 p-value | Close both in `confirm_01_score.py` (cheap). |
| 9 | **Equivalence / smallest effect** (Lakens 2017) | Declare SESOI in advance; TOST | None | Not done | 2.B.3: declare or deliberately omit. |
| 10 | **Observed power** (Hoenig & Heisey 2001) | Do not report | Not reported | Update's "well-powered null" wording | Wording rule. |
| 11 | **Multiple testing** (Holm 1979; Hansen 2005; Hansen, Lunde, Nason 2011) | Control the family declared in advance; SPA/MCS for model sets | Holm on the declared primary family; SPA/MCS for model sets | Holm is invalid for the anti-conservative static tests | Disclose (2.C.4). |
| 12 | **Regime estimation uncertainty** | Bootstrap the full pipeline or report as a limitation | Limitation + null-scenario size | No pipeline bootstrap | Keep as limitation; do not build. |
| 13 | **Distribution** | Student-t margins/innovations common for ES | N primary; t secondary; df ML from standardised returns | df estimators differ across arm families (2.A.1) | Mention in methods. |
| 14 | **Data** | Two vendors, split/dividend audit | One vendor; audit done in WP0 | Same-vendor | Limitation (she agreed). |

---

## 8. Decisions I need from you

| # | Decision | My recommendation | If you choose otherwise |
|---|---|---|---|
| D1 | Sidedness of the primary test | One-sided 5% (reject at t < -1.645); "worse" at t > +1.96; two-sided CI reported | Two-sided 5%: cleaner for an examiner, about 9 points less simulated power (about 29% vs 38% projected in the strong scenario); quote two-sided power |
| D2 | Smallest effect of interest | Declare SESOI = 0.002 FZ0 as a one-sided bound (O3), state that it is unlikely to be reached | None declared: drop O3; fewer ways to over-interpret, simpler. Neither is dishonest. |
| D3 | Send the frozen spec to Prof. Seo before the run | Yes, with a 3-working-day window and "will proceed on day 4" | No: faster, but she asked for the specification and you lose a pre-run objection opportunity |
| D4 | Replications for the 1,508-day power study | 500 per scenario, about 1-2 hours | 200: matches before, less precise (SE 3.5 pts); 1,000: double the time, little gain |
| D5 | Reversal of RSC_P vs RSC power ranking | Do not change the test | Switching after a second look = second selection on the same DGP; if you want to keep the option open, pre-declare a rule now |
| D6 | Master document | `.md`; regenerate PDF/docx; archive as-sent versions | Docx as master: edits are not diffable and errors like E1 recur |
| D7 | Title | Option 1 (smallest change) unless the school lets you choose freely | Option 2 matches the argument better but needs more paperwork |
| D8 | Portfolio wording | Fix text to "constant weights, rebalanced daily" | Changing the code to buy-and-hold would invalidate all results |
| D9 | MDE convention | Keep 2.8016 x SE (two-sided) everywhere; add 2.4865 x SE for the primary only | Switching everything to one-sided would require re-labelling all tables |
| D10 | OSF deposit of the frozen specification | Optional: yes if you are comfortable (it is public and cached; confirm first) | Skip: git tag only; disclose as self-registered |
| D11 | Keep SPA vs GARCH-t among the secondary analyses | Keep (already declared, cheap) | Drop to cut the list to five; move to appendix as exploration only |
| D12 | Re-run the dry run from the clean frozen commit | Yes | Skipping leaves the dry-run provenance mismatch (3.10.3) |
| D13 | Write exploration/ladder results before the hold-out opens | Yes | After: the framing could be shaped by the hold-out |
| D14 | Deadline and scenario | Tell me the date | Plan assumes nothing |

## 9. Questions to send the supervisor (short)

1. I found errors in the two documents I sent (details in the attached note, corrected PDFs attached). Do you want anything else corrected?
2. For the confirmatory test I propose a **one-sided** 5% test (H1: regime-switching SPY-IEF correlation lowers expected FZ0), with a two-sided 95% CI reported alongside and a separate "worse" rule at the two-sided 5% level. Do you prefer a two-sided test?
3. May I send you the frozen specification for a 3-working-day look before I run it?
4. Do you agree to keep a short list of secondary analyses (the 2022 episode, the conditional test, ladder steps at hold-out, alpha 2.5%, SPA), unadjusted and labelled secondary? They use the same forecasts and add no models.
5. Which milestones and update form would you like (my proposal: 5.4)?
6. Do you know the module-specific length and format requirements, the submission deadline, and the process for a title change? (I could not find them online.)
7. Is a title such as "Regime-Switching Risk Models for ETF Portfolios: Do Market-State Shifts Improve Tail-Risk Forecasting?" acceptable?
