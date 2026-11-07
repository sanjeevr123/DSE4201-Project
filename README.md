# Regime-Switching Risk Models for ETF Portfolios

Honours thesis code and results: *Regime-Switching Risk Models for ETF Portfolios: Do Market-State Shifts Improve Tail-Risk Forecasting?* The compiled thesis is `thesis/final/thesis.pdf`; Chapter 10 of the thesis documents this repository.

## Question and answer

A risk manager who reports one-day value-at-risk (VaR) and expected shortfall (ES) for a stock, bond and gold portfolio has to decide whether the stock–bond correlation should be allowed to change with the market state. The thesis tests whether letting the SPY–IEF correlation switch with a two-state hidden Markov regime (fitted to SPY) improves VaR and ES forecasts of an equal-weight SPY, IEF and GLD portfolio, against constant correlation with the same GARCH margins. Forecasts are scored with the FZ0 joint loss.

The comparison was fixed before the 2020–2025 hold-out was used and was run once. Over 1,508 hold-out days the switching model's loss was lower by 0.0013 (95% interval −0.0037 to +0.0012; one-sided p = 0.158; outcome O2). The test could detect only differences above 0.0031, so a useful gain is neither shown nor ruled out. Both models breached the 5% VaR on about 6.8–6.9% of days; a post hoc EWMA breached on 5.2% with a loss that could not be told apart from theirs.

## Repository map

| Folder | Content | Thesis |
|---|---|---|
| `config/pilot.yaml` | parameters and seeds (window, refit intervals, tail levels, simulation design) | Ch. 4–5 |
| `data/raw/` | raw Yahoo Finance downloads, never re-pulled, with SHA-256 hashes in `MANIFEST.txt` | Ch. 3, 10 |
| `src/` | models (HMM, static covariance, GARCH margins, DCC), FZ0 loss, DM and coverage tests, simulation | Ch. 4–5 |
| `scripts/explore_*` | development results and power studies | Ch. 6 |
| `scripts/confirm_*` | frozen hold-out runner (`confirm_00_run.py`), scorer (`confirm_01_score.py`) and checks | Ch. 5, 7 |
| `scripts/thesis_*`, `build_all.py`, `check_numbers.py` | summary statistics, tables, figures, post hoc checks, number trace, PDF build | all chapters |
| `output/explore/`, `output/confirm/` | development, dry-run, hold-out and post hoc results; stored hold-out forecasts (`holdout_forecasts.pkl`) | Ch. 6–7 |
| `output/figures/`, `output/tables/` | thesis figures; data summary and pilot tables | Ch. 3, 6–7 |
| `docs/` | confirmatory specification and the log of every specification tried | Ch. 3, 5 |
| `tests/` | 101 tests by default; 3 more read hold-out-period data and were run only after scoring | Ch. 10 |
| `thesis/` | LaTeX source, generated tables, `numbers.yaml` (every registered prose number and its source file) | — |

`scripts/00`–`02`, `wp2`–`wp4`, `src/wp*`, `src/run_pilot.py`, `src/audit.py`, `data/processed/`, `data/metadata/` and `output/tables/wp*` belong to the pilot stage. No thesis table depends on them; they stay because tests and `explore_05 --validate` read them, and `src/` is frozen.

## Exhibits and their sources

| Exhibit | Result file | Script |
|---|---|---|
| Table 3.1, Figure 3.1 (summary statistics, SPY–IEF correlation) | `output/tables/data_summary.json` | `thesis_data_summary.py` |
| Table 3.2 (eras) | `output/explore/longhistory_summary.json` | `explore_03_longhistory.py` |
| Table 5.1 (smallest effect of interest) | `output/confirm/sesoi.json` | `confirm_04_sesoi.py` |
| Tables 6.1–6.4, Figure 6.1, Appendix B | `output/explore/ladder/ladder_dm_table.csv`, `ladder_loss_table.csv` | `explore_13`–`explore_15`, `thesis_fig_forest.py` |
| Table 6.5 (primary pair, development) | `output/explore/routes/routes_dm_table.csv` | `explore_08`, `explore_09` |
| Table 6.6 (power) | `output/explore/ladder/power_1508_summary.csv`, `power_2520_twosided.csv` | `explore_16`, `explore_20`–`explore_22` |
| Tables 7.1–7.3 | `output/confirm/holdout/` | `confirm_00_run.py holdout`, `confirm_01_score.py` |
| Figure 7.1, Table 7.4 (breaches by year), post hoc rows | `holdout_forecasts.pkl`, `posthoc.json`, `baselines.json` | `thesis_fig_cumulative.py`, `thesis_posthoc.py`, `thesis_baselines.py` |
| Figure 8.1 (regime signal and correlation estimates) | `holdout_forecasts.pkl`, `regime_summary.json` | `thesis_fig_regime.py` |

All tables are written to `thesis/tex/generated/` by `thesis_tables.py` (Table 3.1 by `thesis_data_summary.py`; Tables 3.3 and 4.1 are written by hand); figures go to `output/figures/`.

## Setup

Python 3.9.6, tested on macOS. From the repository root:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` is frozen with the hold-out specification and therefore also lists notebook packages that the analysis does not need. The PDF build needs [tectonic](https://tectonic-typesetting.github.io/).

## Reproduce

| Task | Command | Time |
|---|---|---|
| Rebuild every table and figure from saved results, check the 190 registered numbers, build the PDF | `.venv/bin/python scripts/build_all.py` (`--no-pdf` to skip LaTeX) | seconds |
| Run the tests | `.venv/bin/python -m pytest -q` | under 1 minute |
| Post hoc checks and baselines, from the stored forecasts | `.venv/bin/python scripts/thesis_posthoc.py`, `scripts/thesis_baselines.py` | seconds |
| Verify the build from a clean clone of the committed repository | `.venv/bin/python scripts/verify_clean_clone.py` | minutes |
| Dry run and hold-out, then scoring | `scripts/confirm_00_run.py pseudo` or `holdout`, then `confirm_01_score.py` | under 1 minute |
| Development results | `scripts/explore_00` … `explore_20` in order | several hours |
| Power at the hold-out length | `scripts/explore_21_power_holdout_length.py --workers 4`, then `explore_22_power_summary.py` | about 19 s per replication on one core; 2,000 replications (2–3 h on 4 workers) |

Large intermediate files (`output/explore/**/*.pkl`, `*.jsonl`) are not tracked; the `explore_*` scripts regenerate them, and the csv/json summaries the thesis reads are tracked.

## Frozen specification

The hold-out specification is fixed by the annotated tags `spec-freeze-v1` and `spec-freeze-v1.1` (one amendment of the scorer's validity rule, made before any scoring and recorded in `docs/preregistration_confirmatory.md`, section 8). The scorer checks that `src/`, the runner and `requirements.txt` are unchanged since the tag, so those files are not edited, including stale comments in them (for example the reference to `docs/decision_log.md` and the pilot-era `locked_test_start: 2016-01-01` in `config/pilot.yaml`, which the confirmatory run does not use). Results produced after the freeze (`thesis_posthoc.py`, `thesis_baselines.py`, `thesis_fig_cumulative.py`, `thesis_fig_regime.py`) are labelled POST HOC in the thesis.

## Data

Daily adjusted closes for SPY, IEF and GLD, and the development-only ETF and fund samples, come from Yahoo Finance through `yfinance` (vintage 26 September 2026) and are stored with their SHA-256 hashes; the pilot file `data/raw/pilot_etf_yahoo_2010_2025.csv` is not in `MANIFEST.txt`. Yahoo revises adjusted prices, so a fresh download can change the numbers slightly, which is why the raw files are kept. Yahoo's terms on redistribution have not been checked: keep the repository private, or confirm the terms before making it public.

## Known quirks

- About 450 `RuntimeWarning`s in the test run come from NaN rows before the first forecast in a frozen module; they are harmless.
- BLAS threads are fixed to one in `build_all.py`; results were produced on one machine and have not been checked on another.
