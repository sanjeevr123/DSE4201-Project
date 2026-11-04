# Thesis Progress Recap and Direction Options

**Regime-Switching Risk Models for ETF Portfolios.** Snapshot of the repository as of 2026-10-27 (last commit 2026-10-13).

**How this was made.** I read every prose file, the config, the result tables and the code layout, re-ran the test suite (54 pass), and checked the headline numbers against the result files where I could. I did not run any model, and nothing after 2019-12-31 was touched. Items marked *(my suggestion)* are my own ideas, not results or verified literature.

---

## 1. One-page summary

**Where you are.** The pilot is finished and passed all six pre-registered criteria. An exploration phase (data through 2019 only) followed, as the supervisor asked, and a GARCH-margin follow-up on 13 Oct. Nothing has been committed since then, and no thesis draft exists in the repo. The 2020-2025 hold-out has not been used by any model.

**The single most important result.** Across 10 ETF universes, 10 regime definitions and a 28-year stock/bond sample, letting correlations switch by regime gave no detectable forecasting gain over letting only volatilities switch (0 of 214 tests survive Holm correction). The test is also weak: the smallest detectable loss difference (about 0.009) is three times the typical observed difference (about 0.003). So the honest status is "no evidence for, and cannot rule out".

**The most interesting new finding.** Regime models appeared to lose to GARCH-t and DCC-t, but most of that gap disappears once the regime model gets GARCH volatility inside each regime (loss improves by 0.026 to 0.073 in all four universes checked; Holm-significant in one). The "regime models lose" story is largely a design confound. This is the strongest candidate for a real contribution.

**The biggest risks.**
1. Time. The pilot prompt (26 Sep) said "5 weeks left". If that clock is still current, it is nearly out. Your deadline decides which options in Section 9 are feasible.
2. The motivating episode (2022 stock-bond correlation flip) is a single event in the held-out data, so even the confirmatory test has limited power.
3. Many tests (214+) on overlapping samples. Only the pre-declared Holm families should be quoted as evidence.
4. No record of Prof. Seo's reaction to the supervisor brief. The decisions in Section 8 are still open.

---

## 2. Timeline (from git)

| Date | Milestone |
|---|---|
| 23 Aug | Repo set up; decision log started; question and ETF pilot (SPY/IEF/GLD) provisional |
| 4 Sep | Day-1 EDA pipeline: returns, rolling vol, ACF (`scripts/01-03`, `outputs/`) |
| 26 Sep | Starter code, literature briefing and pilot prompt added; WP0 (data, audit, engine) and WP1 (tests) done |
| 26-27 Sep | WP2 power study (2,800 replications, 40 min), WP3 real data 2010-2015, WP4 reproducibility, WP5 literature; **PILOT_REPORT: PROCEED** |
| 27 Sep | Housekeeping: README, supervisor questions |
| 11-12 Oct | Exploration: universe screen, regime definitions, long-history check, 214-test backtest grid, study guide, supervisor brief |
| 13 Oct | GARCH-margin arm, Route M / Route P, power study for routes, research document, confound check on U3/U8/U10 |
| 13-27 Oct | No commits |

---

## 3. The research design in one page

- **Question.** Does a real-time regime model improve one-day-ahead VaR/ES for a fixed equal-weight portfolio, and specifically does the *correlation* channel add anything beyond the *volatility* channel? In plain terms: when losses grow, is it assets getting more volatile, or diversification breaking down?
- **Regimes.** One 2-state Gaussian HMM on SPY returns, filtered probabilities only (no look-ahead). State 0 is calm.
- **Four covariance variants sharing the same regime probabilities.** A pooled; B regime vols, pooled correlation; C pooled vols, regime correlation; D both switch. Forecast is a 2-component normal mixture; VaR by root-finding, ES in closed form.
- **Primary contrast.** D vs B.
- **Estimation.** Rolling 1260-day window, refit every 21 days (GARCH every 63).
- **Benchmarks.** Historical simulation, EWMA, GARCH-t, and (added in exploration) DCC-N and DCC-t.
- **Scoring.** FZ0 joint VaR/ES loss (lower is better), Diebold-Mariano tests with HAC errors, Kupiec and Christoffersen backtests, Acerbi-Szekely ES test. Levels 5% (primary) and 2.5%.
- **Data rules.** Raw data downloaded once, SHA-256 in `data/raw/MANIFEST.txt`. Pilot lock was 2016+; exploration moved the line to 2020+ with 2016-2019 as a pseudo-holdout (documented in the preregistration addendum).
- **Layers added in exploration.** *Layer 1* is the original static-covariance design. *Layer 2* uses GARCH(1,1) margins with constant (CCC) or regime-switching (RSC) correlation of the standardised residuals. *Route M* builds correlations with a Kendall's-tau matrix. *Route P* lets only the SPY-IEF pair switch.

---

## 4. Repository map

| Area | Files | Status |
|---|---|---|
| Question and rules | `README.md`, `docs/PILOT_PROMPT.md`, `docs/preregistration.md`, `docs/decisions_log.md` | Done; README stage text is current |
| Day-1 EDA (separate pipeline) | `scripts/01-03`, `notes/pilot_eda.md`, `notebooks/`, `outputs/` (plural) | Done. Covers 2010-2025 (see Section 7) |
| Pilot | `config/pilot.yaml`, `src/engine.py`, `scripts/00,wp2,wp3,wp4`, `output/tables/`, `output/figures/`, `output/PILOT_REPORT.md/.pdf` | Done, reproducible |
| Exploration | `src/explore*.py`, `scripts/explore_00..12`, `output/explore/` | Done through 2019 |
| Tests | `tests/` (11 files) | 54 pass today (41 at pilot time) |
| Reading and writing aids | `output/STUDY_GUIDE`, `SUPERVISOR_BRIEF`, `FURTHER_EXPLORATION_RESEARCH.md`, `literature_positioning.md`, `docs/literature_briefing.md` | Done |
| Personal notes | `notes/thesis_notebook.md`, `literature_matrix.csv`, `model_card_template.md`, `supervisor_questions.md` (top two sections) | **Empty templates** |
| Historical | `starter/` (prototype, superseded by `src/engine.py`) | Keep for reference |
| Thesis draft | none | **Not started** |

Run order for exploration is in the README table (steps 0 to 11, plus `explore_12_score_confound.py`). Use `--validate` first and `OMP_NUM_THREADS=1` for parallel runs.

---

## 5. Results so far

### 5.1 Pilot (SPY/IEF/GLD)

**Go/no-go scorecard** (`docs/preregistration.md`, `output/PILOT_REPORT.md`):

| Criterion | Verdict | Evidence | Margin |
|---|---|---|---|
| G1 correctness | Pass | 41/41 tests then; 54 now | Clear |
| G2 test size | Pass | S0 false positives 5.0% (stylised), 2.0% (calibrated) | Clear |
| G3 detectability | Pass on primary DGP | S2 power 52.5%; calibrated DGP only 42.0% | **Marginal** |
| G4 regime stability | Pass | 65/72 refits = 90.3% vs 90% bar | **Marginal (0.3 pts)** |
| G5 reproducibility | Pass | Identical on rerun; different seed within tolerance | Single machine |
| G6 feasibility | Pass | ~26 s measured, ~43 s extrapolated | Clear |

**Power of the D-vs-B test** (one-sided DM, 5%, 10 years, 200 reps):

| Scenario | Stylised DGP | Calibrated DGP |
|---|---|---|
| S0 vol-only (size) | 5.0% | 2.0% |
| S1 moderate breakdown | 25.5% | 16.5% |
| S2 strong breakdown | 52.5% | 42.0% |
| S3 flight to quality | 3.5% | 9.5% |

Moderate-shift power grows slowly with data: 19.5% at 5 years, 25.5% at 10, 30.0% at 15.

**Real data 2010-2015** (`output/tables/wp3_*.json`):
- Stress state 18.3% of days; expected stress duration 32 days.
- SPY-IEF correlation moves from -0.33 (calm) to -0.51 (stress): bonds hedge *more* in stress. Shapley share of the vol increase: volatility 113%, correlation -13%.
- Walk-forward FZ0 at 5%: GARCH-t -4.4537 best, D -4.4423, B -4.4397, EWMA -4.4245, HS -4.4129, A -4.4058, C -4.3840. D vs B: t = -0.47, p = 0.64. Neither B nor D beats GARCH-t significantly.
- Calibration: A, C and D are too conservative at 5% (hit rates 3.0%, 2.7%, 3.9%); GARCH-t and EWMA are closest.
- **2013 taper tantrum**: mean stress probability 0.007. The equity HMM did not see a bond-led shock.
- EWMA and multivariate EWMA are algebraically identical for a fixed-weight portfolio, so that benchmark adds nothing. DCC was added later to fill the gap.

### 5.2 Exploration (data through 2019-12-31)

| # | Finding | Key numbers | File |
|---|---|---|---|
| 1 | No correlation channel in a diversified universe: bond correlations fall in stress while risk-asset correlations rise, and they cancel | Bond-containing universes: -0.05 to -0.22. Equity/risk-asset universes: +0.13 to +0.39 | `fig_universe_*`, `universe_screen.json` |
| 2 | Volatility-based regime definitions agree; all miss the 2013 taper tantrum. Only a correlation-defined regime flags it, but it also fires in calm 2017 and ignores 2008 | Stress share 22-41%; taper-tantrum stress prob 0.00-0.17 vs 0.68 for the correlation rule | `fig_regimes_C_timelines.png` |
| 3 | The positive stock-bond correlation that motivates the thesis is absent from 2010-2019 | Share of days with positive 252-day correlation: 91% (1988-99), 24% (2000-09), 0% (2010-19) | `longhistory_summary.json` |
| 4 | Regime models beat the pooled normal but never beat smooth benchmarks | D beats A in 105/214; D beats GARCH-t in 0/214 and is worse in 96; vs DCC-t 0 and 124 | `backtest_dm_table.csv` |
| 5 | Correlation channel (D vs B) not detectable | 37/214 raw p<0.05 (about 11 expected), split 18/19; 0 survive Holm (min adjusted p = 0.14). Min detectable diff 0.009 vs median observed 0.003 | `fig_backtest_E_corr_channel.png` |
| 6 | Long history (1992-99, positive-correlation era) does not rescue it | D-B within ±7 per 1000 for six of seven signals | `backtest_*.csv` |
| 7 | Bond-aware regime signals (MOVE, yield vol, IEF vol) give no consistent gain | Sign flips by universe and signal | same |
| 8 | **GARCH margins remove most of the regime-vs-GARCH gap** | Margin effect -0.026 (U1), -0.039 (U3), -0.036 (U8), -0.073 (U10; Holm p = 0.003). RSC-t vs GARCH-t within ±0.016, p>0.12 | `routes/confound_dm_table.csv` |
| 9 | Correlation channel still undetectable with GARCH margins | RSC vs CCC -0.004 to -0.006, p 0.14-0.31; min detectable about 0.011 | `routes/routes_dm_table.csv` |
| 10 | Route M vs Route P: neither primary test significant | D_M vs B p=0.145 (Holm 0.29); D_P vs B p=0.37. In simulation, Route P has the most power (S1 35%, S2 78.5%) | `routes/power_summary.csv` |

Universes: U1 SPY/IEF/GLD, U2 SPY/TLT/GLD, U3 SPY/IEF/HYG, U4 SPY/EFA/EEM, U5 +EEM, U6 +DBC/VNQ, U7 eight-asset, U8 sectors, U9 SPY/LQD/GLD, U10 HYG/EEM/VNQ/DBC, L1 long-history funds (VFINX/VUSTX). Regime signals: HMM_SPY2, HMM_SPY3, HMM_MV2, HMM_SPYVIX2, RULE_VIX20, RULE_RV75, RULE_CORR, plus bond-aware HMM_SPYIEF2, RULE_IEFRV75, RULE_YLDVOL75.

---

## 6. Evidence strength

| Claim | Rating | Why |
|---|---|---|
| Code is correct and reproducible | Solid | 54 tests, bit-for-bit validation of the generalised engine against the pilot |
| The test has low power for moderate correlation shifts | Solid (within the simulated DGP) | Size is right; power curves; reproduced under a second seed. DGP is stylised and has no GARCH |
| Regime volatility beats a pooled normal | Suggestive-to-solid | 105/214 significant, never significantly worse. Overlapping samples |
| Regime-switching correlation adds no detectable gain | Suggestive of "small or absent", but not evidence of absence | 0/214 after Holm, but under-powered |
| Regime models lose to GARCH-t/DCC-t | Fragile as a claim about regimes | Largely a margin confound (finding 8) |
| The GARCH-margin confound explains the gap | Suggestive | Same direction in 4/4 universes, but Holm-significant in only 1/3 new tests. Mean treatment also differs between arms |
| Route P is the best-powered test | Suggestive | Only on a DGP where the shift is concentrated in SPY-IEF by construction |
| Stock-bond positive correlation absent in 2010-2019 | Solid | Direct from the long-history data (fund proxies) |
| Taper tantrum missed by equity regimes | Suggestive | One episode |
| Literature positioning | Fragile | Most references checked at abstract level only; Fortin et al. findings flagged UNVERIFIED in the research doc |

---

## 7. Issues found in this audit

1. **"Untouched" needs a footnote.** No model was fitted on 2020-2025, but the data has been *seen*: the Day-1 EDA (4 Sep) computed summary statistics, correlations and rolling vol on 2010-2025 (`outputs/tables/supervisor_pilot_summary.csv`); the WP0 audit flagged 2020 and 2025 outliers; `data/processed/*` and the raw pilot file run to 2025-12-31 and 2026-09-25. You also know how 2022 played out. The hold-out is still clean in the sense that no specification was tuned on it, but say this explicitly in the write-up.
2. **The lock moved.** The pilot locked 2016 onwards; exploration then used 2016-2019 and moved the lock to 2020. It is documented, but a reviewer can ask why.
3. **Multiplicity.** 214 headline tests, 7 to 10 regime signals, 11 samples, plus routes, layers and sub-periods. Holm was applied only to pre-declared families. The 214 tests overlap heavily.
4. **Approved title vs work.** The title promises "risk-controlled allocation". Nothing so far addresses allocation. Either drop it from the title with the supervisor's agreement or add a small economic-value section.
5. **Open decision list in README is stale in part.** It still lists universe, regime count and benchmark set as open, though exploration informed all of them. Update after the supervisor meeting.
6. **Duplicated pipelines.** `output/` and `outputs/` are deliberately separate but confusing in a thesis appendix.
7. **GARCH-margin layer has no power study.** The pilot DGP has no GARCH dynamics, so the power of the layer you now favour is unknown.
8. **Mean treatment confound.** Static arms use regime-specific means, GARCH arms a constant mean, so finding 8 measures the whole change, not volatility alone.
9. **HMM uncertainty is not in the CIs.** The bootstrap holds regime weights fixed.
10. **Equal weights, one portfolio, three assets.** Every result is conditional on this.
11. **Empty personal notes.** `thesis_notebook.md`, `literature_matrix.csv` and the model card are blank, so the learning record a viva might probe is thin.
12. **No supervisor feedback on file.** The research document says an earlier draft misread the supervisor's "pick 2" instruction, and the original wording is not in the repo. Add meeting notes.
13. **Repo size.** 680 MB with `.venv`; the tracked data is fine, but check the pickles in `output/explore/backtests/` before sharing.

---

## 8. Open decisions

**Needs Prof. Seo** (from the brief and research document):
1. Centre the thesis on detectability, accepting a plain null if that is what the data say?
2. Approve one pre-registered confirmatory specification for 2020-2025. Suggested: SPY/IEF/GLD, SPY HMM, GARCH margins, Route P (SPY-IEF), D vs B at 5%, DCC-t and GARCH-t as comparators.
3. Use the 1986-2019 fund sample only as supplementary evidence?
4. Keep the universe multi-asset or add an equity-heavy secondary?
5. Is a slow macro-state variable in scope?
6. Is a second data vendor (e.g. Tiingo, or CRSP via the university) available? Not verified.
7. Hold-out protocol: cross-validate on 2005-2019, check selection bias (SPA / model confidence set), freeze, run once.
8. Title and allocation extension.

**You can decide alone:** write-up structure, which exploratory figures go in the thesis, filling the notes templates, repo clean-up.

---

## 9. Where the thesis could go

Effort is in working days and is my estimate. "Null still teaches" is what you keep if the result is negative.

| # | Direction | Thesis claim | Done already | Missing | Effort | Main risk | Null still teaches |
|---|---|---|---|---|---|---|---|
| **1** | **Controlled ablation of volatility treatment vs correlation treatment** (2×2: static vs GARCH margins × constant vs regime correlation) | "Most of the regime-model deficit is a margin specification effect; correlation switching adds little once margins are right" | Layer 2 built; confound check on 4 universes | Power study with a GARCH-based DGP; equal-mean control; SPA / model confidence set | 5-8 | Examiner calls it a replication of Pelletier-style models | Where regime information does and does not matter |
| **2** | **Detectability as headline** | "How much data would you need to see a correlation-regime effect, and what is the smallest effect this design can detect?" | WP2, route power, minimum detectable differences | Power for layer 2; power vs sample and effect-size curves; plain write-up | 4-6 | Reads as a negative-results thesis; supervisor must accept | The whole framing is the contribution |
| **3** | **One pre-registered confirmatory test on 2020-2025** (Route P, SPY-IEF, GARCH margins) | "Does letting only the stock-bond correlation switch help through the 2022 reversal?" | Spec nearly fixed; code exists | Supervisor sign-off, freeze and tag, 2022 episode analysis, Giacomini-White conditional test | 4-6 | Single episode; low power; one shot | A clean, honest out-of-sample null |
| **4** | **Slow macro-state for the stock-bond sign** (inflation volatility, good vs bad inflation) | "Stock-bond correlation is a slow macro state, not a fast volatility regime" | Literature in research doc | FRED data, new model, new tests | 10-15 | Time; new multiplicity; little power in 6 years | Whether market-based regimes are the wrong tool |
| **5** | **Economic value / allocation extension** (min-variance or risk-targeted weights using each model's covariance) | "Do better covariance forecasts translate into better risk-controlled portfolios?" | Covariance forecasts exist | Allocation rule, transaction-cost assumption, performance and risk metrics | 5-8 | Crowded literature; added scope | Delivers the title's "allocation" half |
| **6** | **Equity-heavy / sector universe as a primary arena** | "Where a correlation channel exists (risk assets), does regime correlation help?" | U8, U10 explored | Pre-declared test; Forbes-Rigobon adjustment | 3-5 | Off-theme for "diversified"; sign depends on signal | Boundary of where the effect lives |
| **7** | *(my suggestion)* **Evaluate covariance forecasts with a covariance loss, not only tail loss** | "Tail-only scoring from one daily return per day throws away power; a covariance-based loss (e.g. QLIKE on realised measures) can see correlation effects sooner" | None | Realised covariance data (intraday, probably unavailable for free) or noisy proxy; new loss tests | 6-10 | Data access; moves away from VaR/ES focus | Whether low power is a scoring problem rather than a modelling one |
| **8** | *(my suggestion)* **More than one portfolio from the same assets** (random or standard weights, 60/40, risk parity) | "Does the conclusion hold across portfolio weights?" | Weights are config-driven | Pre-declared weight set; careful treatment of dependence between tests | 2-3 | Not independent evidence; inflates test count | Shows weight sensitivity cheaply |

**Combinations that hang together.**
- *Fastest defensible thesis:* **1 + 2 + 3**. The ablation is the model story, the power analysis is the honesty story, the single hold-out run is the test. Most of the code exists.
- *If there is room for ambition:* add **5** to deliver the title's allocation half.
- *Highest upside, highest risk:* **4**, but not with this timeline unless the deadline is generous.

**What I would drop or demote.** Kendall's-tau Route M (no edge once margins are right; keep as a robustness check). Bond-aware regime signals as a headline (no consistent gain). The 1986 fund sample as anything beyond an appendix. The 3-state and 4-state HMM unless the supervisor asks.

**What a harsh examiner would ask.**
- *Direction 1:* "You changed two things between static and GARCH models (volatility and mean). How do you know it's the margins?" Needs the equal-mean control.
- *Direction 2:* "A power study on your own stylised DGP is circular." Needs the calibrated DGP shown alongside and a GARCH-based DGP.
- *Direction 3:* "One episode, one test: why is a null informative?" Needs the minimum detectable effect next to the result, and a clear statement that the claim is about this design, not about correlations in general.

---

## 10. Suggested next steps

Adjust once you know the deadline. Steps 1-3 are cheap and unblock everything else.

| Step | What | Days |
|---|---|---|
| 1 | Write down the supervisor's reply to the brief (even bullet points) into `notes/` and update the open-decisions list | 0.5 |
| 2 | Pick the primary path from Section 9 and a fallback; write one paragraph each | 0.5 |
| 3 | Fill `thesis_notebook.md` with the three concepts you would be asked about first (HMM filtering, FZ0 and joint VaR/ES, why D vs B isolates correlation) | 1 |
| 4 | Equal-mean control and GARCH-DGP power study (Direction 1 and 2) | 4-6 |
| 5 | Selection-bias reporting: count all specs; SPA / model confidence set for "does any regime model beat GARCH-t" | 1-2 |
| 6 | **Freeze the specification**: addendum to the preregistration and a git tag, before opening 2020-2025 | 1 |
| 7 | Single run on 2020-2025, 2022 episode analysis, minimum detectable effect | 2-3 |
| 8 | Write-up: methods, results, power section, limitations, literature positioning | ongoing; start now |

**If time is very short:** skip step 5's extras, keep steps 4 (reduced), 6, 7, 8, and state the limitations plainly.

---

## 11. Appendix

**Key files to open first:** `output/SUPERVISOR_BRIEF.md` (best one-page narrative), `output/explore/EXPLORATION_SUMMARY.md`, `output/FURTHER_EXPLORATION_RESEARCH.md` (Section 2.4 has the newest results), `docs/preregistration.md`, `docs/decisions_log.md`.

**Glossary.**
- **VaR / ES**: loss threshold exceeded with probability alpha / average loss beyond it.
- **FZ0**: a scoring rule that evaluates VaR and ES together; lower is better.
- **DM test**: tests whether one model's average loss differs from another's, with autocorrelation-robust errors.
- **Holm**: multiple-testing correction.
- **HMM**: hidden Markov model; infers a calm/stress state each day.
- **DCC / CCC**: dynamic / constant conditional correlation models.
- **RSC**: regime-switching correlation.
- **Forbes-Rigobon**: correlations rise mechanically when volatility rises, so a measured jump overstates a real change.
- **Power / MDE**: probability of detecting a true effect / smallest effect detectable with 80% power.
