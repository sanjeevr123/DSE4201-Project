# Prompt: audit the whole project and write a progress-and-direction document

Paste everything below the line into a fresh Claude Code session opened at the repo root.
Fill in the three `[...]` fields first.

---

You are auditing my honours thesis repository ("Regime-Switching Risk Models for ETF Portfolios") and writing one
document that lets me (a) recall exactly what has been done, (b) see how trustworthy each result is, and (c) ideate on
what to do next, including whether to pivot. Be a sceptical research assistant, not a cheerleader.

## Context you must not get wrong

- Question: for a fixed diversified ETF portfolio (pilot: equal-weight SPY/IEF/GLD), does letting cross-asset
  **correlations** switch by regime improve one-day VaR/ES forecasts beyond letting only **volatilities** switch?
  Primary contrast is model D vs model B (A = pooled, B = regime vols, C = regime corr, D = both).
- Approved title also promises "risk-controlled allocation". Check how much of that has been addressed.
- Phases: Day-1 EDA, then pilot WP0-WP5 with pre-registered go/no-go criteria G1-G6, then an exploration phase
  restricted to data through 2019-12-31, then GARCH-margin / Route M / Route P follow-ups.
- Data rule: 2020-2025 is a confirmatory hold-out. **Do not run any model, backtest or statistic on data after
  2019-12-31, and do not download new data.** This audit is read-only apart from the one output file.
- Supervisor: Prof. Seo (financial econometrics / dependence modelling).
- My situation: deadline `[DATE]`, hours per week available `[N]`, and what I want most from the thesis
  `[e.g. a clean defensible result / a publishable idea / skills for quant roles]`.

## Step 1: inventory (read everything, skip nothing)

Read every tracked file: `git ls-files`. Group them as you go. For each group note purpose, state (done / partial /
stale / empty template), and what it depends on.

- Prose and records: `README.md`, `docs/`, `notes/`, `output/*.md`, `output/explore/EXPLORATION_SUMMARY.md`,
  `output/FURTHER_EXPLORATION_RESEARCH.md`, `output/STUDY_GUIDE.md`, `output/SUPERVISOR_BRIEF.md`.
- Config, code, tests: `config/pilot.yaml`, `src/`, `scripts/`, `starter/`, `tests/`, `notebooks/`.
- Results: `output/tables/*.json`, `output/explore/*.csv|json`, `output/explore/routes/*`, `output/figures/`,
  `outputs/` (the older, separate Day-1 EDA pipeline), `data/metadata/`, `data/raw/MANIFEST.txt`.
- Look at the figures (`.png`) and describe what each one shows.
- Use `git log` for the timeline. Run `pytest tests -q` once and report the count.

## Step 2: verify, don't transcribe

Prose summaries in this repo were written by earlier sessions. For every headline number you put in the document,
trace it to a result file (JSON/CSV) and cite the file. Where prose and files disagree, say so. Specifically check:

1. The "0 of 214 Holm-significant" and "37 of 214 raw p<0.05" claims against `output/explore/backtest_dm_table.csv`.
2. The D-vs-B, D-vs-GARCH-t and D-vs-DCC-t counts in `EXPLORATION_SUMMARY.md`.
3. Pilot power table (`output/tables/wp2_summary.json`) vs `PILOT_REPORT.md` vs `output/explore/routes/power_summary.csv`.
4. The GARCH-margin confound table (U1, U3, U8, U10) vs `routes/confound_dm_table.csv`.
5. Whether anything computed so far has *looked at* 2020-2025 (including descriptive EDA, the data audit, the processed
   returns files, figures, notebooks). Separate "no model was fitted there" from "the data was never seen".
6. Whether any pre-declared rule (primary tests, Holm families, G1-G6) was changed after results were seen.
7. Stale facts: test counts, "next steps" lists, README stage text, duplicated pipelines (`output/` vs `outputs/`).

## Step 3: write `output/THESIS_PROGRESS_RECAP.md`

Audience: me, the thesis author, who will use it to brainstorm. Plain language; define any term on first use.
Tables for numbers, short prose for reasoning. Target 8-12 pages. Use exactly these sections:

1. **One-page summary**: where the project stands, the single most important result, the single biggest risk.
2. **Timeline**: dated milestones from git.
3. **The research design**: question, models A-D, benchmarks, scoring, windows, data rules, in one page.
4. **Repository map**: what each folder/script does and the order to run it.
5. **Results so far**: pilot (WP0-WP5) then exploration (all findings), each with the number, file, and sample used.
6. **Evidence strength**: a table of every claim, rated *solid / suggestive / fragile / unsupported*, with the reason
   (power, multiple testing, in-sample, proxy data, confounds, unverified citations).
7. **Issues found in this audit**: inconsistencies, stale docs, hold-out exposure, gaps between the approved title and
   the work, empty templates, anything that would embarrass me in a viva.
8. **Open decisions**: what still needs the supervisor, and what I can decide alone. Note which supervisor feedback is
   *not* recorded in the repo.
9. **Where the thesis could go**: see Step 4.
10. **Recommended next steps**: a dated plan that fits `[DATE]` and `[N]` hours/week, with a "minimum viable thesis"
    path and a "stretch" path, plus what to cut first if time runs short.
11. **Appendix**: file index, key numbers, glossary.

## Step 4: directions and pivots (the part I care most about)

Give at least 6 distinct options, including the ones already on the table (power/detectability as headline; the
GARCH-margin confound as the central contribution; a single pre-registered Route-P test on 2020-2025; slow macro-state
signal; equity-heavy universe; allocation/economic-value extension) **and at least two new ideas of your own**.
Mark anything not grounded in the repo or a verified source as *my suggestion, unverified*. Do not invent citations.

For each option give: the thesis claim it would support; what is already done toward it; what is missing; effort in
days; main risk; what a null result would still teach; novelty relative to the literature already in the repo; fit with
the hold-out rule. Then score all options on impact, feasibility by `[DATE]`, and risk, rank them, and recommend one
primary path and one fallback with a reason. Say what you would drop and why. Include one "what would a harsh examiner
ask" paragraph per top-3 option.

## Rules

- Report nulls and weak evidence plainly. Do not rescue a result by rewording it.
- Distinguish: confirmatory vs exploratory, in-sample vs out-of-sample, pre-declared vs post hoc.
- Numbers come from files, not memory. If you cannot verify something, write [UNVERIFIED].
- Do not edit any existing file. Do not commit. Do not run new backtests or simulations.
- When done, give me a 10-line summary in chat and list any question you could not answer from the repo.
