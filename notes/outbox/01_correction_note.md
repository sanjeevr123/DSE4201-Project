**To:** Prof. Seo
**Subject:** Corrections to the update and methods draft (thesis: regime-switching risk models)
**Attach:** corrected `01_design_and_methods.pdf` and `SUPERVISOR_DRAFT_2026-11-03.pdf`

Dear Prof. Seo,

Thank you for the feedback. While preparing the preregistration I found some errors in the two documents I sent. None of them changes a forecast or a computed result, but some change how results should be read.

<!-- wording-ok: this list quotes the errors it corrects; delete this line before sending -->
1. **Methods, p.3.** The minimum detectable difference is 2.80 x SE at 80% power (two-sided 5%). The PDF printed "8.800% power ... 2 x SE" because of a conversion error.
2. **Fund sample.** The test with p = 0.12 is on the full 1992-2019 sample (n = 7,053), not 1992-2009, and its 2010-2019 part overlaps the ETF samples in time.
3. **Calibration.** "Static regime models are too conservative" holds for the four ETF universes (5% hit rates 2.8% to 4.2%), not for the fund sample (B 5.4%, D 5.3%).
4. **Sidedness.** The power table is one-sided 5%, while the minimum detectable difference is two-sided. The confirmatory specification will state both, and every table will carry a label.
5. **Mean treatment.** I wrote that it does not explain the margin effect, and quoted only pooled and regime means. With zero means the effect is larger (U1: -0.0259 pooled, -0.0263 regime, -0.0339 zero), so the size depends on the mean treatment while the sign does not.
6. **An omission.** Under the GARCH-margin simulation, the static D-vs-B test is oversized: 11.0% at one-sided 5% (95% CI 6.7 to 15.3) and 17.0% at |t| > 1.96. The 37 of 214 raw rejections (17.3%) are therefore not evidence of an effect. The correlation tests on GARCH margins, including the proposed confirmatory test, have a one-sided rejection rate of 4.5% in the same simulation.
7. **Wording.** "Well-powered null" was wrong: simulated power for a strong shift was 38.0% and 53.5%. "About half" of the detectable difference is 0.36 to 0.52. Regime moments do use smoothed in-window probabilities (data up to the window end only), while forecast-day mixture weights are filtered. "Without rebalancing" should read "constant weights, rebalanced daily". The lag rule is a fixed formula, not automatic selection. Following your comment, I have removed "nested" where models are not strictly nested. I have also removed the sentence attributing a result to Ardia et al. (2018), which I had not checked against the paper.

Corrected versions are attached. I will send the frozen specification before running the hold-out, with a few working days for any objection.

Could you also let me know which milestones you would like from here, and in what form you want the next update?

Best regards,
Sanjeev
