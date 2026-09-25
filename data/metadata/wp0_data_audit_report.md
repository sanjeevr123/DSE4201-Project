# WP0 Data Audit Report

Audited range: 2004-11-18 to 2026-09-25

## Missing dates
- 205 missing business days out of 5702 expected (5497 observed).
- Sample: 2004-11-25, 2004-12-24, 2005-01-17, 2005-02-21, 2005-03-25, 2005-05-30, 2005-07-04, 2005-09-05, 2005-11-24, 2005-12-26, 2006-01-02, 2006-01-16, 2006-02-20, 2006-04-14, 2006-05-29, 2006-07-04, 2006-09-04, 2006-11-23, 2006-12-25, 2007-01-01

## Zero / duplicate / stale prices
- 0 duplicate index dates in the panel.
- SPY: 0 zero/negative prices, 16 stale consecutive-day repeats.
- IEF: 0 zero/negative prices, 47 stale consecutive-day repeats.
- GLD: 0 zero/negative prices, 20 stale consecutive-day repeats.

## Returns beyond 8 standard deviations
- SPY: 6 flagged days.
  - 2008-10-13: +0.1452
  - 2008-10-15: -0.0984
  - 2008-10-28: +0.1169
  - 2020-03-12: -0.0957
  - 2020-03-16: -0.1094
  - 2025-04-09: +0.1050
- IEF: 1 flagged days.
  - 2009-03-18: +0.0343
- GLD: 2 flagged days.
  - 2008-09-17: +0.1129
  - 2026-01-30: -0.1027

## Dividend days per ticker
- SPY: 88 dividend days.
- IEF: 403 dividend days.
- GLD: 0 dividend days.

## IEF dividend spot-check (manually verify against a public source)
- 2009-11-02: close=90.9800, adj_close=61.9366, adjusted_return=-0.2630%, raw_return=-1.0979%, implied_dividend_effect=+0.8350%
- 2007-06-01: close=81.1200, adj_close=49.9478, adjusted_return=-0.4307%, raw_return=-0.8313%, implied_dividend_effect=+0.4006%
- 2007-09-04: close=83.6500, adj_close=52.1144, adjusted_return=-0.1861%, raw_return=-0.5824%, implied_dividend_effect=+0.3963%
