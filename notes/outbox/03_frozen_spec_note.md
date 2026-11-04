Dear Prof. Seo,

As you asked, here is the specification of the hold-out test before I run it. The full text is in `docs/preregistration_confirmatory.md` (attached).

- **Hypothesis.** The test compares two forecasting procedures for the one-day 5% VaR and ES of an equal-weight (daily rebalanced) SPY/IEF/GLD portfolio: GARCH(1,1) margins with (RSC_P) a two-state regime-switching SPY-IEF correlation, and (CCC) a constant correlation. Loss: FZ0. H0: the switching model does not have lower expected loss; H1: it does.
- **Sidedness.** One-sided 5% test, reject if t < -1.645 (HAC standard error, 7 lags). I also report the two-sided 95% interval and both p-values. A separate statement, "significantly worse", applies at t > +1.96.
- **Exact SPY-IEF specification.** Only the (SPY, IEF) correlation entry switches with the regime; the other two correlations stay pooled. Regime: two-state Gaussian HMM on SPY returns, 1,260-day rolling window, refitted every 21 days.
- **Expected power.** In simulation at the hold-out length (1,508 days, 500 replications) the test rejects in 3.6% of null replications, and in 18.2% (moderate shift) and 35.2% (strong shift) of the alternatives. An inconclusive result is therefore likely, and the pre-written wording says so without claiming an absence of an effect.
- **Secondary analyses.** Six, unadjusted and labelled secondary (listed in the file).

The specification is fixed by a git tag before the run. Unless I hear an objection within three working days, I will run it once on the fourth.

Best regards,
[name]
