"""
Pre-freeze audit of the single-pair (SPY-IEF) correlation matrices of RSC_P (docs/THESIS_PLAN.md 3.6). For every refit of two
chains with data through 2019-12-31 (forecasts from 2010 and from 2016, both anchored at their first forecast day), and for the
window ending 2019-12-31 (the first hold-out window), it records for each state: pooled and regime-specific SPY-IEF correlation
of the GARCH-standardised residuals, whether the PSD repair in nearest_corr fired, the smallest eigenvalue before and after,
the largest change to any entry, and the admissible interval of the SPY-IEF entry given the other two entries.
The 2016 chain is the dry-run chain; its repair flags are cross-checked against run_rs_corr's own diagnostics when the dry-run
pickle exists. Same functions as run_rs_corr, no forecasts.

  .venv/bin/python scripts/confirm_02_pair_repair_audit.py
Output: output/confirm/pair_repair_audit.csv, output/confirm/pair_repair_audit_summary.json. Data are truncated at 2019-12-31
before any computation (confirm_00_run.load).
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from confirm_00_run import LAG_RETURNS, OUT, PAIR, REFIT, WINDOW, load  # noqa: E402,F401
from src.explore_routes import fit_margins, garch_filter, nearest_corr, pair_variant, weighted_corr  # noqa: E402
from src.explore_wf import HMMProvider  # noqa: E402

MARGIN_REFIT = 63


def admissible(R: np.ndarray, pair=PAIR) -> tuple[float, float]:
    """Interval of the (i, j) correlation that keeps a 3x3 correlation matrix PSD, given the other two entries."""
    i, j = pair
    k = [x for x in range(3) if x not in pair][0]
    a, b = R[i, k], R[j, k]
    half = np.sqrt((1 - a ** 2) * (1 - b ** 2))
    return a * b - half, a * b + half


def rows_for_window(R, win, gamma, params, t0, date, chain):
    eps, sig2 = garch_filter(R[win], params)
    z = eps / np.sqrt(sig2[:-1])
    pool = weighted_corr(z, np.ones(len(z)))
    out = []
    for k in range(gamma.shape[1]):
        reg = weighted_corr(z, gamma[:, k] + 1e-12)
        raw = pool.copy()
        raw[PAIR] = raw[PAIR[::-1]] = reg[PAIR]
        rep = []
        fixed = pair_variant(pool, reg, PAIR, repairs=rep)
        lo, hi = admissible(pool)
        out.append(dict(chain=chain, t0=t0, date=str(date.date()), state=k, pooled=pool[PAIR], regime=reg[PAIR],
                        repaired=rep[0], min_eig_raw=float(np.linalg.eigvalsh(raw).min()),
                        min_eig_final=float(np.linalg.eigvalsh(fixed).min()), max_entry_change=float(np.abs(fixed - raw).max()),
                        adm_lo=lo, adm_hi=hi))
    return out


def chain(R, dates, start, name):
    T = len(R)
    prov, params, rows = HMMProvider("HMM_SPY2", R[:, 0], K=2), None, []
    for t0 in range(start, T, REFIT):
        win, blk = slice(t0 - WINDOW, t0), slice(t0, min(t0 + REFIT, T))
        if params is None or (t0 - start) % MARGIN_REFIT == 0:
            params = fit_margins(R[win])
        gamma, _ = prov.step(win, blk)
        rows += rows_for_window(R, win, gamma, params, t0, dates[t0], name)
    return rows


def first_holdout_window(R, dates):
    """The window of 1,260 returns ending 2019-12-31 with a cold HMM and fresh margins, as the hold-out's first refit."""
    T = len(R)
    win, blk = slice(T - WINDOW, T), slice(T - 1, T)
    prov = HMMProvider("HMM_SPY2", R[:, 0], K=2)
    gamma, _ = prov.step(win, blk)
    return rows_for_window(R, win, gamma, fit_margins(R[win]), T, dates[-1], "first_holdout_window")


def main():
    r = load("2019-12-31")
    R, dates = r.values, r.index
    rows = []
    for name, first in (("2010", "2010-01-01"), ("2016", "2016-01-01")):
        rows += chain(R, dates, int(np.searchsorted(dates, pd.Timestamp(first))), name)
    rows += first_holdout_window(R, dates)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "pair_repair_audit.csv", index=False)

    summary = {}
    for name, g in df.groupby("chain"):
        summary[name] = dict(n_matrices=len(g), repairs=int(g.repaired.sum()), max_entry_change=float(g.max_entry_change.max()),
                             min_eig_final=float(g.min_eig_final.min()), min_eig_raw=float(g.min_eig_raw.min()),
                             adm_median=[float(g.adm_lo.median()), float(g.adm_hi.median())], adm_min_upper=float(g.adm_hi.min()),
                             adm_max_lower=float(g.adm_lo.max()), pooled_median=float(g.pooled.median()),
                             regime_by_state={int(k): dict(median=float(s.regime.median()), min=float(s.regime.min()),
                                                           max=float(s.regime.max())) for k, s in g.groupby("state")})
    pk = OUT / "pseudo_forecasts.pkl"
    if pk.exists():
        d = pickle.load(open(pk, "rb"))["L2"]["diag"]["psd_repairs"]
        mine = {t0: g.repaired.tolist() for t0, g in df[df.chain == "2016"].groupby("t0")}
        summary["crosscheck_vs_run_rs_corr_2016"] = bool(all(mine[t0 - 0] == d[t0] for t0 in d if t0 in mine) and len(d) > 0)
    (OUT / "pair_repair_audit_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
