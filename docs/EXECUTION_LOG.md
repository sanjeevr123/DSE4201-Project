# Execution log

State file for `docs/THESIS_EXECUTION_PROMPT.md`. If this file exists, resume from "Next step" and never rerun a completed one-shot step.

**Next step:** see the last phase entry below.

## Hold-out status
Not run. `HOLD-OUT GO-AHEAD: NOT YET GIVEN`. Tags: none yet.

## Standing constraints added by the user
- 2026-11-03: use only established, trusted packages and install methods, verified before use. If the instructed route is unavailable, ask.

## Corrections to the plan
| Plan ref | Plan says | Evidence | Action |
|---|---|---|---|
| 3.8 | `.gitignore` ignores `output/confirm/pseudo_forecasts.pkl` | `git ls-files` lists it as tracked; `git check-ignore` returns nothing | The dry-run pickle has git history. Keep the tracked copy until the Phase 3 bit-identity check is done. Decide on the hold-out pickle by size at the time. |
| 2.E | Correction email has 5 items | E4 and E11 also bear on how results are read | Note has 7 items, including mean treatment and the D-vs-B size. |
| 2.A.3 | "Margin and volatility steps 91-100%" not listed as an error | `power_summary.csv`: maximum is 99.5% | Corrected draft shows per-scenario ranges with 99.5%. |

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
