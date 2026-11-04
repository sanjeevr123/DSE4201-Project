# Reference thesis analysis (format, structure and tone only)

Reference: Santoso, NUS Department of Economics honours thesis, AY2023/24, 40 PDF pages (file in `notes/reference/`, not committed). Used only for page layout, spacing, heading and table conventions, structure, tone, and citation practice. Nothing in it is reused as text, table, figure or argument. This file contains no copied sentences.

## 1. How it was measured

| Step | Method |
|---|---|
| Page size, fonts | `pypdf` 6.19 (`.venv`): `mediabox` and the `/Font` resources of every page |
| Text positions, sizes, line pitch | `pypdf` `extract_text(visitor_text=...)`: each text chunk's start position (text matrix times CTM), font and effective size; baselines grouped per page |
| Margins | Each page rendered to 100 dpi greyscale with CoreGraphics (`swift`, scratch script), then the bounding box of dark pixels per page (Pillow, numpy) |
| Visual check | Pages 4, 17, 27, 38 inspected as images |

Units. PDF coordinates are in big points (1/72 in). LaTeX points are 1/72.27 in, so 1 TeX pt = 0.9963 bp. Values below are in bp unless marked "TeX pt". Several figures only make sense after converting: the line pitch 27.1 bp is exactly 27.2 TeX pt, which is twice the 11pt class baseline of 13.6 TeX pt.

## 2. Measured format

| Element | Value measured | Where |
|---|---|---|
| Page size | US Letter, 612 x 792 bp, all 40 pages. **This thesis uses A4 instead (author's decision).** | all pages |
| Left and right margin | Text starts at x = 70.9 bp = 2.50 cm; right ink edge is 0.99 to 1.00 in from the page edge (render); so left and right margins are 2.5 cm | pages 2 to 39 |
| Top margin | First baseline of a full page at 81.8 bp from the top; with `\topskip` of 10.95 TeX pt that puts the top of the text block at 70.85 bp = 2.5 cm | pp. 2, 6, 9 |
| Bottom | A full page holds 24 lines (baselines 81.8 to 705.1); block height 23 x 27.2 + 10.95 = 636.5 TeX pt; consistent with a 2.5 cm bottom margin | p. 9 |
| Text width | about 6.5 in on Letter (21 cm minus 5 cm on A4 is 16 cm) | all |
| Font | Latin Modern Roman: `LMRoman10-Regular`, `-Bold`, `-Italic` at 10.9 bp (10.95 TeX pt, the `11pt` class), `LMRoman8` for table notes and sub/superscripts, `LMRoman12-Bold` for front-matter list headings at 14.3 bp (`\Large`) and for the title page at 12 bp (`\large`), `LMMathItalic` for equations | font resources |
| Line spacing | Body: 27.1 bp = 27.2 TeX pt = baseline stretch exactly 2 on the 11pt class. Title page 27.9 bp = 28 TeX pt (double on 12/14). Table notes, references and tables are single spaced | pp. 2 to 37 |
| Paragraphs | First line indented 16.9 bp = 17 TeX pt (the class default); no extra space between paragraphs; the paragraph directly after a heading is not indented (checked on pp. 8, 13, 17, 18) | pp. 7, 8 |
| Page numbers | Front matter: lower-case roman, centred at the foot (baseline 41 bp, 0.57 in, from the bottom edge). Body: arabic from the Introduction (page 1), **right-aligned at the top** (baseline 43.5 bp from the top, right edge at the text margin), except on pages where a chapter heading starts and on the first body page, where the number is centred at the foot (pp. 6, 8, 13, 22, 36). The prompt's "centred at the top" is wrong; it is right-aligned at the top | pp. 2 to 40 |
| Title page | Everything bold 12 bp, centred: title in capitals on two lines (first baseline 107 bp from the top), "by" (319), author (347), degree wording (531, 559), "Presented to" (615), "Department of Economics" (643), "National University of Singapore 2023/2024" (671). No page number | p. 1 |
| Front matter order | Title, Abstract (heading centred bold; one paragraph; "KEYWORDS:" line in bold at the foot of the page, 683 bp), Acknowledgements, Table of Contents (heading 14.3 bp bold, left), List of Figures, List of Tables (same style, continuing on the same page) | pp. 1 to 5 |
| Chapter heading | Centred, bold, same size as body (10.9 bp), capitals, number first ("3 DATA AND METHODOLOGY"). Chapters do **not** start a new page except the Introduction. Space above: baseline pitch 44.7 bp to the previous line (an extra 17.6 bp); below 38.0 bp (an extra 10.9 bp) | pp. 8, 13, 22, 36 |
| Section heading | Centred, bold, body size, title case, "3.4 In-Sample, Out-of-Sample & Evaluation Sets"; 34.6 to 34.7 bp to the first text line | pp. 13, 17 |
| Sub-section heading | Left-aligned, bold, body size, "3.5.1 GARCH(1,1)"; 34.1 bp to the text | p. 18 |
| Counters | Chapter = LaTeX `\section`, section = `\subsection`, sub-section = `\subsubsection`; tables and figures numbered within the chapter (Table 3.1, Figure 4.2); equations run (1) to (21) through the whole thesis; appendix tables A.1, A.2 | pp. 17 to 40 |
| Tables | Caption above, centred, "Table 3.1: " in the body font then the caption in capitals; rules above the header, below the header, and below the last row (some tables also between rows); header row bold; body single spaced (row pitch 16.9 bp; the one-sample table 24.9 bp); a "Note:" paragraph below at 8 bp, in a narrower measure than the table, ends with units and scaling | pp. 17, 25, 27 |
| Figures | Caption below, centred, "Figure 4.1: " then capitals; sub-figures lettered (a), (b), (c) | pp. 23, 24 |
| Equations | Centred, math italic, number in parentheses flush with the right margin | pp. 14 to 35 |
| In-text citation | Author-date, "Name et al. (2023)" in running text and "(Name et al., 2023)" in parentheses; `natbib` style | throughout |
| Reference list | Heading "REFERENCES" centred bold; entries single spaced, hanging indent 10.8 bp, 22.5 bp between entries, author names in bold, titles in quotation marks, journal and volume in italics, repeated author replaced by a dash and comma; the list shows tool-export noise ("Publisher:", "_eprint:") that this thesis avoids | pp. 38 to 39 |
| Contents and lists | Entry number, caption (capitals in the lists of figures and tables), dotted leader, page number at the right; chapter entries bold with larger gaps (37.9 bp pitch), section entries indented 16.2 bp, regular weight, 26 to 27 bp pitch | pp. 4, 5 |
| Appendix | "APPENDIX" bold centred, then "Appendix A" and a caption; tables A.1, A.2 | p. 40 |
| Body length | About 32 numbered pages double spaced: Introduction p. 1, Conclusion p. 31, References p. 33, Appendix p. 35 (the PDF has 40 pages including 5 of front matter) | pp. 6 to 40 |

## 3. What the reference does well (keep)

- Signposting: a roadmap paragraph at the end of the introduction, and a sentence before each table saying what it will show.
- Literature organised by strands and ending on the gap the thesis addresses.
- A numbered list of the scenarios assessed.
- Each model defined with its equation, symbols explained directly after, and the estimation window stated.
- Table notes giving scaling and the sign convention.
- Results text that ties each finding back to earlier work and offers a reason for a difference.
- Limitations and future work in the final section.

## 4. What does not work (do not reproduce)

| Defect in the reference | Where | My chapters affected | What I do instead |
|---|---|---|---|
| Roadmap says "section 6" for the conclusion, which is section 5; "four distinct sets" followed by three | pp. 8, 17 | Ch. 1 (not drafted yet), cross-references everywhere | Cross-references are `\ref` labels; counts are checked in the consistency gate |
| Diebold-Mariano equation sets a loss differential equal to zero, confusing the statistic with the null; sign convention flips between tables; significance claimed at 10% and 15% | pp. 21 to 28 | Ch. 5, all tables in Ch. 6 | Null and statistic in separate equations; one sign convention (richer minus baseline, negative is better); one test level declared in advance; intervals and labelled p-values |
| Same-term slips ("FiGAS, also known as FiGAS"), GARCH(1,1) equation with the wrong lag structure, misspelled heading, "this paper" and "this thesis" mixed | pp. 15, 18, 5 | Ch. 3 to 6 | One voice ("I"); equations re-derived from code; spell check before commit |
| Citation of the DM test dated 1996 | p. 33, 39 | Ch. 5, bibliography | Kept `[UNVERIFIED]` until checked against a registry |
| Outlier rule (three standard deviations) removes observations with no sensitivity analysis; estimation choices justified by "it is plausible that" | pp. 17, 21 | Ch. 3, 4 | Every data and estimation choice stated with its reason and what was not examined |
| Results tables mix scaled numbers without a stated sign, no interval or detectability | pp. 25 to 35 | Ch. 6 | Estimate, SE, 95% interval, n, labelled p-value, minimum detectable difference, sidedness label |
| Reference export noise in the bibliography ("Publisher:", "_eprint:") | pp. 38, 39 | Bibliography | Clean BibTeX entries |

## 5. Structure and tone (summary)

Five chapters: Introduction, Literature Review, Data and Methodology, Empirical Results, Conclusion; then References and an Appendix. Roughly 8,000 to 9,500 words. Voice mixes "we", "this paper", "this thesis" and "the author"; mine uses "I" throughout (see the style guide). The reference reports tests with t-statistics in brackets and the language "outperforms at the 5% level"; mine reports intervals and uses the approved wording in `scripts/check_wording.py`.
