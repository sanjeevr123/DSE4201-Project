# Prompt: format and style from the reference thesis, then draft chapters 3 to 6

Paste everything below the line into a Claude Code session at the repo root. The reference thesis (Santoso, NUS Department of Economics, AY2023/24) is already at `notes/reference/2342328347 - THERESIA AGUSTINE SANTOSO - AY2324_Sem_2.pdf`. Do not commit it.

---

You are helping me write my honours thesis ("Regime-Switching Risk Models for ETF Portfolios: Do Market-State Shifts Improve Tail-Risk Forecasting?", BSc Data Science and Economics, NUS, supervisor Prof. Seo). It must be economics and data-science work at the level of an NUS 4000-level honours thesis. The plan is `docs/THESIS_PLAN.md`, the standing rules are in `docs/THESIS_EXECUTION_PROMPT.md`, and the state is in `docs/EXECUTION_LOG.md`. Read all three first. Phases 0, 1 and 3 are finished. The hold-out has not been run and must not be run in this session.

## 1. What I want

1. A **format specification** measured from the reference thesis, and a **LaTeX scaffold** that reproduces its page layout, spacing, margins, headings, tables, figures, front matter and referencing.
2. A short **style guide** (`notes/thesis_style_guide.md`) for structure, tone, phrasing and information layout, drawn from the reference thesis and from my own plan.
3. **Chapters 3, 4, 5 and 6** drafted in that format and style, plus a chapter 2 skeleton, with chapter 7 left as a placeholder.

The reference thesis is for **format, structure, tone, phrasing, information layout, sentence construction and citation practice**. Never copy its sentences, tables, figures or arguments. Everything I submit is original text about my own work.

**Requirements file.** When you write `notes/requirements.md` (plan Phase 2), state the format this thesis uses as the format adopted: A4, margins, font and size, line spacing, heading style, citation style. **Do not say or imply that it comes from the reference thesis or from any other thesis.** Record what is not known: deadline, length limit, title-change process, viva, AI-use policy. Keep the reference thesis only in `notes/reference_thesis_analysis.md`.

**Do not search the web for this task.** I have decided the reference thesis is the format authority, so no search for official NUS rules or guides is needed. If a gap could only be closed online (an official deadline or length limit, a citation to verify, an AI-use policy), do not search. Record it in `notes/outbox/02_requirements_questions.md` for me to ask, or keep the claim marked `[UNVERIFIED]`.

## 2. Standing constraints (from the execution prompt; they still apply)

- **Hold-out discipline.** Do not run `scripts/confirm_00_run.py holdout`. Do not load, compute on or display returns after 2019-12-31. Do not open the protected files listed in section 2 of the execution prompt.
- **Evidence.** Every number in the thesis traces to a result file, ideally through `thesis/numbers.yaml` and `scripts/check_numbers.py`. Report weak and null results plainly. Do not round in a flattering direction.
- **Wording.** `scripts/check_wording.py` must pass on every chapter. Never write that a non-significant result means "no effect". Say "I do not detect ... (estimate, 95% CI, minimum detectable difference)". Use "I did not find" for novelty claims, never "no study has".
- **Citations.** No invented citations. Anything not checked against a registry, abstract or full text stays `[UNVERIFIED]`. Do not take a citation from the reference thesis on trust: it contains at least one error (see 3.3).
- **Installs.** Use only established, verified sources. The toolchain (`tectonic`, `pandoc`) is already installed through Homebrew. If something else is needed, ask me first.
- **Single process, light load.** This is reading and writing work. No simulations. If you run any compute, follow the CPU and thermal rules in `docs/EXECUTION_LOG.md`.
- **Git.** Stage named files only. No push. No Claude co-author or footer lines. Do not commit the reference thesis PDF.
- **Authorship.** Do not write in my voice as a personal learning record. Leave `notes/thesis_notebook.md` empty.
- Keep `docs/EXECUTION_LOG.md` current. Give me one short status line per step.

## 3. Step A: read, then measure the reference thesis

Read the state files in section 0, then the whole reference PDF. **Measure its format from the file with code (for example `pypdf` in `.venv`, which is installed); do not guess from the look of it.** Log each measured value and how you measured it.

### 3.1 Format I measured (verify; correct me where the PDF disagrees)

| Element | Measured or observed |
|---|---|
| Page size | **A4, 210 x 297 mm (my decision, overriding the reference).** The reference itself is US Letter, 8.5 x 11 in (612 x 792 pt), 40 pages; use its other measurements below as given |
| Margins | About 1 in (2.54 cm) on all sides, kept on A4: left text edge at 0.98 in (measured); right edge about 0.9 to 1.0 in (read from a page image, so confirm it) |
| Font | Latin Modern Roman, the LaTeX default family, normal size 10.9 pt, which is the `11pt` class option |
| Line spacing | Double: 27.1 pt from line to line at 11 pt. Table notes 8 pt. Equations in math italic |
| Paragraphs | First-line indent, no extra space between paragraphs |
| Page numbers | Roman (i to iv) for front matter, arabic for the body starting at the Introduction. Observed: centred at the foot of chapter-opening pages (about 0.57 in from the bottom) and centred at the top of other pages. Confirm on several pages |
| Title page | Title in capitals, "by", author, "Honours Thesis in Part Fulfilment for the Degree of Bachelor of Social Sciences (Honours)", "Presented to Department of Economics, National University of Singapore 2023/2024" |
| Front matter order | Abstract (one paragraph, then KEYWORDS), Acknowledgements, Table of Contents, List of Figures, List of Tables |
| Chapter headings | Centred, bold, capitals, number first: "1 INTRODUCTION" |
| Section headings | Centred, bold, "3.1 Sentiment Data"; sub-sections left-aligned bold, "3.2.1 FinBERT" |
| Tables | Caption above, centred, in capitals ("Table 3.1: TIME PERIODS AND ..."); horizontal rules only; single-spaced; a "Note:" line below at 8 pt with units, scaling and sign convention |
| Figures | Caption below, in capitals ("Figure 4.1: TIME SERIES OF ...") |
| Numbering | Tables and figures by chapter (Table 4.2, Figure 4.1); equations run continuously, (1) to (21), at the right margin; appendix tables A.1, A.2 |
| Citations | Author-date in text ("Hansen et al. (2014)'s ...", "(Barbaglia et al., 2023)") |
| References | Alphabetical, single-spaced, bold surnames, hanging indent, a repeated author shown with a dash |
| Contents and lists | Number, caption in capitals, dotted leader, page |
| Body length | About 32 numbered pages, double spaced; chapters 1 Introduction, 2 Literature Review, 3 Data and Methodology, 4 Empirical Results, 5 Conclusion, References, Appendix |

The chapter numbering matches an `article`-style document where each chapter is a numbered `\section` ("1 INTRODUCTION") and sub-sections are numbered 3.1, 3.2.1. Check this against the PDF and choose the LaTeX class and `titlesec` settings that reproduce it.

**Page size is decided: A4.** Set it in one place in the preamble. Keep the measured margins, font size and line spacing from the table.

**One thing to flag to me.** Length: no length rule is known. The reference body is about 32 pages (roughly 8,000 to 9,500 words with tables and equations). My plan's 12,000-word figure is a planning number only. Report the page count the layout produces and tell me if the body exceeds about 50 pages.

### 3.2 Structure, tone and information layout I observed

- **Introduction:** a broad hook, then the gap, the objective, the approach, a numbered list of what is assessed, and a one-paragraph roadmap.
- **Literature review:** organised by strands of work, narrowing to what the thesis adds.
- **Data and methodology:** numbered sub-sections for data, each model, the estimation scheme, the loss functions and the test, with numbered equations and a symbol defined at first use.
- **Results:** each table is followed by prose that says what it shows and ties the result back to earlier work. A sub-period section for an unusual episode.
- **Conclusion:** summary, what it means, limitations, future work.

Keep what works: signposting, strand-by-strand literature, table notes, and links from each result to earlier work. Where it is weak, do better (see 3.3). For my thesis the standard on inference and wording is the one in section 2.

### 3.3 Defects in the reference: do not reproduce them

- The roadmap points to a "section 6" when the conclusion is section 5. The text says "four distinct sets" and lists three.
- The Diebold-Mariano test is written with an equation that equates a loss differential to zero, which confuses the statistic with the null. The sign convention of the t-statistics changes between tables. Significance is claimed at "10%" and "15%" levels without a reason.
- Presentation slips: "FiGAS, also known as FiGAS", a mistyped GARCH equation, misspellings in headings, and "this paper" and "this thesis" used interchangeably.
- Diebold and Mariano is cited as 1996. My plan records it as 1995, *J. Business & Economic Statistics* 13(3); keep it `[UNVERIFIED]` until checked against a registry.
- An outlier rule (3-sigma) is applied with no sensitivity analysis. Estimation choices are justified with "it is plausible that".

Write `notes/reference_thesis_analysis.md`: the measured format table with page references and the method used, what worked, what did not, and which of my chapters each point affects. It contains no copied text.

## 4. Step B: write `notes/thesis_style_guide.md`

One guide I can keep open while writing. Sections:

1. Format specification (from 3.1, as measured).
2. Chapter contract: purpose, contents, required exhibits and share of length for each chapter, from plan 6.1.
3. Voice and tense: choose between "I" and "this thesis", state the choice, and keep it. The reference mixes them; do not.
4. Sentence and paragraph rules with before-and-after examples written about my own topic: one idea per paragraph, topic sentence first, define a term at first use, active voice, no filler or hype, claims no stronger than the evidence.
5. Notation table and equation rules.
6. Table and figure standard: the layout in 3.1, and a worked example built from `output/explore/ladder/ladder_dm_table.csv` that adds my reporting standard (estimate, SE, 95% CI, n, labelled p-value, MDE, sign convention, sidedness label). The reference uses stars or t-statistics; mine uses intervals.
7. Citation standard: author-date, how to cite working papers, data and software, and the `[UNVERIFIED]` rule.
8. Pre-submission checklist.

Mark each rule as **reference** (observed in the thesis), **plan** (from my plan or execution prompt) or **practice** (general writing practice that you are stating from your own knowledge, with no outside source). Do not present a practice rule as if it were sourced.

## 5. Step C: LaTeX scaffold

Under `thesis/tex/`: `main.tex` with the measured settings in one preamble file, one file per chapter, `front/` (title page in the reference's wording adapted to my details, abstract with keywords, acknowledgements placeholder, contents, list of figures, list of tables, list of abbreviations and notation), `references.bib`, and a build command using `tectonic`. Roman numerals for the front matter, arabic for the body, and page numbers placed as measured. Check that the empty scaffold builds on A4 and that a page from it matches the reference's margins, font size, line spacing and heading style when measured with the same code (page size excepted). Log the settings.

## 6. Step D: draft chapters 3 to 6

Follow plan 6.1 for purpose and share, plan 2.A for what each comparison isolates, plan 2.C for the story and the claim-to-exhibit map, and the style guide for form.

- **Chapter 3 (data and sample design):** data, vendor, returns, portfolio (constant weights, rebalanced daily), the development, dry-run and hold-out split, hashes, and the disclosure of what was seen before the freeze.
- **Chapter 4 (methodology):** every model with equations and consistent notation; the table of what differs between comparisons (plan 2.A.1, re-verified cell by cell against the code); the mean treatment; what is estimated, when and on what window. A reader must be able to reimplement the study from the text.
- **Chapter 5 (evaluation and inference):** FZ0 and its derivation, DM and Giacomini-White readings, the HAC rule, the one-sided test and the "worse" rule, minimum detectable differences, the smallest effect of interest and its derivation, calibration tests, how to read the power study, multiple testing, preregistration. Separate estimand, estimator, test, decision rule and interpretation.
- **Chapter 6 (exploration and ladder results):** the storyline in plan 2.C.1, the exhibits in 2.C.2, the D-vs-B size finding, the missed pre-declared bar, the real-data RSC_P vs CCC row, the 1,508-day power results. Use the greyscale figures from `scripts/thesis_fig_forest.py`.
- **Chapter 2:** a skeleton organised by plan 6.3 as an argument. Every specific finding stays `[UNVERIFIED]`; leave out claims you have not read.
- **Chapter 7:** a placeholder only. Do not interpret any hold-out result.

For every table and figure, write the sentence that says what it shows and why it matters. Define every term at first use for a reader who knows econometrics but not this project.

## 7. Step E: quality gates

Run and fix until clean, and report the results:

1. `scripts/check_wording.py` on every chapter, plus a read for meaning (phrases can overstate without being banned).
2. Number trace: every number in the prose maps to a result file.
3. Citations: every in-text citation is in the bibliography and the reverse; the `[UNVERIFIED]` count is listed.
4. **Originality check against the reference thesis:** no run of 8 or more consecutive words, and no table or figure layout copied beyond the measured format. Say how you checked.
5. Consistency: model names, notation, sign convention ("richer minus baseline; negative means better"), sample sizes, sidedness labels, cross-references.
6. **Format check:** build the PDF, measure page size, margins, line spacing and font with the same code used on the reference, and compare. Convert pages to images and inspect equations, tables, figures and fonts.
7. A read as a newcomer to the project: can each section be followed, and does the storyline hold?

## 8. Stopping and reporting

Commit in stages (named files only): format analysis and style guide; scaffold; each chapter. Do not tag `prewrite-v1` yet; that waits for the Phase 4 gate. At the end, give me a one-page report with: the format values you measured and any that differ from section 3.1, the style decisions you made and why, what the reference did well and badly, what is `[UNVERIFIED]`, the page count, and what only I can do (confirm any length limit and the deadline with the programme office, check paywalled sources at the NUS library, choose my voice and the AI-statement wording).

If something blocks you, record it and carry on with whatever is independent of it.
