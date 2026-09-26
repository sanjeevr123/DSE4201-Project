# Pilot Decisions Log

Ambiguous choices made while executing docs/PILOT_PROMPT.md, picked
conservatively and logged here per that document's working rules ("If
something is ambiguous, pick the conservative option, write it into
docs/decisions_log.md with a one-line reason, and continue"). This is
separate from `notes/decision_log.md`, which tracks broader thesis-level
methodology decisions outside the pilot's scope.

- **`output/` vs `outputs/`**: created a new `output/` (singular) directory
  for all pilot (WP0-WP5) deliverables, left the pre-existing `outputs/`
  (plural) untouched for the unrelated Day-1 EDA pipeline. Confirmed with
  the user before WP0.

- **Zero-mean bug in `mix_var_es`**: fixed before WP1, by threading the
  regime-conditional mean through `build_variants` into `mix_var_es`
  (`src/engine.py`), rather than leaving A/B/C/D/Oracle zero-mean while
  GARCH-t/HS remain mean-aware. Confirmed with the user before WP0.

- **EWMA vs EWMA_MV are mathematically identical for this design**: for a
  *fixed*-weight portfolio, `w' (lam*Cov + (1-lam)*r r') w == lam*(w'Cov*w) +
  (1-lam)*(w'r)^2`, i.e. the multivariate EWMA's portfolio-projected
  variance recursion is algebraically identical to the univariate EWMA
  recursion on the portfolio return series directly. Confirmed numerically
  (WP3 real-data table: EWMA and EWMA_MV rows are identical to floating-point
  precision). This does not affect the B/D vs EWMA_MV comparisons, which
  remain meaningful (regime models vs. a smooth, non-regime benchmark) —
  but it means the univariate/multivariate EWMA *distinction itself* adds
  no information here, and is not, on its own, a further test of the
  correlation channel the way D vs B is. Reported plainly in the final
  report rather than treated as a redundant "extra confirmation."

- **WP4 "re-run from a clean environment"**: interpreted as re-running each
  deterministic step from its saved inputs (fixed seeds, the archived raw
  data) on the same single development machine, and diffing outputs
  numerically — not provisioning a second physical machine, which is out of
  scope for a one-person pilot on a laptop. Machine specs and package
  versions are recorded so this claim is at least auditable.

- **Data-audit missing-dates check** (`src/audit.py::missing_dates`): uses a
  plain business-day calendar, not an NYSE holiday calendar, so it
  over-counts genuine market holidays as "missing." Conservative in the
  sense that it never under-reports; the audit report is read alongside
  this caveat rather than the check being made holiday-aware, which would
  add an external dependency (a market-calendar package) for a pilot-stage
  audit.

- **Ardia et al. (2018) citation** (named in docs/PILOT_PROMPT.md's WP5 list
  but not present in docs/literature_briefing.md): verified via web search
  rather than left as a bare, unchecked name. Confirmed as Ardia, Bluteau,
  Boudt et al. (2018), "Forecasting risk with Markov-switching GARCH
  models: A large-scale performance study," *International Journal of
  Forecasting* 34(4), 733-747
  (https://www.sciencedirect.com/science/article/pii/S0169207018300840) —
  matches the "regime volatility, univariate" description in the prompt.

- **Forbes & Rigobon (2002)**: only briefly named in
  docs/literature_briefing.md (motivating why the thesis tests correlation
  via forecast accuracy rather than raw crisis-correlation comparisons), not
  described in detail there. Cited only for that motivating point in WP5's
  output/literature_positioning.md, not for specific numeric findings, since
  the briefing gives no further detail and it was not independently
  re-verified.
