# Thesis pilot: handoff to Claude Code

1. Copy the `starter/` and `docs/` folders into the root of your GitHub repo.
2. Commit them: `git add starter docs && git commit -m "Add pilot starter code and briefing"`.
3. Open the repo in VS Code and start Claude Code. Switch to plan mode.
4. Paste in the full contents of `docs/PILOT_PROMPT.md`, or type:
   "Read docs/PILOT_PROMPT.md and follow it exactly, starting in plan mode."
5. Approve the plan. Claude Code pauses after the correctness tests and again
   after the 10-replication timing run.

Contents:
- starter/pilot_core.py: HMM, the four covariance variants, mixture VaR/ES,
  benchmarks, FZ0, DM, Kupiec
- starter/simulate.py: Monte Carlo power study (4 correlation scenarios)
- starter/analyze.py: summarises the simulation results
- starter/pilot_real_data.py: real-data pilot, hard-capped at 2015-12-31
- docs/literature_briefing.md: literature review and data-source notes
- docs/PILOT_PROMPT.md: the full instructions for Claude Code

Note: the starter code was smoke-tested on synthetic data only. Real Yahoo data
could not be downloaded in the environment where it was written.
