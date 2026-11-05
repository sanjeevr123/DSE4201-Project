# Viva preparation

Plain-language guide to the methods, then the 20 hardest likely questions with honest answers and where the evidence lives. Numbers are from `output/confirm/holdout/` unless stated.

## The methods in plain language
- **VaR and ES.** The 5% value-at-risk is the loss that should be exceeded on 1 day in 20. Expected shortfall is the average loss on those bad days. Both are negative numbers here (returns).
- **FZ0 loss.** One score that rewards a VaR and ES pair for being right together. Lower is better. A difference of 0.0013 is roughly the penalty for scaling both forecasts by a factor 2 to 3 per cent away from the truth (Table 5.1).
- **Regime switching.** A two-state hidden Markov model fitted to SPY returns says each day whether the market is calm or stressed (as a probability). In RSC_P only the SPY-IEF correlation is allowed to differ by state; volatilities come from GARCH(1,1) in both models. CCC keeps one constant correlation.
- **GARCH(1,1).** Volatility that rises after big moves and decays slowly. Both primary models use it for each asset, so the difference between them is the correlation treatment only.
- **Diebold-Mariano test.** Takes the daily loss difference d_t, averages it, and divides by a standard error that allows for serial dependence (HAC, 7 lags). One-sided 5%: reject if t < -1.645.
- **MDE, SESOI, power.** MDE is the smallest true difference that would be detected with 80% probability given the standard error (0.0031 here). SESOI is the smallest difference I would call meaningful (0.002). Power depends on the true effect and the standard error.
- **Preregistration.** The hypothesis, decision rule and code were fixed in git tags before the 2020-2025 forecasts were made (`spec-freeze-v1`, amended once by `spec-freeze-v1.1`).
- **Result.** Outcome O2: estimate -0.0013 (95% interval -0.0037 to +0.0012), one-sided p = 0.158; the data neither establish nor exclude an improvement.

## Twenty hard questions
1. **Why is a non-significant result worth a thesis?** It is the pre-specified answer to a stated question, reported with an interval and the MDE, so it shows what 1,508 days can and cannot detect. Ch7, Ch8.
2. **Your MDE (0.0031) exceeds your SESOI (0.002). Why run it?** The sample was fixed by history (2020-2025); I stated in advance that O3 was unlikely and that no equivalence claim would be made (Ch5, Section 5.7). The honest description is a measurement of precision, not a test with a good chance of excluding a gain. Ch8 limitations.
3. **Which power is the test's: 18%, 35%, 48% or 86%?** They answer different questions. 18.2% and 35.2% are simulated, each under its own scenario and simulated standard error (S2's is 0.0026, twice the observed one). 48% is power against a true gain of 0.0020 at the observed SE; 86% is against the strong simulated shift at the observed SE. The last two were computed after the result and are labelled so. Ch6 Section on power, Ch7.
4. **Why one-sided?** The hypothesis is directional (switching should help) and the power simulation used it; the two-sided p is 0.316 and the conclusion is unchanged. Ch5.
5. **You amended the freeze after the forecasts existed. Why trust it?** The scorer refused the run because the recorded commit was two commits after the tag; those commits touched only an ignore file and the log. The amendment compares code files, the forecasts were not re-run, and the pickle hash matches. It went beyond the letter of preregistration 6a and the check does not cover configuration or environment; I say so in Ch7. Evidence: preregistration section 8 (the amendment), git diff v1..v1.1.
6. **Was the specification really independent of the data?** No. It was chosen after exploring development data (ten universes, ten regime definitions) and a power simulation where the SPY-IEF shift is largest by construction. What is clean is that nothing was fitted on 2020-2025. Ch8 limitations.
7. **Is DM valid when one model nests the other?** Nesting results (Clark-McCracken, Clark-West) are for linear models and squared error; I do not rely on them. My estimand is the loss difference of two procedures with rolling estimation windows, in the Giacomini-White sense, where estimation error is part of the estimand. I checked size by simulation (3.6% one-sided, 500 replications, interval 2.0% to 5.2%) and I admit that evidence is weak. Ch5, Ch6.
8. **Why is the HAC lag 7? Does it matter?** m = floor(4(T/100)^(2/9)). Post hoc, the t-statistic is -1.04, -1.00, -0.90, -0.84 at lags 0, 7, 21, 42. Ch7 post hoc subsection, `output/confirm/posthoc.json`.
9. **Is the mean of d_t meaningful when it comes from a few episodes?** The sum is -1.91; 2021 contributes -1.56, the COVID window in 2020 +1.05, and excluding that window the mean is -0.0020. So the average is a net of large opposite episodes. It is the pre-specified estimand; I report the decomposition post hoc. Ch7.
10. **Did the model capture the 2022 correlation reversal?** No claim. 2022 contributes -0.24 to the sum, with an interval of -0.0089 to +0.0070. The model learns stress correlation from five years in which it was negative or low, so it was unlikely to produce a positive stress correlation. Ch1, Ch8.
11. **Both models breached the 5% VaR on about 6.9% of days. Is that a finding?** Yes, descriptive: 104 and 103 breaches against 75 expected, Kupiec p about 0.001 to 0.002; breach-day returns averaged about 1.17 times forecast ES. Z2 mixes frequency and magnitude. I did not run a separate test of ES magnitude, and the independence test is first-order with low power. Ch7 calibration.
12. **If both are miscalibrated the same way, what does their difference tell a risk manager?** Little about adequacy: it says only that, relative to each other, switching changed the loss by an amount too small to detect. Ch7, Ch8.
13. **Why do the static models have standard errors twenty times larger?** Their losses have a few huge days; I conjecture 2020 but did not examine it (labelled conjecture). Ch7.
14. **Why does regime-specific volatility help against a pooled normal but not against GARCH?** GARCH already tracks volatility clustering, which is what the regime proxy mostly captures. Development data: the GARCH-margin class did better in all four ETF samples and significantly after Holm in one. Ch6.
15. **How do you know the HMM is not look-ahead biased?** Forecast for day t uses returns through t-1, filtered (not smoothed) probabilities, and the one-step regime transition; refits use only the rolling window. Checked against src/ in Phase 9. Ch4.
16. **Are your SESOI and the 3% scale error arbitrary?** Yes, an assumption stated as such. The unrounded value is 0.00167 under normal; under t6 about 0.0013 to 0.0014. O3 depends on it, but the O2 verdict would not change at 0.001 (lower bound -0.0033 is below -0.001). Ch5 Section 5.7, `output/confirm/sesoi.json`.
17. **Why not a bootstrap for inference?** The pre-specified test is DM/HAC; a bootstrap of the whole pipeline is listed as future work because it would carry HMM and GARCH uncertainty into the interval. Ch8.
18. **What is new relative to Paolella et al. and Fortin et al.?** I did not find a study that scores a switching-correlation stock-bond portfolio with a joint VaR/ES loss under a pre-fixed decision rule with MDEs next to results. Stated as what I read, not as a claim that none exists; I read working-paper versions only. Ch2.
19. **Would a different window or signal change the result?** Not tested, by design; running variants on the hold-out would be unplanned analysis. Ch8 slow-signal section and future work.
20. **What would you do with more time or data?** Several portfolios or markets to raise power, a signal from the stock-bond correlation or macro variables, a faster window, and a bootstrap of the full pipeline; each a new pre-specified study. Ch8.

## Known weak points to be ready for
- Preregistration was self-timestamped; the v1.1 amendment came after the forecasts existed.
- Low power; the 48% and 86% figures use the observed standard error.
- Size evidence from 500 simulated replications.
- Post hoc decomposition shows 2021 and the COVID window drive the average.
- Literature read partly as abstracts and working papers (see `notes/literature_audit.md`).
