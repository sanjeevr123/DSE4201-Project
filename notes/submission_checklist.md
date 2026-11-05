# Submission checklist (draft; items marked YOU can only be done by the author)

## Done in the repository
- [x] Thesis builds from source (`scripts/build_all.py`); clean-clone rebuild matches (`scripts/verify_clean_clone.py`).
- [x] 191 registered prose numbers traced to output files (`scripts/check_numbers.py`, 0 problems); wording, citation and format gates pass; pytest 110 passed.
- [x] Pre-specified test run once; outcome O2 reported with the frozen sentence; amendment `spec-freeze-v1.1` disclosed (Ch7 Section 7.1).
- [x] Four independent reviews run and acted on (`docs/EXECUTION_LOG.md`, Phase 10).
- [x] Final PDF: `thesis/final/thesis_draft_for_review.pdf`. Editable export: `thesis/final/thesis_editable_draft.docx` (pandoc conversion of the LaTeX; formatting is approximate; the PDF is the reference version).

## YOU
- [ ] Title page: author name, degree wording, department or programme (placeholders in `thesis/tex/front/titlepage.tex`).
- [ ] Acknowledgements (`thesis/tex/front/acknowledgements.tex` still reads "TO WRITE").
- [ ] Confirm the official format, page limit (the thesis has about 54 numbered pages against a guideline of about 50), deadline, title change, and any AI-use declaration with the programme office.
- [ ] Decide the final wording of the AI-assistance statement (`notes/ai_statement_draft.md`) and where it goes.
- [ ] Send `notes/outbox/04_full_draft_note.md` (and the earlier outbox notes) to Prof. Seo.
- [ ] Read the whole thesis yourself; read `notes/viva_prep.md`.
- [ ] Submit. Nothing has been pushed or submitted by me beyond the earlier branch push.

## Known issues (not blocking)
- Preregistration section numbering has two sections numbered 8 (frozen file, left).
- Low-severity open items from the reviews are listed in `docs/EXECUTION_LOG.md` (notation collisions B/R/mu/A, glossary of git terms, repeated result paragraphs, abbreviation-list gaps).
- Literature: several sources read as abstracts or working papers only (`notes/literature_audit.md`); candidate further references in `notes/outbox/05_library_requests.md`.
- Figure 6.1 and a few tables have underfull-box warnings.
