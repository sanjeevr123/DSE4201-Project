"""
Smallest effect of interest in FZ0 units (docs/THESIS_PLAN.md 2.B.3), derived analytically with no market data.

If a forecaster states VaR and ES both multiplied by c relative to the true values of a correctly specified distribution, the
expected FZ0 loss exceeds the minimum by a penalty P(c) = E[S(c v0, c e0, Y)] - E[S(v0, e0, Y)] >= 0 (FZ0 is strictly consistent for
(VaR, ES), so the minimum is at c = 1). c > 1 overstates risk, c < 1 understates it. FZ0 (Patton, Ziegel and Chen 2019):
S(v, e, y) = -1{y <= v}(v - y)/(alpha e) + v/e + log(-e) - 1, with v, e < 0, and
E[1{Y <= v}(v - Y)] = integral of F from -inf to v.

DECLARED VALUE (docs/decisions_log.md): the mean of the penalties of a 3% overstatement and a 3% understatement, standard normal,
tail level 5%, rounded to one significant figure. Other distributions, tail levels and sizes are reported for context only.

  .venv/bin/python scripts/confirm_04_sesoi.py
Output: output/confirm/sesoi.json. The script reads no data.
"""
from __future__ import annotations

import json
import sys
from math import floor, log10
from pathlib import Path

import numpy as np
from scipy import integrate, stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "confirm"


def unit_variance_t(nu: float):
    """Standardised (unit-variance) Student-t: cdf, ppf, and expected shortfall of a standard deviation of one."""
    s = np.sqrt((nu - 2) / nu)
    return (lambda y: stats.t.cdf(y / s, nu)), (lambda p: s * stats.t.ppf(p, nu))


def dist(name: str):
    if name == "normal":
        return stats.norm.cdf, stats.norm.ppf
    if name.startswith("t"):
        return unit_variance_t(float(name[1:]))
    raise ValueError(name)


def expected_fz0(c: float, alpha: float, name: str) -> float:
    cdf, ppf = dist(name)
    v0 = ppf(alpha)
    e0 = integrate.quad(lambda p: ppf(p), 0, alpha)[0] / alpha            # ES = mean of the lower alpha tail
    v, e = c * v0, c * e0
    I = integrate.quad(cdf, -np.inf, v)[0]                                 # E[1{Y <= v}(v - Y)]
    return float(-I / (alpha * e) + v / e + np.log(-e) - 1.0)


def penalty(c: float, alpha: float, name: str) -> float:
    return expected_fz0(c, alpha, name) - expected_fz0(1.0, alpha, name)


def one_sig_fig(x: float) -> float:
    return round(x, -int(floor(log10(abs(x)))))


def main():
    # closed-form check for the standard normal: E[1{Y <= v}(v - Y)] = v Phi(v) + phi(v)
    a, v = 0.05, 1.7 * stats.norm.ppf(0.05)
    assert abs(integrate.quad(stats.norm.cdf, -np.inf, v)[0] - (v * stats.norm.cdf(v) + stats.norm.pdf(v))) < 1e-9
    table = {}
    for name in ("normal", "t6"):
        for alpha in (0.05, 0.025):
            table[f"{name}_alpha{alpha}"] = {f"c={c}": penalty(c, alpha, name)
                                             for c in (0.90, 0.95, 0.97, 0.98, 1.02, 1.03, 1.05, 1.10)}
    over, under = penalty(1.03, 0.05, "normal"), penalty(0.97, 0.05, "normal")
    mean_pen = (over + under) / 2
    out = {"penalty_by_scale_factor": table, "declared_rule": "mean of 3% overstatement and 3% understatement penalties, "
           "standard normal, tail level 5%, rounded to one significant figure",
           "overstatement_3pct": over, "understatement_3pct": under, "mean_3pct": mean_pen,
           "sesoi_declared": one_sig_fig(mean_pen),
           "all_variants_round_to": sorted({one_sig_fig(x) for k, t in table.items() for c, x in t.items() if c in ("c=0.97", "c=1.03")}),
           "assumption": "that a 3% proportional error in the stated VaR and ES is economically meaningful is an assumption, not a fact"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sesoi.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "penalty_by_scale_factor"}, indent=2))
    for k, t in table.items():
        print(k, {c: round(x, 5) for c, x in t.items()})


if __name__ == "__main__":
    main()
