"""
WP3: real-data pilot on the locked-safe 2010-2015 validation window.

Loads the WP0-archived SPY/IEF/GLD raw data, truncates strictly at
2015-12-31 (asserting no locked-period leakage), and produces:
  - in-sample descriptive regime statistics (2004-2015) and a
    volatility/correlation Shapley attribution of the calm->stress
    portfolio-vol increase;
  - a 2010-2015 walk-forward backtest and scoring table at both alphas;
  - stability diagnostics (regime collapse/flip flags per refit, stress-share
    distribution, window/refit-frequency sensitivity of the D-B result);
  - three named-episode diagnostics inside 2010-2015.

Figures are produced by scripts/wp3_run_real_data_pilot.py, not here, to
keep this module import-light and testable without matplotlib side effects.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from src.config import get_config
from src.data import (
    RAW_DATA_DIR,
    assert_no_locked_period_leakage,
    build_adjusted_price_panel,
    raw_snapshot_exists_for_range,
)
from src.engine import (
    DEFAULT_DM_PAIRS,
    christoffersen_ind,
    corr_from_cov,
    fit_hmm,
    fz0,
    score,
    walk_forward,
    weighted_cov,
)

W = np.ones(3) / 3

EPISODES = {
    "2011_us_downgrade_euro_crisis": ("2011-08-01", "2011-10-31"),
    "2013_taper_tantrum": ("2013-05-01", "2013-09-30"),
    "2015_august_selloff": ("2015-08-01", "2015-08-31"),
}


def load_pilot_prices() -> pd.DataFrame:
    """Load the WP0-archived raw data, build the adjusted-price panel, and
    truncate strictly at the locked-period cutoff."""
    cfg = get_config()
    tickers = cfg["data"]["tickers"]
    cutoff = cfg["dates"]["pilot_forecast_end"]

    filename = raw_snapshot_exists_for_range(cfg["data"]["download_start"])
    if filename is None:
        raise RuntimeError(
            "No archived raw snapshot found. Run `python -m src.run_pilot` (WP0) first."
        )
    raw = pd.read_csv(RAW_DATA_DIR / filename, index_col="Date", parse_dates=True)
    panel = build_adjusted_price_panel(raw, tickers)
    panel = panel.loc[:cutoff].dropna()
    assert_no_locked_period_leakage(panel, cutoff=cutoff)
    return panel


def descriptive_regime_stats(R: pd.DataFrame) -> dict:
    """In-sample (full 2004-2015) regime-conditional moments and vol
    attribution. Descriptive only -- a single full-sample HMM fit, distinct
    from the rolling walk-forward fits used for forecasting."""
    Rv = R.values
    hmm = fit_hmm(Rv[:, 0])
    gamma = hmm.predict_proba(Rv[:, :1])

    stress_share = float(gamma[:, 1].mean())
    calm_duration = float(1 / (1 - hmm.transmat_[0, 0]))
    stress_duration = float(1 / (1 - hmm.transmat_[1, 1]))

    regimes = {}
    for k, name in enumerate(["calm", "stress"]):
        S, _ = weighted_cov(Rv, gamma[:, k])
        C, d = corr_from_cov(S)
        regimes[name] = {
            "annualised_vol": {t: float(d[i] * np.sqrt(252)) for i, t in enumerate(R.columns)},
            "correlation": C.tolist(),
        }

    Sc, _ = weighted_cov(Rv, gamma[:, 0])
    Ss, _ = weighted_cov(Rv, gamma[:, 1])
    Cc, dc = corr_from_cov(Sc)
    Cs, ds = corr_from_cov(Ss)
    vol = lambda d, C: float(np.sqrt(W @ (np.outer(d, d) * C) @ W) * np.sqrt(252))
    base, v_only, c_only, both = vol(dc, Cc), vol(ds, Cc), vol(dc, Cs), vol(ds, Cs)
    vol_share = 0.5 * ((v_only - base) + (both - c_only)) / (both - base)

    return {
        "stress_share_full_sample": stress_share,
        "expected_calm_duration_days": calm_duration,
        "expected_stress_duration_days": stress_duration,
        "regime_conditional_moments": regimes,
        "portfolio_vol_attribution": {
            "calm_annualised_vol": base,
            "vol_only_change_annualised_vol": v_only,
            "corr_only_change_annualised_vol": c_only,
            "both_change_annualised_vol": both,
            "volatility_share_of_stress_increase_shapley": float(vol_share),
            "correlation_share_of_stress_increase_shapley": float(1 - vol_share),
        },
    }


def walk_forward_backtest(R: pd.DataFrame, alphas: Iterable[float]) -> dict:
    """2010-2015 walk-forward backtest and scoring table at each alpha."""
    cfg = get_config()
    pilot_start = cfg["dates"]["pilot_forecast_start"]
    dates = R.index
    Rv = R.values
    start = int(np.searchsorted(dates, pd.Timestamp(pilot_start)))
    window = min(cfg["model"]["window"], start)

    out = {}
    for alpha in alphas:
        res = walk_forward(Rv, W, start=start, window=window, alpha=alpha,
                            refit=cfg["model"]["refit"], garch_refit=cfg["model"]["garch_refit"],
                            hs_window=cfg["model"]["hs_window"], lam=cfg["model"]["ewma_lambda"])
        sc = score(res, alpha, pairs=DEFAULT_DM_PAIRS)
        table = {}
        for m in res["V"]:
            hits = (res["y"] <= res["V"][m])
            table[m] = {
                "fz0_loss": float(sc["loss"][m]),
                "hit_rate": float(sc["hit"][m]),
                "kupiec_p": float(sc["kupiec_p"][m]),
                "christoffersen_p": float(christoffersen_ind(hits)),
            }
        out[str(alpha)] = {
            "table": table,
            "dm_tests": {k: list(v) for k, v in sc["dm"].items()},
            "window": window,
            "start_date": str(dates[start].date()),
        }
    return out


def _walk_forward_result(R: pd.DataFrame, alpha: float = 0.05, window: int = 1260, refit: int = 21) -> tuple[dict, pd.DatetimeIndex]:
    cfg = get_config()
    pilot_start = cfg["dates"]["pilot_forecast_start"]
    dates = R.index
    Rv = R.values
    start = int(np.searchsorted(dates, pd.Timestamp(pilot_start)))
    win = min(window, start)
    res = walk_forward(Rv, W, start=start, window=win, refit=refit, alpha=alpha)
    return res, dates[res["idx"]]


def stability_diagnostics(R: pd.DataFrame) -> dict:
    """Per-refit regime-collapse/instability flags, stress-share
    distribution, and window/refit-frequency sensitivity of the D-B result.
    Reported as sensitivity checks, not as tuning: no parameter choice here
    feeds back into the primary walk-forward backtest above."""
    cfg = get_config()
    pilot_start = cfg["dates"]["pilot_forecast_start"]
    dates = R.index
    Rv = R.values
    start = int(np.searchsorted(dates, pd.Timestamp(pilot_start)))
    window = min(cfg["model"]["window"], start)
    refit = cfg["model"]["refit"]

    hmm = None
    records = []
    prev_stress_share = None
    for t0 in range(start, len(Rv), refit):
        win = slice(t0 - window, t0)
        x = Rv[win, 0]
        hmm = fit_hmm(x, prev=hmm, seed=0)
        gamma = hmm.predict_proba(x.reshape(-1, 1))
        stress_share = float(gamma[:, 1].mean())
        vol_ratio = float(np.sqrt(hmm.covars_.ravel()[1] / hmm.covars_.ravel()[0]))
        collapsed = stress_share < 0.01 or stress_share > 0.99 or vol_ratio < 1.2
        large_jump = (
            prev_stress_share is not None and abs(stress_share - prev_stress_share) > 0.3
        )
        records.append({
            "refit_date": str(dates[t0].date()),
            "stress_share_in_window": stress_share,
            "vol_ratio_stress_over_calm": vol_ratio,
            "collapsed": bool(collapsed),
            "large_jump_from_prev_refit": bool(large_jump),
        })
        prev_stress_share = stress_share

    stress_shares = [r["stress_share_in_window"] for r in records]
    n_collapsed = sum(r["collapsed"] for r in records)
    n_flips = sum(r["large_jump_from_prev_refit"] for r in records)

    sensitivity = {}
    for win_len in [756, 1260]:
        for refit_freq in [5, 21, 63]:
            key = f"window{win_len}_refit{refit_freq}"
            try:
                res, _ = _walk_forward_result(R, alpha=0.05, window=win_len, refit=refit_freq)
                sc = score(res, 0.05, pairs=(("D", "B"),))
                sensitivity[key] = {
                    "mean_fz0_diff_D_minus_B": float(sc["loss"]["D"] - sc["loss"]["B"]),
                    "dm_D_B_t": float(sc["dm"]["D-B"][0]),
                    "dm_D_B_p": float(sc["dm"]["D-B"][1]),
                }
            except Exception as e:
                # A genuine finding, not a bug to hide: some window/refit
                # combinations (short window + frequent refits) cause the
                # warm-started HMM to numerically collapse on real data.
                # Reported as-is, per "sensitivity checks, NOT tuning."
                sensitivity[key] = {"error": f"{type(e).__name__}: {e}"}

    return {
        "n_refits": len(records),
        "n_collapsed_refits": n_collapsed,
        "collapsed_refit_share": n_collapsed / len(records) if records else float("nan"),
        "n_large_jump_refits": n_flips,
        "stress_share_distribution": {
            "mean": float(np.mean(stress_shares)),
            "std": float(np.std(stress_shares)),
            "min": float(np.min(stress_shares)),
            "max": float(np.max(stress_shares)),
        },
        "per_refit_records": records,
        "window_refit_sensitivity": sensitivity,
    }


def episode_diagnostics(R: pd.DataFrame) -> dict:
    """Within named-episode stats from the primary (window=1260, refit=21,
    alpha=0.05) walk-forward result."""
    res, dates = _walk_forward_result(R, alpha=0.05)
    stress_prob = pd.Series(res["stress_prob"], index=dates)
    y = pd.Series(res["y"], index=dates)
    V = {m: pd.Series(v, index=dates) for m, v in res["V"].items()}

    out = {}
    for name, (ep_start, ep_end) in EPISODES.items():
        mask = (dates >= ep_start) & (dates <= ep_end)
        if mask.sum() == 0:
            out[name] = {"n_days": 0, "note": "no walk-forward days in this window"}
            continue
        y_ep = y[mask]
        out[name] = {
            "n_days": int(mask.sum()),
            "date_range": [ep_start, ep_end],
            "mean_stress_prob": float(stress_prob[mask].mean()),
            "max_stress_prob": float(stress_prob[mask].max()),
            "mean_realised_return": float(y_ep.mean()),
            "worst_realised_return": float(y_ep.min()),
            "D_hits": int((y_ep <= V["D"][mask]).sum()),
            "B_hits": int((y_ep <= V["B"][mask]).sum()),
            "mean_fz0_D_minus_B": float(
                np.mean(
                    fz0(y_ep.values, V["D"][mask].values, res["E"]["D"][mask], 0.05)
                    - fz0(y_ep.values, V["B"][mask].values, res["E"]["B"][mask], 0.05)
                )
            ),
        }
    return out
