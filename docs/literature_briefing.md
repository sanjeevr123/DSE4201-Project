I'll research similar studies, whether the key results hold up, data sources and tooling, then give you a feasibility verdict.The idea holds up. It's feasible, it sits in a genuinely unsettled part of the literature, and I couldn't find a study that runs your exact test. Details below.

## 1. Verdict

| Criterion | Assessment | Why |
|---|---|---|
| Feasible in 5 weeks | ✅ Yes | Free data, standard Python tools, only 3 assets |
| Value-adding | ✅ Yes, as a transparent extension | Published evidence on whether correlation modelling improves portfolio risk forecasts is split |
| Intriguing | ✅ Yes | Stocks and bonds moved from hedging each other to falling together (2022) and back, and industry is debating where it goes next |
| Novelty | ⚠️ Likely gap, not proven | Close relatives exist, but none isolates correlation from volatility with shared regime probabilities |

## 2. Do results hold? Similar studies

The literature disagrees on whether modelling changing dependence improves portfolio risk forecasts. That disagreement is why your question is worth asking.

**Evidence that correlation dynamics matter:**
- **Santos, Nogales & Ruiz (2013).** Multivariate models beat univariate ones out of sample, with DCC and Student-t errors the best fit for real portfolio VaR. They also found multivariate models with constant correlations usually did worse than univariate models. That hints that *changing* correlation is what adds value, which is close to your D-vs-B contrast.
- **Paolella, Polak & Walker (2019), the closest relative.** They show Markov-switching correlation dynamics produce highly accurate risk forecasts and could lower regulatory capital during distress. Their model is heavy (generalized hyperbolic distributions, a custom two-stage EM algorithm) and does not separately test volatility vs correlation. Your thesis is the simple, interpretable version of that question.
- **Engle & Colacito (2006).** Getting dynamic correlations right is worth roughly 60 basis points a year on average, and hundreds on some days.
- **Pouliasis (2018).** Working with stocks, bonds and commodities, he found substantial economic value in both volatility timing and correlation timing.
- **Itou & Yoshiba (2025).** Lower-tail dependence rose relative to upper-tail dependence across asset pairs during the COVID crash and the recent inflation period, and modelling this improved ES accuracy.

**Evidence that it doesn't matter much:**
- **Fortin, Simonato & Dionne (2023, IJF).** For one-week-ahead ES, they found mostly no statistically significant accuracy difference between univariate and multivariate approaches. They use the same joint VaR/ES scoring method you plan to use, which makes this your most important counterpoint.
- **Kole et al. (2017).** Modelling at the asset level beat full portfolio aggregation, but the gaps were small, and model and distribution choices mattered less than data frequency.
- **Earlier work.** Brooks & Persand (2003) and McAleer & da Veiga (2008) found no clear preference between multivariate and univariate approaches for VaR.
- **Fortin et al. on why results conflict.** They attribute the disagreement partly to whether studies use daily or weekly data and whether they allow skewed distributions. Daily data favours multivariate models, so your daily design gives correlation its fairest chance.

**Evidence on measuring crisis correlation:**
- **Chua, Kritzman & Page (2009).** US/international equity correlation was +76% when both fell more than one standard deviation, versus −17% when both rose.
- **Kinlaw et al. (2021).** They argue such conditional correlations ignore episodes where one asset's gains offset the other's losses, and that measuring what matters changes the conclusions sharply. Together with Forbes–Rigobon, this is why you test correlation through forecast accuracy rather than by comparing raw crisis correlations.

**A 2026 descriptive study that pairs well with yours:** a leave-one-out decomposition of an equal-weight multi-asset portfolio.
- The 2007 equity risk spike came mostly from standalone volatility.
- In 2008, equities and commodities showed a correlation-driven spike.
- In 2022, bond volatility rose but was offset by falling correlation risk.

So which channel dominates depends on the episode. That study is descriptive (Level 2); yours tests whether this helps *forecasting* (Level 3), which is the natural next step.

**Signs the allocation space is crowded:** a May 2026 arXiv paper already runs a 3-state HMM on SPY/TLT/GLD with rule-based and reinforcement-learning allocation. That reinforces dropping allocation. A forecasting ablation is more distinctive than yet another regime-trading backtest.

## 3. Why the timing works

Your 2016–2025 test window contains a full stock-bond correlation cycle, which gives the correlation channel a real chance to matter:
- **Before 2021:** negative (bonds hedged stocks).
- **2022:** the first year since 1977 that both equities and bonds had negative returns.
- **Recently:** BlackRock notes the correlation has reverted to slightly negative as inflation cooled.
- **Looking ahead:** Oxford Economics argues the reversal is temporary and expects the correlation back in positive territory in 2026, while AQR says the future sign remains uncertain.

A risk-model thesis on exactly this question is topical in interviews right now.

**Built-in hypothesis:** a regime defined by *equity* volatility may miss the 2022 episode, because that was a rates and inflation shock, not a classic equity panic. Report 2022 as a pre-declared diagnostic case. The finding is interesting either way.

## 4. Data sources

| Source | Verdict | Notes |
|---|---|---|
| **Yahoo Finance via yfinance** | Primary | The library now returns dividend-adjusted prices by default under the label "Close" rather than "Adj Close", so set `auto_adjust` explicitly. It's unofficial, can break without notice, and adjusted histories shift after each dividend. **Download once, save the raw file, never re-pull.** |
| **Tiingo (free tier)** | Cross-check | Full price history available. A 2022 test found Tiingo's adjusted prices matched an independent recalculation. Use it to spot-check IEF dividends. |
| **Stooq** | Avoid for returns | It doesn't provide adjusted closes, which misstates performance for bond ETFs that pay coupons. |
| **FRED** | Optional | T-bill rate, VIX, CPI for descriptive context only |

**Sample:** GLD launched in late 2004, which sets the start date. IEF (2002) and SPY are older. GLD pays no dividends, so its adjustment risk is low; IEF is the one to audit.

## 5. Tooling (all free, mostly Python)

| Task | Tool |
|---|---|
| 2-state HMM | `hmmlearn` (or hand-coded forward filter; about 30 lines) |
| GARCH-t benchmark | `arch` |
| Mixture VaR/ES | `scipy` root-finding plus the closed-form formula from Brief 1 |
| Joint VaR/ES score (FZ0 loss) | Hand-code; about 10 lines |
| ES backtest | A Python implementation of the Acerbi–Székely unconditional test exists on GitHub. The R package `esback` implements the strict and auxiliary ESR backtests if you want the regression version. |
| Loss comparison | Diebold–Mariano with HAC errors (`statsmodels`) |

## 6. Design changes the research suggests

1. **Add a cheap, smooth-correlation benchmark: multivariate EWMA vs univariate EWMA.** This is a non-regime version of your D-vs-B question. Santos et al. found smooth correlation dynamics (DCC) helped, so this tests whether *regimes* beat *smooth updating*. It's roughly 20 lines of code.
2. **Keep daily data.** Fortin et al.'s weekly null result is partly attributed to frequency.
3. **Report statistical power openly.** Fortin et al. mostly found no significant differences, so if you get a null, show confidence intervals to distinguish "no effect" from "can't tell".
4. **Frame your contribution explicitly against Paolella et al. (2019)**, as the simple, interpretable decomposition, and against Fortin et al. (2023), as a daily, multi-asset rather than weekly equity-factor setting.

## 7. How to position the thesis

A one-line framing for Prof. Seo:

> "Prior work disagrees on whether modelling time-varying dependence improves portfolio tail-risk forecasts (Santos et al., 2013 vs Fortin et al., 2023), and the most direct regime-switching evidence (Paolella et al., 2019) uses complex models that don't separate volatility from correlation. I isolate the correlation channel with a controlled ablation on a stock-bond-gold portfolio through the 2022 correlation reversal."

That is honest, clearly grounded, and defensible in a viva or an interview.

**Remaining risks:** HMM instability, a likely small effect size, and the need to verify Paolella et al.'s full text through your library before leaning on it. None of these threatens completion, because the fallback (volatility-only vs GARCH-t) is already inside the design.

Sources:
- [Paolella, Polak & Walker (2019), J. Econometrics](https://www.sciencedirect.com/science/article/abs/pii/S0304407619301563)
- [Santos, Nogales & Ruiz (2013), SSRN](https://www.ssrn.com/abstract=2110297)
- [Fortin, Simonato & Dionne (2023), IJF](https://www.sciencedirect.com/science/article/abs/pii/S0169207021001849)
- [Kole et al. (2017), SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2711203)
- [Engle & Colacito (2006), SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1267010)
- [Pouliasis (2018), J. Futures Markets](https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.21939)
- [Chua, Kritzman & Page (2009), JPM](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/217ad761-4240-4989-ab5c-c32f3c847965/jpm_the_myth_of_diversification.pdf)
- [Kinlaw et al. (2021), SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3781844)
- [Leave-one-out risk decomposition (2026), arXiv](https://arxiv.org/pdf/2604.10375)
- [HMM + RL on SPY/TLT/GLD (2026), arXiv](https://arxiv.org/abs/2605.27848)
- [Oxford Economics, stock-bond correlation 2026](https://www.oxfordeconomics.com/resource/stock-bond-correlation-will-become-positive-again-in-2026/)
- [BlackRock, bonds and diversification](https://www.blackrock.com/us/financial-professionals/insights/bonds-offer-more-diversification)
- [AQR, positive stock-bond correlation](https://www.aqr.com/Insights/Perspectives/A-Positive-Stock-Bond-Correlation-Is-a-Terrible-Reason-to-Add-More-Equity-Risk-to-Your-Portfolio)
- [Vanguard, stock/bond correlations](https://www.vanguard.co.uk/professional/vanguard-365/investment-knowledge/portfolio-construction/understanding-stock-bond-correlations)
- [Free equity API data card](https://edwardlg.github.io/assip-2026-empirical-finance/textbook/data-cards/free-equity-apis.html)
- [yfinance adjusted-price note](https://kerryback.substack.com/p/02-online-data)
- [Portfolio Optimizer, data API comparison](https://portfoliooptimizer.io/blog/selecting-a-stock-market-data-web-api-not-so-simple/)
- [Stooq limitation](https://medium.com/@josue.monte/practical-guide-to-backtesting-investment-strategies-with-python-and-yahoo-finance-5fe72305aaf3)
- [Acerbi–Székely Python implementation](https://github.com/LlucPuigCodina/expected-shortfall-unconditional-test-acerbi-szekely)
- [esback R package](https://rdrr.io/github/BayerSe/esback/man/esr_backtest.html)