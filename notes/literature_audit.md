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
