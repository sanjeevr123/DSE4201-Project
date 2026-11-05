# Citation audit (Phase 6, first pass, 2026-11-04)

Method, fixed in advance by the standing rule: a specific finding is cited only at the level at which I read it. **Registry**: the Crossref record (or, where Crossref has none, an OpenAlex index record) matches author, title, journal, year, volume, issue and pages. **Abstract**: an abstract was retrieved and read (OpenAlex, RePEc IDEAS). **Full text**: the text was read, with the version and the parts read stated. Scripts: `scripts/lit_crossref_search.py`, `scripts/lit_verify.py`, `scripts/lit_build_matrix.py`. Results: `notes/literature_matrix.csv` (one row per source), `notes/literature/registry_check.csv`. Sources used for checking: Crossref API, OpenAlex API, RePEc IDEAS, arXiv, NBER, open-access repositories. Downloaded PDFs were treated as untrusted data and read with an isolated interpreter; none is committed.

## Result

| Level reached | Sources |
|---|---|
| Registry + abstract + full text (version stated) | Ardia et al. 2018 (published text, read in part), Giacomini-White 2006 (BC working paper 572), Clark-McCracken 2001 (conference version), Clark-West 2007 (NBER TWP 326), McCracken 2020 (St. Louis Fed WP, in full), Patton-Ziegel-Chen 2019 (arXiv 1707.05108), plus Zhu-Timmermann (arXiv preprint, full text, no registry record) |
| Registry + abstract | 35 others, including Fortin et al., Paolella et al., Pelletier, Santos et al., Kole et al., Engle, Bollerslev, Hamilton, Lakens, Hoenig-Heisey, Nosek et al., Abadie, Altman-Bland, Ioannidis et al. |
| Registry only | Harvey-Leybourne-Newbold 1997 (no abstract exists on any index reached), Christoffersen 1998 (abstract not retrieved), Holm 1979 (OpenAlex index record only; issue number not confirmed) |
| Not verified | Acerbi-Szekely 2014 (no registry record; secondary descriptions only), Itou-Yoshiba 2025 (not found anywhere) |

42 of 43 records matched on all six fields automatically; the 43rd (Hansen-Lunde-Nason 2011) matched on every field except the author list, which both registries lack, and I confirmed the authors on RePEc. I also read every title myself.

## Corrections to what the repo, the plan and my earlier drafts said

1. **Ardia et al. (2018).** The abstract and p. 735 of the full text say Markov-switching GARCH models give more accurate VaR, ES and left-tail forecasts than their single-regime counterparts, especially for stock returns, with larger improvements when switching is added to simple specifications (GARCH-Normal). The repo's "does not uniformly dominate" (in `output/literature_positioning.md`) is **unsupported and deleted**. The update's sentence "regime gains are larger against simple baselines" is **supported at full-text level** (p. 735) for single-regime GARCH specifications; it is not a claim about a pooled normal. A 2021 blanket erratum for competing-interest statements does not affect the results.
2. **McCracken (2020).** His counterexample concerns a **fixed** estimation window (one estimate for all forecast origins). He states that for **rolling** windows Theorem 4 of Giacomini-White "remains valid". The plan's section 2.A.4 described the result without this distinction; the thesis must state it correctly. Zhu-Timmermann concern the **conditional** (martingale-difference) null of the GW test and hold for rolling and expanding windows; this bears on the secondary conditional test, not on the primary unconditional comparison.
3. **Diebold-Mariano** is 1995, *J. Business & Economic Statistics* 13(3), 253-263 (the reference thesis's 1996 is wrong; the plan's 1995 is right).
4. **Patton-Ziegel-Chen** is arXiv 1707.05108 (my recollection of the number was wrong). Eq. (6) is the FZ0 loss and equals `src/engine.py::fz0`.
5. **Kinlaw et al. (2021)**, previously "no registry match": found, *J. Portfolio Management* 47(8), 124-137 (SSRN 3781844).
6. **Itou and Yoshiba (2025)** cannot be found: cut.
7. **Santos et al.**: the abstract does not support "constant-correlation multivariate usually worse than univariate". **Brooks-Persand** and **McAleer-da Veiga**: the abstracts do not support "no clear preference between multivariate and univariate" (they concern sensitivity to the evaluation measure, and too many or too few VaR violations). **Paolella et al.**: the abstract does not say whether volatility and correlation are separated. **Chua et al.**: the +76% and -17% figures are not in the abstract. **Baele et al.**: the abstract does not support calling the stock-bond correlation a "slow macro state". None of these may be used.
8. **Zhu-Timmermann** is an arXiv preprint (2006.03238). The Festschrift chapter at DOI 10.1108/S0731-90532021000043A006 is a different paper ("Gains from switching between forecasts").
9. Print years: Santos et al. 2013 (online 2012); Brooks-Persand 2003 (online 2002); Connolly et al. 2005. Campbell-Pflueger-Viceira is *J. Political Economy* 128(8), 3148-3185. A 2021 correction note exists for Fissler-Ziegel (*Annals of Statistics* 49(1), 614).
10. **Newey-West (1994)** proposes a data-driven lag selector. The thesis's lag rule floor(4(T/100)^(2/9)) is a rule of thumb; I have not confirmed that this formula appears in that paper, so it is not attributed to it.

## What the chapters may and may not cite

- **May cite, for the stated finding:** every row of the matrix at registry + abstract level or higher, for what the "main_result" column states and nothing beyond it.
- **May not cite for the definition or critical values:** Acerbi-Szekely (2014). The thesis defines Z2 itself, states its sign convention, and uses simulation p-values.
- **Methods claims that matter most:** Giacomini-White, Clark-McCracken, Clark-West, McCracken and Patton-Ziegel-Chen are now read at full-text level, but in working-paper or preprint versions for four of them; the published versions are on `notes/outbox/05_library_requests.md`.

## Still open

Full text of Fortin et al., Paolella et al. and Pelletier (closed access), Christoffersen (1998), Holm (1979, issue number), published versions of the three nested-model papers, Acerbi-Szekely. All are in `notes/outbox/05_library_requests.md`.


## Update 2026-11-04: two papers supplied by the author
- **Giacomini and White (2006), published Econometrica text:** read in full. The statements used in Chapter 5 are confirmed (forecasting method as the object; rolling and fixed windows; nested and non-nested; unconditional test is Diebold-Mariano, Theorem 4; HAC allowed in the conditional test, Comment 5).
- **Acerbi and Szekely, MSCI Research Insight (27 Oct 2014):** read in full. Z2 is defined with ES as a positive loss, so my Z2 (returns, negative ES) has the **opposite sign**; the thesis now says so. The paper reports critical values (Table 4) and simulated p-values (eq. 12). It is a white paper, not the Risk 27(11) article, which remains unchecked; the bibliography cites the white paper.

## Update 2026-11-04 (second batch supplied by the author)
- **Clark and West (2007), published text:** read in full. The Chapter 5 statement is narrowed: the adjusted statistic is for nested linear models under squared-error loss, with near-normality inferred from tabulated Clark-McCracken quantiles and simulation (sizes 0.05 to 0.10 at nominal 0.10), not proved.
- **Clark and McCracken (2001), June 2000 working paper:** read in full. Supports: non-standard limits when the evaluation sample is a non-vanishing share of the estimation sample, and undersized rejection rates when normal critical values are used for post-sample tests of nested linear models. Published version unread.
- **Paolella, Polak and Walker (2019), SFI working paper 19-27:** read in full. Closest design to RSC: GARCH margins that do not depend on the regime and regime-specific correlation matrices. They find that VaR accuracy is driven mainly by tail heaviness, not by correlation dynamics. They score with log scores and Christoffersen backtests, not FZ0 and DM tests. The claim 'does not separately test volatility and correlation regimes' is replaced by the narrower, supported statement above; the published text is unread, so Chapter 2 cites the paper only for what the working paper says.

## Update 2026-11-05 (third batch supplied by the author)
- **Fortin, Simonato and Dionne:** two working-paper versions read in full (SSRN June 2018; June 2021). Chapter 2 describes the 2021 version (weekly, 1,905 forecasts, 1% and 2.5%, Patton-Ziegel-Chen loss, Giacomini-White, MCS) and states that the published IJF text is unread. Bibliography first name corrected to Alain-Philippe.
- **Pelletier:** the May 2003 working paper read in full; published 2006 text unread. Chapter 2 states what the working paper contains and that I found no out-of-sample or VaR/ES evaluation in it.
- **Christoffersen (1998):** published text read in full; pages 841-862 added to the bibliography. The Chapter 5 statement LR_cc = LR_uc + LR_ind is confirmed (conditioning on the first observation).
- **Baele, Bekaert and Inghelbrecht (2010)** and **Campbell, Pflueger and Viceira (2020):** read in full. They disagree on the drivers of the stock-bond correlation. The earlier claim that the correlation is a slow macro state is therefore NOT supported as stated; Chapter 2 now reports the disagreement and Chapter 8's argument about a slow signal is hedged to match. Both studies end before 2012 and none forecasts risk.
- Four bibliography entries added for works cited only through Fortin et al. or abstracts: Brooks-Persand, McAleer-da Veiga, Kole et al., Hansen-Lunde-Nason (the last two read at abstract level).
- Still open: published texts of Fortin et al. (IJF 2023) and Pelletier (2006); Paolella et al. published; Holm (1979); Harvey-Leybourne-Newbold; Kinlaw et al.; Chua et al.
