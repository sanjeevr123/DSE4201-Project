# Further Exploration: Research-Backed Suggestions

**Regime-Switching Risk Models for ETF Portfolios.** Prepared for the discussion with Prof. Seo.
Written from web research (October 2026) plus the pilot and exploration results in this repo. No new backtests were run and 2020-2025 was not touched.

**How to read the evidence labels.** Search tools returned abstracts, listings and secondary summaries, not full papers. Every reference in Section 6 is tagged *abstract-level* (confirmed from an abstract or bibliographic record) or *secondary* (known only from a summary of the paper). Anything I could not confirm is marked **UNVERIFIED**. "Inference" marks my own reasoning, which the literature does not establish.

**Interpretation of the supervisor's points (revised).** Prof. Seo's first point offers *two alternative routes*, and the task is to see which works better:
- **Route M (multivariate):** a more robust dependence measure, estimated jointly for all N assets, from which the covariance or correlation matrix is built, instead of the ordinary sample correlations.
- **Route P (pairwise on a chosen pair):** keep ordinary correlation but pick two of the assets and let only that pair's correlation switch with the regime.

Section 2 specifies both and a head-to-head comparison. (An earlier draft of this document read "pick 2" as "choose two measures"; that was a misreading.)

---

## 1. Executive summary: five ranked recommendations

1. **Fix a likely design confound before running anything new (highest value).** Our regime models (A-D) use a *constant* covariance inside each regime, while the benchmarks that beat them (GARCH-t, DCC-t) update every day. So regime models lose partly because they ignore within-regime volatility clustering, not necessarily because regimes are useless. The literature's best regime evidence puts the regimes *on top of* GARCH dynamics (Pelletier 2006; Ardia et al. 2018/2019). Add a **GARCH-margins + regime-switching correlation** arm, so that volatility dynamics are identical in B' and D' and only the correlation treatment differs. (Inference, grounded in the papers above; Section 3, finding F2.)
2. **Compare the supervisor's two routes head to head (Section 2).** Route M: a robust, jointly estimated correlation matrix for all assets (primary candidate: the Kendall's-tau rank-based matrix). Route P: let only one pre-chosen pair switch (SPY-IEF, the stock-bond pair, chosen by theory, not by scanning the data). Both are scored against the same reference (model B) and against DCC-t, with a pre-declared decision rule. Caution: outlier-trimming estimators such as MCD remove the stress days that the regime contrast depends on.
3. **Validate with a small, pre-sequenced package, all on data through 2019:** reproduce the primary specification with a second data vendor, report it over three non-overlapping sub-periods, keep the 1992-2019 fund proxies as supplementary, and control the family-wise error with Holm plus Hansen's SPA/model confidence set. Then freeze the specification and look at 2020-2025 once (Section 4).
4. **Use the established three-layer design for the 2020-2025 question (Section 4.2).** Choose settings by rolling-origin plus blocked cross-validation on 2005-2019; quantify selection bias (SPA/model confidence set, probability of backtest overfitting); freeze the specification; then run it once on 2020-2025. Pre-register D vs B as the primary test, add a *conditional* predictive-ability test (Giacomini-White) conditioned on the stock-bond correlation, and analyse 2022 directly. Report the minimum detectable effect next to every result.
5. **Position the thesis as a controlled ablation plus a power analysis.** The null results are consistent with published work (Santos et al. 2013: DCC-t best; Fortin et al. 2023: mostly no significant difference; Boyer et al. 1999: "correlation breakdown" can be a selection artefact). The novelty is the clean B-vs-D contrast with power reported, not another regime model.

---

## 2. Workstream 1: the dependence measure (two routes, compared head to head)

**Why change anything.** Average pairwise sample correlation (a) cancels across asset types (Treasuries' correlation fell in stress while risk assets' rose), (b) is sensitive to outliers and fat tails, and (c) is biased upward in high-volatility samples (Forbes and Rigobon 2002; Boyer et al. 1999).

### 2.1 Route M: a robust joint estimate for all assets

Candidates for building the correlation matrix R (the covariance is then D·R·D with regime-weighted volatilities D):

| Estimator | What it does | Strength | Weakness for *our* use | Cost |
|---|---|---|---|---|
| **Kendall's-tau rank correlation matrix**, R = sin(πτ/2) (Lindskog, McNeil & Schmock) | Uses only the ranks of returns; recovers the Pearson correlation under an elliptical distribution; robust to heavy tails and heteroskedasticity | Does not discard extreme days, it limits their *influence*; no variances needed | Not guaranteed positive semidefinite (needs a nearest-PSD repair); regime-probability weights need a weighted tau (O(T²), fine for T = 1260) | Medium |
| **Ledoit-Wolf shrinkage** (2004) | Shrinks the sample covariance toward the identity with an optimal weight | Always well-conditioned; simple | Shrinks regime-specific matrices toward a common target, which *reduces the D-vs-B difference we are trying to detect* (inference); designed for large N | Low |
| **Minimum Covariance Determinant (MCD)** (Rousseeuw) | Estimates covariance from the most "central" subset of observations | Very robust to outliers | **Throws away the stress days** that define the stress regime (inference); not designed for soft regime weights | Medium |
| **Tyler M-estimator, optionally with shrinkage** | Scale-free robust estimator for heavy tails | Good for heavy tails; combined versions exist | More complex; no regime weighting out of the box | High |
| *Descriptive summaries only:* Gaussian total correlation -½·log det R (**sign-blind**: it is identical if an asset's sign is flipped, so it cannot see a stock-bond sign change; checked on SPY/IEF/GLD 2005-2019, where it was highest in the calm, strongly hedged 2012 and lowest during the 2013 taper tantrum); absorption ratio (Kritzman et al.); distance correlation; lower-tail dependence (Ang-Chen exceedance correlation; **sign-aware but too sparse**: on SPY/IEF 2005-2019 only 22 days fall in the joint lowest 10% and 6 in the lowest 5%; conditioning on the SPY tail alone gives 191 days at 5% with a 90% interval of -0.49 to -0.10) | One-number multivariate summaries | Useful for plots and regime diagnostics | They summarise dependence; they do not give a covariance matrix to forecast with | Low |

**Recommended Route M estimator: the Kendall's-tau matrix** (with Ledoit-Wolf as a single secondary check inside the same comparison). Reason: it is the robust option that does not delete the stress observations, and it addresses fat tails directly. Robustify the *correlation* only: keep the regime-weighted standard deviations as volatilities, because robust (trimmed or MAD-based) volatilities would understate tail risk and bias VaR/ES downward (inference).

### 2.2 Route P: pairwise correlation on two chosen assets

Keep ordinary correlation, but let **only one pair's correlation switch by regime**, with all other correlations pooled ("D_pair"). It sits between B (no correlation switching) and D (every pair switching).
- **Pair choice rule (pre-declared, not data-driven):** the **stock-bond pair SPY-IEF** in the primary universe, because the literature ties the sign change in this pair to inflation and growth uncertainty (Campbell et al. 2017; Brixton et al. 2023; Baele et al. 2010) and it is the thesis's motivating case. Other universes get their pair fixed in the specification *before* running. Scanning all N(N-1)/2 pairs and picking the best would add a hidden multiple-testing family.
- **Why it might work better:** one switching parameter instead of N(N-1)/2 per regime gives more power if the real shift is in that pair, and Pelletier (2006) reports that regime-switching correlation models struggle once N exceeds 3 without parameter restrictions (secondary).
- **Why it might not:** if the shift is spread over several pairs, D_pair misses it.

### 2.3 Head-to-head design ("which works better?")

All arms use the same regime signal (the SPY HMM as primary), window, refit and the same data. The GARCH-margin version from Recommendation 1 is run as a second layer.

| Arm | Volatility | Correlation |
|---|---|---|
| **B** (reference) | regime-dependent | pooled |
| **D** (current) | regime-dependent | all pairs switch, sample estimate |
| **D_M** (Route M) | regime-dependent | all pairs switch, Kendall's-tau matrix |
| **D_P** (Route P) | regime-dependent | only SPY-IEF switches, sample estimate |
| DCC-t, GARCH-t | benchmarks | |

Pre-declared criteria, in order of weight:
1. **Forecast accuracy:** FZ0 difference vs B (and vs DCC-t), Diebold-Mariano with HAC errors. The two primary tests are D_M vs B and D_P vs B, Holm-adjusted over these two.
2. **Power:** repeat the pilot's WP2 simulation for D_M and D_P across scenarios S0-S3. D_P should win when the true shift sits in the SPY-IEF pair, D_M when it is diffuse. This tells us *when* each route is the right tool, which a single real-data result cannot.
3. **Stability:** variation of the estimated correlations across the monthly refits; share of Kendall matrices needing a PSD repair; a stress test that injects outliers.
4. **Regime-detection:** whether a signal built from each route's dependence measure flags the named episodes (2008, 2011, 2013, 2015-16, 2018 Q4), as in the exploration timelines.
5. **Interpretability and cost.**

**Decision rule (fixed in advance).** Choose the route with the lower mean FZ0 relative to B on the 2005-2019 development folds. If neither beats B significantly, report "no detectable gain from either route" together with each route's minimum detectable effect, and keep D_P as the default because it is simpler. This is a falsifiable plan: it can come out in favour of either route or neither.

**What I expect (inference, not a result):** differences will be small (the exploration found D-B within ±0.01 FZ0), D_P will have the power advantage in the stock-bond case, and D_M will be more stable but may blunt the stress contrast. Only the comparison can say.

**Control for the Forbes-Rigobon bias.** Report every regime-conditional correlation both raw and after standardising returns by regime volatility, and treat the adjusted figure as a sensitivity bound (Corsetti et al. 2005 show the adjustment depends on assumed shock variances).

**Baseline for comparison:** average pairwise sample correlation (current D) and DCC-t.

---

### 2.4 Results of plan steps 1, 2 and 2B (implemented; SPY/IEF/GLD, forecasts 2010-2019, data through 2019 only)

Code: `src/explore_routes.py`, `scripts/explore_08..11_*.py`; tables in `output/explore/routes/`; figure `fig_routes_G_power.png`. Checks: layer-1 B and D reproduce the saved backtest bit for bit; the power harness reproduces the pilot's WP2 D-vs-B statistics to 1e-6 on the same simulated data; 9 new unit tests pass. Signs: negative = first model better. Pre-declared primary tests: D_M vs B and D_P vs B, alpha = 5%, full window, SPY HMM, Holm over the two. Everything else is secondary and unadjusted.

**Step 1: GARCH margins + regime correlation.**

| Model (alpha = 5%, full window) | FZ0 | Hit rate | Kupiec p |
|---|---|---|---|
| B (static regime vol, pooled corr) | -4.598 | 3.7% | 0.002 |
| D (static, all correlations switch) | -4.601 | 3.6% | 0.001 |
| CCC (GARCH margins, constant corr) | -4.624 | 5.0% | 0.94 |
| RSC (GARCH margins, regime corr), Gaussian | -4.628 | 4.7% | 0.53 |
| RSC, Student-t | -4.634 | 5.3% | 0.46 |
| DCC-N / DCC-t / GARCH-t (benchmarks) | -4.628 / -4.633 / -4.632 | 5.0% / 5.6% / 5.5% | 0.99 / 0.15 / 0.23 |

- Adding GARCH margins moves the loss by -0.025 to -0.026 (CCC vs B: t = -1.46, p = 0.14; RSC vs D: t = -1.51, p = 0.13) and fixes calibration: the static regime models are too conservative at 5% (hit rate 3.6-3.7%, Kupiec rejects), while all GARCH-margin arms are close to 5%.
- RSC is indistinguishable from DCC (vs DCC-N: +0.0001, p = 0.99; Student-t RSC vs DCC-t: -0.0008, p = 0.94) and from GARCH-t (-0.0025, p = 0.86). So on this universe the earlier "regime models lose to GARCH/DCC" gap (about 0.03) disappears once the regime model has GARCH volatility. The gap was not statistically significant on this universe even before (D vs GARCH-t: p = 0.18), so the claim rests on the point estimates here; the universes where the loss was significant (U3, U8, U10) are the place to confirm it.
- The correlation channel with GARCH margins (regime vs constant correlation) has a consistent negative sign but is not significant: RSC vs CCC -0.0040 (p = 0.31), Student-t -0.0041 (p = 0.26); the minimum detectable difference here is about 0.011.

**Step 2: Route M vs Route P.**

| Test (alpha = 5%, full window) | Mean FZ0 difference | t | p | Holm (2 primary tests) |
|---|---|---|---|---|
| **D_M vs B (primary)** | -0.0054 | -1.46 | 0.145 | 0.29 |
| **D_P vs B (primary)** | -0.0009 | -0.90 | 0.37 | 0.37 |
| D vs B (current design) | -0.0031 | -0.82 | 0.41 | secondary |
| D_M vs D (Kendall vs sample) | -0.0023 | -1.62 | 0.11 | secondary |

- **Neither primary test is significant.** The pre-declared decision rule therefore gives "no detectable gain from either route", with D_P kept as the default route.
- **Route M's small edge is specific to the static layer.** In the static layer D_M has the lower mean loss (also at 2.5%: D_M vs B -0.0147, p = 0.006; the 2016-2019 pseudo-holdout agrees). That edge vanishes once GARCH margins are used: RSC_M vs RSC_S is 0.0000 (p = 0.98). It is also not a power advantage (below). My reading (inference): in the static layer, regime-specific sample covariances are contaminated by stress-day outliers, which a rank-based estimator limits; the GARCH standardisation already removes most of that.
- **Route P captures only part of the effect, but measures it more precisely.** D_P vs B is -0.0009 (about a third of the all-pairs effect), with a minimum detectable difference of 0.0027 against 0.0104 for D_M.
- A sensitivity provider (realised-volatility rule instead of the HMM) gives the same direction: D_M vs B -0.0034 (p = 0.32), D_P vs B +0.0002 (p = 0.89) at 5%.

**Step 2B: power and size on the pilot DGP (200 replications per cell; 95% intervals about +/-6 points at 25%).** One-sided 5% DM test, VaR/ES 5%:

| Scenario | D vs B | D_M vs B (Route M) | D_P vs B (Route P) |
|---|---|---|---|
| S0 null (false-positive rate) | 5.0% | 5.0% | 3.0% |
| S1 moderate breakdown | 25.5% | 24.5% | **35.0%** |
| S2 strong breakdown | 52.5% | 53.5% | **78.5%** |
| S3 flight-to-quality | 3.5% | 2.5% | **11.0%** |

- Route P has clearly higher power: +10 points in the moderate case and +25 points in the strong case. Route M adds nothing over the plain all-pairs test.
- Caveat (important): the simulated shifts are largest in the equity-bond pair by construction, which is also the real-world motivating case. The simulation therefore shows the gain from testing the right pair, not that a single pair is generally better. If the true shift were spread evenly across pairs, Route P would lose its advantage (not simulated).
- At alpha = 2.5% every route has lower power (S2: 25% for D and D_M, 50% for D_P).
- Under the null, D_P rejects in the wrong direction 11% of the time (5% expected), a mild sign that an unneeded switching parameter costs some accuracy.

**What this changes.**
1. The primary confirmatory contrast should use **GARCH margins (layer 2)**, where models are calibrated and competitive with DCC, with Route P (SPY-IEF) as the default switching route.
2. Kendall's tau does not earn a place in that primary design; keep it as a robustness check.
3. The correlation channel is still not detectable on this universe at 2010-2019, consistent with the pilot's power finding; Route P should be the most informative test available on the hold-out.
4. Open items: confirm the confound explanation on U3, U8 and U10 (about 30 seconds each); power simulation for the GARCH-margin layer needs a DGP with GARCH dynamics (the pilot DGP has none).

---

## 3. Workstream 3 first: what the literature says (so the other two build on it)

Detailed table of the papers most relevant to the design. "Headline derivation" is how the result is obtained.

| Paper | Question and data | Model / how the headline is derived | Conclusion | Limitation | Insight for us | Evidence |
|---|---|---|---|---|---|---|
| Hamilton (1989), *Econometrica* 57(2) | Do growth rates shift between discrete states? US real GNP, postwar | Markov-switching autoregression; states inferred probabilistically; ML estimation | Recurrent switches between positive and negative growth | Replication (Boldin 1996) found sensitivity to sample and starting values (secondary) | Use multiple HMM starts and report fit stability (we warm-start; add a stability audit) | abstract-level |
| Ang & Bekaert (2002), *RFS* 15(4) | Value of regimes in international allocation; US, UK, German equities | Regime-switching with a high-volatility, high-correlation state; dynamic portfolio choice | Correlations rise in bad times; ignoring regimes costs little for equity-only portfolios but more when a risk-free asset is available | Utility-based, not tail-risk forecasting; 1999 and 2002 versions differ in magnitude | Our diversified (bond-containing) universes are where regimes should matter; our result there is null | abstract-level |
| Ang & Chen (2002), *JFE* 63 | Are correlations asymmetric (higher in down markets)? US equity portfolios | Exceedance correlations and a formal test (H statistics); compare with model-implied values | Down-market correlations exceed normal-model values by ~11.6%; regime-switching models capture asymmetry best | Equity-only | Exceedance correlation is a ready-made tail measure (Section 2.1, descriptive summaries) | abstract-level |
| Longin & Solnik (2001), *JF* 56(2) | Does correlation rise in volatile markets? Five largest markets, monthly 1958-1996 | Extreme value theory for tail correlation | Normality rejected for the negative tail, not the positive; correlation tracks bear *trend*, not volatility per se | Monthly data | Supports asymmetry, and warns against reading volatility as the driver | abstract-level |
| Forbes & Rigobon (2002), *JF* 57(5) | Is "contagion" real or a volatility artefact? 1997 Asia, 1994 Mexico, 1987 US | Adjust correlations for the volatility bias | After adjustment, almost no contagion, only interdependence | Assumes a particular structure of shocks | Our correlation shares in stress may be inflated by construction | abstract-level |
| Corsetti, Pericoli & Sbracia (2005), *JIMF* 24(8) | Are the "no contagion" results robust? 17 markets around 1997 Hong Kong | Factor model; vary the variance of country-specific shocks | Results hinge on that variance assumption; contagion found for 5 of 17 under plausible values | Single episode | Report adjusted correlations as bounds | abstract-level |
| Boyer, Gibson & Loretan (1999), Fed IFDP 597 | Is "correlation breakdown" real? Analytic, numerical, empirical | Show breakdown can arise from selecting on volatility with constant true correlation | Breakdown can be a statistical artefact | Not a full structural model | Condition on regimes carefully; compare with constant-correlation nulls | abstract-level |
| Engle (2002), *JBES* 20(3) | A tractable time-varying correlation model | Univariate GARCH + dynamic correlation, estimated in two steps | Flexible and simple to estimate | Single smooth process, no regimes | Our DCC-t benchmark follows this | abstract-level |
| Santos, Nogales & Ruiz (2013), *JFEc* 11(2) | Univariate vs multivariate GARCH for portfolio VaR; simulated + real | Out-of-sample comparative predictive ability tests | Multivariate beats univariate out of sample; DCC with Student-t errors best on real portfolios | VaR focus, no regime models | Matches our finding that DCC-t is the model to beat | abstract-level |
| Pelletier (2006), *J. Econometrics* 131 | Regime-switching *correlations* with GARCH margins | Correlation matrix constant within a regime, Markov chain across regimes | Better in-sample fit than DCC; **for more than 3 assets, common parameters must be assumed** (secondary) | Constraint limits performance for large N; in-sample | The model we should add (Recommendation 1); R package RSDC exists (Ardia and Seguin) | abstract-level + secondary |
| Guidolin & Timmermann (2007), *JEDC* 31(11) | Regimes in stock-bond allocation | Multivariate regime switching | Four states (crash, slow growth, bull, recovery) needed for the joint distribution | Allocation, not forecast accuracy | Questions the 2-state restriction; a 3- or 4-state variant is a robustness check | abstract-level |
| Ardia, Bluteau, Boudt & Catania (2018), *IJF*; MSGARCH package (2019, *JSS* 91(4)) | Do Markov-switching GARCH models forecast risk better? Large equity set | Out-of-sample VaR/ES comparison, single-regime vs regime GARCH | Regime GARCH gives more accurate VaR/ES; **gains larger for simple specifications such as GARCH-Normal** | Univariate | A GARCH-t baseline is already strong, so small regime gains are expected | abstract-level |
| Fülle et al. (2024), *J. Forecasting* | Markov-switching copula MGARCH for tail risk | Ten years of daily returns; compare with MGARCH and constant-copula MGARCH | Outperforms those benchmarks; stronger when assets are similarly risky | Not compared with DCC specifically | Indirect support; gains are larger in risky-asset portfolios (our U8, U10) | abstract-level |
| Fortin, Simonato & Dionne (2023), *IJF* 39(1) | Univariate vs multivariate for one-week ES; Fama-French and momentum factors | Joint VaR/ES scoring | Mostly no significant difference between approaches (from this repo's literature briefing) | Weekly data, equity factors | The closest published null; shows why power must be reported | abstract-level for the question; the findings are **UNVERIFIED** this session (publisher page returned 403) |
| Campbell, Sunderam & Viceira (2017), *Critical Finance Review* 6(2) | Why does the stock-bond covariance change? US 1953-2009 | Term-structure model with a time-varying nominal-real covariance | Covariance slightly positive on average, high in the early 1980s, negative in the 2000s | Model-based | The sign is a slow-moving state tied to inflation risk | abstract-level |
| Baele, Bekaert & Inghelbrecht (2010), *RFS* 23(6) | What drives stock-bond comovement? Dynamic factor model | Fundamentals and liquidity proxies in a factor model | Macro fundamentals explain little; liquidity matters more; the model fits covariances poorly | Model weak exactly where we need it | Do not expect a simple macro state to be easy; hold expectations modest | abstract-level |
| Brixton et al. (2023), *JPM* 49(4) | Drivers of the stock-bond correlation | Correlation depends on the relative volatility of growth and inflation and their correlation | Explains ~70% of long-term variation, less of short-term swings; a move from -0.5 to +0.5 raises 60/40 volatility ~20% (secondary) | Weak at short horizons | A *slow* state, not a fast regime | secondary |
| Cieślak & Pflueger (2023), *Annu. Rev. Financ. Econ.* 15 | Inflation and asset returns | "Good" (demand) vs "bad" (supply or cost-push) inflation | Different inflation sources change stock-bond sign | Review | Candidate macro state variable for a later design | abstract-level |
| Patton, Ziegel & Chen (2019), *J. Econometrics* 211(2) | Joint VaR/ES modelling | FZ0 loss from joint elicitability; semiparametric dynamics | ES-VaR models beat GARCH and rolling windows on four indices | Univariate | Our scoring rule is the right one | abstract-level |
| Fissler & Ziegel (2016), *Ann. Statist.* 44(4) | Is ES elicitable? | Higher-order elicitability | (VaR, ES) is jointly elicitable under mild conditions | Theory | Justifies FZ0 | abstract-level |
| Giacomini & White (2006), *Econometrica* 74(6) | Conditional predictive ability | Test whether a model beats another *given* current information | Allows choice of the best forecast for a given state | A 2020 Fed working paper finds it correctly sized but typically low in power (secondary) | Use it with the stock-bond correlation as conditioning variable | abstract-level + secondary |

**Papers listed but not tabulated** (relevance noted): Kritzman, Li, Page & Rigobon (2011), *JPM*, absorption ratio (secondary: TradingView and fund-industry pages, not the paper); Székely, Rizzo & Bakirov (2007), *Ann. Statist.* 35(6), distance correlation (abstract-level); Laloux et al. (1999), *PRL*, noise dressing (abstract-level); Hansen, Lunde & Nason (2011), *Econometrica*, model confidence set; Hansen (2005), *JBES*, SPA test; Romano & Wolf (2005), stepwise multiple testing (all secondary; implemented in the Python `arch` package per its documentation); Nystrup, Hansen, Madsen & Lindström, regime-based vs static allocation (secondary: thesis listing); Fox, Sudderth, Jordan & Willsky (2008), sticky HDP-HMM, ICML (abstract-level); Wergé (2021), arXiv 2107.05535, sticky-HMM asset-independent regimes (abstract-level); David & Veronesi (2013, *JPE* per a secondary summary), learning about inflation regimes; Kinlaw, Kritzman, Page & Turkington (2021), "The Myth of Diversification Reconsidered", *JPM* 47(8) (abstract-level); Paolella, Polak & Walker (2019), *J. Econometrics* 213(2), regime-switching dynamic correlations with fat tails (abstract-level). Hafner & Franses (generalised DCC) and Guidolin's 2006 VaR/ES comparison (CEPR DP4645; author attribution unclear from the listing) were **not confirmed**.

### Synthesis

**Where the literature agrees.**
- Correlations differ across market states and are asymmetric in equity portfolios (Ang-Bekaert, Ang-Chen, Longin-Solnik).
- Naïve conditional correlations are biased by volatility selection (Forbes-Rigobon, Boyer et al.), though the correction is itself assumption-dependent (Corsetti et al.).
- Joint VaR/ES scoring with FZ0 is the correct evaluation (Patton et al.; Fissler-Ziegel).

**Where it disagrees.**
- Whether regimes add forecast accuracy over strong single-regime models. Univariate regime-GARCH helps most when the baseline is simple (Ardia et al.). Multivariate evidence is thin and mixed: regime copulas beat constant-copula MGARCH (Fülle et al.), DCC-t beats univariate (Santos et al.), and one-week ES shows mostly no difference (Fortin et al., unverified).
- Whether the stock-bond sign is predictable: models tie it to slow macro state (Campbell et al., Brixton et al., David-Veronesi), while Baele et al. find fundamentals explain little.

**How our null results compare.**
- Regime models lose to GARCH-t/DCC-t: consistent with Santos et al. and with Ardia et al.'s observation that regimes help less against a rich baseline.
- No detectable correlation channel: consistent with Fortin et al. (unverified), Boyer et al., and Forbes-Rigobon.
- **Methodological flags (inference):**
  - **F1.** The equity-only HMM signal cannot see bond-led shocks (shown in our taper-tantrum result).
  - **F2.** Constant within-regime covariance versus daily-updating benchmarks (Recommendation 1).
  - **F3.** The stock-bond sign is a slow macro-driven state, so a fast volatility regime is mismatched to that channel.
  - **F4.** A 2-state restriction when Guidolin-Timmermann find four states for stock-bond joint behaviour.
  - **F5.** With a 5-year window, each regime has few stress days to learn from.

---

## 4. Workstream 2: robustness across periods and data sources

Everything below runs on data through 2019-12-31 unless stated. Each option says what failure it detects.

| Option | Tests for | Cost | New multiple-testing family? | Rank |
|---|---|---|---|---|
| **Second vendor reproduction of the primary spec** (e.g., Tiingo, or CRSP/WRDS if the university provides it; **availability not verified**) | Data error; dividend-adjustment differences | Low | No (same spec) | 1 |
| **Three non-overlapping sub-periods** on the primary spec (2010-2012, 2013-2015, 2016-2019), plus a shorter window (e.g., 756 days) that allows forecasts from ~2008 | Period dependence; whether results survive the GFC aftermath | Low | Yes, one small family (3 periods) | 2 |
| **Rolling-origin evaluation** with expanding window | Stability of conclusions to the origin | Medium | Folds into the family above | 3 |
| **Long-history proxies** (done: VFINX/VUSTX 1992-2019) | Whether the effect shows in an era with positive stock-bond correlation | Done | Already logged | Supplementary |
| **Alternative instruments for the same exposure** (index total-return series, futures) | Instrument-specific artefacts | Medium | Yes | 4 |
| **International markets** (e.g., European or Japanese equity/bond series) | Market dependence; whether the stock-bond story is US-specific | High (data and currency issues) | Yes | 5, optional |
| **Different portfolio weights** (60/40, risk parity) | Equal-weight dependence | Low | Yes | 3 |

**Data-source notes.** The only data-quality evidence found was informal. Forum and vendor-community threads report inconsistent Yahoo adjusted closes around dividends, a practitioner check suggests Tiingo follows CRSP adjustment guidelines, and a course data card warns that delisted tickers vanish from free sources (survivorship bias; low risk for large ETFs). Treat these as reasons to run the vendor-reproduction check, not as established facts. FRED (yields) and the Kenneth French data library are standard sources, but their coverage was not checked this session.

**Recommended minimum package (about one week).**
1. Second-vendor reproduction of the primary specification, 2010-2019; require agreement of loss differences within a stated tolerance (e.g., 1e-4, the level used to validate the engine).
2. Three-sub-period table of D-vs-B and DM statistics for the primary spec, plus the 60/40 weighting.
3. Keep the 1992-2019 fund-proxy results as supplementary, with the proxy caveats.
4. Treat everything above as **one robustness family**, pre-declared, Holm-adjusted, and *reported regardless of outcome*.

**"What is looked at when" protocol.**
| Stage | Action | Data touched | Gate |
|---|---|---|---|
| 0 | Supervisor decisions; write the specification | none new | Supervisor sign-off |
| 1 | Vendor reproduction and sub-period package | ≤ 2019 | Results logged, not used to tune |
| 2 | Add the GARCH-margins + regime-correlation arm and the Route M / Route P comparison (Section 2.3) | ≤ 2019 | New specs added to the log before running |
| 3 | **Freeze** the specification (git tag, `docs/preregistration.md` addendum) | none | Written before Stage 4 |
| 4 | Run once on 2020-2025 | 2020-2025 | No re-runs; deviations reported |
| 5 | Post-hoc analyses, labelled exploratory | 2020-2025 | Clearly separated in the write-up |

---

### 4.2 How to treat 2020-2025: the established method and the decision

| Method | What it is | Verdict for this thesis |
|---|---|---|
| Fixed end-of-sample hold-out | Keep the last block untouched | Classical forecasting practice; avoids dependence problems but wastes data (Bergmeir & Benítez 2012) |
| Ordinary k-fold CV | Random folds | Theoretically invalid for dependent data; Bergmeir & Benítez found little practical harm for stationary autoregressive models, but our data are non-stationary with regimes, so do not rely on it (inference) |
| **Blocked CV** | Contiguous blocks as folds | Recommended by Bergmeir & Benítez as a standard for model selection; more robust selection than a single last-block test |
| **Rolling-origin with recalibration and several test periods** | What our walk-forward does | Recommended by Tashman (2000) for efficiency and reliability |
| Purged/embargoed CV | Removes training data overlapping the test labels | Designed for overlapping labels; our one-day-ahead forecasts do not overlap, so not needed (inference; source is a community article) |
| Overfitting diagnostics | Count trials; probability of backtest overfitting (Bailey et al.); SPA/MCS | Needed because simple hold-out is unreliable when many configurations are tried (Bailey et al.); we tried 214+ |

**Best decision (three layers).**
1. **Select** window, refit frequency, number of states, regime signal and Route M vs P using rolling-origin plus blocked CV on 2005-2019 only.
2. **Quantify selection bias:** count every trial, run Hansen's SPA / model confidence set for "does any regime model beat GARCH-t", and report a probability-of-backtest-overfitting style estimate.
3. **Freeze, then run once** on 2020-2025 as the end-of-sample test. Afterwards, report a pooled 2010-2025 walk-forward as a *secondary* result, labelled as partly selected (the 2010-2019 portion informed the choice).

**Why this beats the alternatives.** Using 2020-2025 freely gives about 6 more years (more power, includes 2022) but turns the key episode into evidence that was available when choosing, so it can no longer be called confirmatory. Never using it throws away the one episode the thesis is about. The three-layer design uses cross-validation where tuning happens and keeps the final test unbiased. This is the supervisor's call (brief question 4); the document recommends layer 3 as written.

---

## 5. Answers to the cross-cutting questions

**Are the nulls consistent with the literature or a method problem?** Both. They agree with Santos et al., Boyer et al., and (unverified) Fortin et al. They also point at specific design issues (F1-F5 above). The most fixable one is F2, because it is a clean confound in the A-D ablation.

**Most informative test on a single 6-year hold-out with one structural shift?**
- A single average-loss D-vs-B comparison will have low power (pilot: ~20-25% for a moderate shift at 5-10 years).
- Better: (a) the pre-registered D-vs-B test as the primary result; (b) a **Giacomini-White conditional test** with the lagged stock-bond correlation as instrument, which asks "does D help *when* correlation is positive?"; (c) a focused look at 2022: cumulative loss difference, exceedance clustering (Christoffersen), and Acerbi-Szekely ES statistics for D, B, GARCH-t and DCC-t.
- Report the minimum detectable effect. Note that Giacomini-White tests are reported to have low power (secondary), so frame (b) as supporting.

**Which directions does the literature support, and in what order?**
1. **D (power as headline)**: supported by the unverified Fortin et al. null and by the general power problem. Do first.
2. **A new "B" (macro-state signal, not market signals)**: the literature (Brixton et al., Cieślak-Pflueger, Campbell et al.) ties the stock-bond sign to inflation/growth uncertainty. Market-based signals (MOVE, yield vol) gave no consistent gain in our tests. If a second signal is added, a slow macro variable (e.g., inflation volatility or "good vs bad inflation") is better justified, but needs data not yet collected (e.g., from FRED) and is untested.
3. **A (long history)**: useful as supplementary evidence because it contains the positive-correlation era, but it showed no correlation-channel gain, and the literature says the sign is a slow drift, not a fast regime.
4. **C (equity-heavy universes)**: supported by Ang-Chen and Longin-Solnik (asymmetry in equities) and Fülle et al. (stronger gains in risky-asset portfolios), but off-theme for "diversified portfolio", and our D-vs-B results there changed sign with the signal.

**What would a reviewer raise first?**
1. Regime models use static within-regime covariance, so the comparison with GARCH/DCC is not apples to apples (F2).
2. Many specifications and few corrections; use the pre-declared families plus SPA/MCS for "does any regime model beat GARCH-t" (the `arch` package implements these).
3. One equal-weight portfolio and two tail levels (5% and 2.5%); add 1% only if power allows.
4. A 2-state model on equity returns for a stock-bond question (F1, F3, F4).
5. Estimation uncertainty in the HMM is not carried into confidence intervals (our bootstrap holds regime weights fixed).
6. Data vendor and adjustment issues (addressed by the reproduction check).

---

## 6. Proposed next-step plan (about 4 weeks; effort in working days)

| Step | What | Effort | Depends on |
|---|---|---|---|
| 1 | Implement **GARCH-margins + regime-correlation** arm (RSDC-style): B' (constant correlation) vs D' (regime correlations), identical GARCH margins; compare with DCC-t. Reuse the existing DCC and HMM code, or call the R `RSDC` package | 4-6 | Decision 1 |
| 2 | Implement **Route M** (Kendall's-tau matrix with PSD repair, weighted by regime probabilities) and **Route P** (SPY-IEF-only switching); run the head-to-head of Section 2.3 on 2005-2019, including the WP2 power simulation | 5-7 | Decision 2 |
| 3 | Vendor reproduction + sub-period package (Section 4) | 3-4 | Data access |
| 4 | Add SPA / model confidence set for the regime-vs-benchmark family | 1-2 | None |
| 5 | Specification freeze: write the addendum, tag the commit | 1 | Supervisor sign-off |
| 6 | Single hold-out run + 2022 analysis | 2-3 | Step 5 |
| 7 | Write-up: methods, literature positioning, power section | ongoing | All |

**Decisions needed from Prof. Seo.**
1. Approve adding the GARCH-margins + regime-correlation arm as the primary model contrast (replacing or alongside the static-covariance D-vs-B).
2. Confirm the two-route comparison (robust joint matrix vs one chosen pair), the pair (SPY-IEF) and the robust estimator (Kendall's tau), or name different ones.
3. Confirm the validation package and whether a second vendor (Tiingo, CRSP via the university) is available.
4. Approve the hold-out protocol: three-layer design of Section 4.2 (CV on 2005-2019, selection-bias checks, freeze, single run on 2020-2025 with the conditional test and 2022 analysis).
5. Say whether a slow macro-state variable is in scope, or whether it is a future-work item.

---

## 7. Risks and caveats

- **Multiple testing.** Each new arm and measure adds tests. Pre-declare families, adjust, and report everything tried.
- **Proxy quality.** Fund proxies (VFINX, VUSTX) are not ETFs; vendor checks may not exist for them.
- **Low power.** The tests cannot resolve moderate effects at this sample size; null results are not evidence of no effect.
- **Hold-out contamination.** Any design choice informed by 2020-2025 invalidates it. Keep Stage 3 before Stage 4.
- **Evidence strength.** Most references were checked at abstract level only. Read the primary papers for the five that drive the design (Pelletier 2006; Ang-Chen 2002; Forbes-Rigobon 2002; Santos et al. 2013; Fortin et al. 2023) before citing specifics.
- **My inferences** (F1-F5, the choice of Kendall's tau and of the SPY-IEF pair, the expected outcome of the comparison, the Forbes-Rigobon control) are reasoned, not published results about this design.

---

## 8. Reference list (all links from the search results; verification level in brackets)

- Hamilton (1989), *Econometrica* 57(2), 357-384. [abstract-level] https://ideas.repec.org/a/ecm/emetrp/v57y1989i2p357-84.html
- Ang & Bekaert (2002), *RFS* 15(4), 1137-1187. [abstract-level] https://ideas.repec.org/a/oup/rfinst/v15y2002i4p1137-1187.html ; NBER w10080 (2003) https://www.nber.org/papers/w10080.pdf
- Ang & Chen (2002), *JFE* 63, 443-494. [abstract-level] https://ideas.repec.org:443/a/eee/jfinec/v63y2002i3p443-494.html
- Longin & Solnik (2001), *JF* 56(2), 649-676. [abstract-level; method details not retrieved] https://repec.cepr.org/repec/cpr/ceprdp/Dp2538.pdf
- Forbes & Rigobon (2002), *JF* 57(5), 2223-2261. [abstract-level] https://www.nber.org/papers/w7267
- Corsetti, Pericoli & Sbracia (2005), *JIMF* 24(8), 1177-1199. [abstract-level] https://ideas.repec.org/a/eee/jimfin/v24y2005i8p1177-1199.html
- Boyer, Gibson & Loretan (1999), Fed IFDP 597. [abstract-level] https://www.federalreserve.gov/econres/ifdp/pitfalls-in-tests-for-changes-in-correlations.htm
- Engle (2002), *JBES* 20(3), 339-350. [abstract-level] https://ideas.repec.org/a/bes/jnlbes/v20y2002i3p339-50.html
- Santos, Nogales & Ruiz (2013), *J. Financial Econometrics* 11(2), 400-441. [abstract-level] https://ideas.repec.org/p/cte/wsrepe/ws097222.html
- Pelletier (2006), *J. Econometrics* 131(1-2), 445-473. [abstract-level + secondary] https://econpapers.repec.org/RePEc:ecm:nasm04:230 ; R package https://erised.las.iastate.edu/CRAN/web/packages/RSDC/index.html
- Guidolin & Timmermann (2007), *JEDC* 31(11), 3503-3544. [abstract-level] https://ideas.repec.org:443/a/eee/dyncon/v31y2007i11p3503-3544.html
- Ardia, Bluteau, Boudt & Catania (2018), "Forecasting risk with Markov-switching GARCH models: A large-scale performance study", *IJF*. [abstract-level] https://www.sciencedirect.com/science/article/pii/S0169207018300840
- Ardia, Bluteau, Boudt, Catania & Trottier (2019), MSGARCH, *JSS* 91(4). [abstract-level] https://jstatsoft.org/article/view/v091i04
- Fülle et al. (2024), *J. Forecasting*. [abstract-level] https://onlinelibrary.wiley.com/doi/10.1002/for.3117
- Fortin, Simonato & Dionne (2023), *IJF* 39(1), 314-331. [question confirmed; findings UNVERIFIED] https://ideas.repec.Org/a/eee/intfor/v39y2023i1p314-331.html
- Paolella, Polak & Walker (2019), *J. Econometrics* 213(2), 493-515. [abstract-level] https://ideas.repec.org/a/eee/econom/v213y2019i2p493-515.html
- Kinlaw, Kritzman, Page & Turkington (2021), *JPM* 47(8). [abstract-level] https://globalmarkets.statestreet.com/research/portal/insights/article/798c5c4b-ba41-449a-87ec-8fd102867c76
- Campbell, Sunderam & Viceira (2017), *Critical Finance Review* 6(2). [abstract-level] https://www.nber.org/papers/w14701
- Baele, Bekaert & Inghelbrecht (2010), *RFS* 23(6), 2374-2428. [abstract-level] https://nber.org/papers/w15260
- Brixton et al. (2023), *JPM* 49(4). [secondary] https://www.aqr.com/Insights/Research/Journal-Article/A-Changing-Stock-Bond-Correlation
- Cieślak & Pflueger (2023), *Annu. Rev. Financ. Econ.* 15, 433-448. [abstract-level] https://ideas.repec.org/a/anr/refeco/v15y2023p433-448.html
- David & Veronesi (2013), *JPE*. [secondary] https://www.nber.org/system/files/working_papers/w15563/revisions/w15563.rev1.pdf
- 2025 G7 study "Stock-bond return correlation: Understanding the changing behaviour" (authors and journal not confirmed). [abstract-level] https://www.sciencedirect.com/science/article/pii/S1042443125001325
- Patton, Ziegel & Chen (2019), *J. Econometrics* 211(2), 388-413. [abstract-level] https://arxiv.org/pdf/1707.05108
- Fissler & Ziegel (2016), *Ann. Statist.* 44(4), 1680-1707. [abstract-level] https://arxiv.org/pdf/1503.08123
- Acerbi & Székely (2014), "Backtesting Expected Shortfall", *Risk* / MSCI. [secondary: cited in Fissler-Ziegel and the MATLAB documentation] https://www.mathworks.com/help/risk/esbacktestbysim.unconditional.html
- Giacomini & White (2006), *Econometrica* 74(6), 1545-1578. [abstract-level] https://econometricsociety.org/publications/econometrica/2006/11/01/tests-conditional-predictive-ability
- Hansen, Lunde & Nason (MCS); Hansen (SPA); Romano & Wolf (stepwise). [secondary] https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison-reference.html
- Kritzman, Li, Page & Rigobon (2011), *JPM*. [secondary] https://globalmarkets.statestreet.com/research/portal/insights/article/2a8e282a-343b-443c-b362-1634c71d2d26
- Bergmeir & Benítez (2012), "On the use of cross-validation for time series predictor evaluation", *Information Sciences*. [abstract-level] https://research.monash.edu/en/publications/on-the-use-of-cross-validation-for-time-series-predictor-evaluati/
- Tashman (2000), "Out-of-sample tests of forecasting accuracy: an analysis and review", *IJF* 16(4), 437-450. [abstract-level + secondary] https://iaorifors.com/paper/33593
- Bailey, Borwein, López de Prado & Zhu (2016/2017), "The Probability of Backtest Overfitting", *J. Computational Finance* 20(4). [abstract-level] https://papers.ssrn.com/abstract=2326253 ; purging/embargo: https://en.wikipedia.org/wiki/Purged_cross-validation [community source]
- Ledoit & Wolf (2004), *J. Multivariate Analysis* 88(2), 365-411. [abstract-level] https://econpapers.repec.org/RePEc:eee:jmvana:v:88:y:2004:i:2:p:365-411
- Lindskog, McNeil & Schmock (2003), "Kendall's tau for elliptical distributions". [abstract-level; published version not checked] https://staff.math.su.se/lindskog/KendallsTau.pdf
- Rousseeuw, Minimum Covariance Determinant (FastMCD, Rousseeuw & Van Driessen). [secondary: implementation documentation] https://hudsonthames.org/portfolio-optimisation-with-mlfinlab-estimation-of-risk/ ; Tyler + Ledoit-Wolf hybrid https://arxiv.org/abs/1503.08013
- Székely, Rizzo & Bakirov (2007), *Ann. Statist.* 35(6), 2769-2794. [abstract-level] https://arxiv.org/pdf/0803.4101
- Laloux, Cizeau, Bouchaud & Potters (1999), *PRL*. [abstract-level] https://arxiv.org/abs/cond-mat/9810255
- Vicente et al. (2009), copula information, *EPL*. [abstract-level] https://www.ime.usp.br/~rvicente/RVicente_EPL09.pdf
- Fox, Sudderth, Jordan & Willsky (2008), sticky HDP-HMM, ICML. [abstract-level] https://mlanthology.org/icml/2008/fox2008icml-hdp/
- Wergé (2021), arXiv 2107.05535. [abstract-level] https://arxiv.org/pdf/2107.05535
- Nystrup et al., regime-based vs static allocation. [secondary] https://www2.imm.dtu.dk/pubdb/pubs/6808-full.html
- Data-source notes: https://portfoliooptimizer.io/blog/selecting-a-stock-market-data-web-api-not-so-simple/ ; https://edwardlg.github.io/assip-2026-empirical-finance/textbook/data-cards/free-equity-apis.html [informal sources]
