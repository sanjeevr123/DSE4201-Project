# Supervisor Questions

## Questions I Can Answer Through Independent Learning

Use this section for questions that initially seem unclear but can
be resolved through textbooks, lecture notes, coding documentation,
or my own study.

## Questions Requiring Methodological Judgement

Use this section for specification, inference, identification,
robustness, and econometric-design issues where supervisor expertise
is genuinely valuable.

## Decisions to Resolve at the Next Meeting

Use this section only for decisions that should actually be discussed
with my supervisor.

Populated from the pilot study's go/no-go verdict (all six criteria pass
-> PROCEED, see `output/PILOT_REPORT.md`) and the open items already
tracked in `notes/decision_log.md`:

- **Final ETF universe and portfolio construction.** The pilot used a
  temporary SPY/IEF/GLD equal-weight portfolio. Confirm the final
  universe and weighting scheme before extending the pipeline to
  2016-2025.
- **Two vs. three regimes.** Real-data stability diagnostics
  (`output/tables/wp3_stability.json`) show expected stress-state
  durations of 45-97 days per refit, much longer than the 5-day floor —
  worth discussing whether a 3-state model could usefully split "moderate
  stress" from "acute stress," or whether 2 states remain the right call.
- **Regime-identifying variable.** The pilot's equity-only HMM signal
  showed near-zero stress probability during the 2013 taper tantrum — a
  real bond/rates-driven shock the equity signal missed
  (`output/tables/wp3_episodes.json`). Should the final design add a
  second regime-identifying variable (e.g. rates or VIX)?
- **Power caveat (G3).** The design only reliably detects (>=50% power)
  a *strong* correlation-regime shift with 10 years of data; a moderate
  shift is detected only ~25% of the time even at 10 years, ~30% at 15
  years. Is this power level acceptable to report as a limitation, or
  does the full thesis need a different evaluation design (see the
  REFRAME fallback already specified in `docs/preregistration.md`)?
- **Benchmark model set, VaR/ES evaluation design, dependence-testing
  method, portfolio-allocation extension.** Still open per
  `notes/decision_log.md` / the README's "Current Open Methodological
  Decisions" list; not yet addressed by the pilot.
