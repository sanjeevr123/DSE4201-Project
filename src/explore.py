"""
Helpers for the exploratory phase (regime-definition and universe screens).

Descriptive only: full-sample (smoothed) regime weights, no forecasting.
Everything here is restricted to <= 2019-12-31; 2020-2025 is the
confirmatory hold-out (docs/decisions_log.md).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.data import RAW_DATA_DIR
from src.engine import corr_from_cov, weighted_cov

EXPLORE_END = pd.Timestamp("2019-12-31")
SQRT252 = np.sqrt(252)


def load_explore_returns() -> tuple[pd.DataFrame, pd.Series]:
    """Daily simple returns for all ETFs (NaN before inception) and the VIX level."""
    px = pd.read_csv(RAW_DATA_DIR / "explore_etfs_2004_2019.csv",
                     index_col=0, parse_dates=True)
    assert px.index.max() <= EXPLORE_END, "exploration data leaked past 2019-12-31"
    vix = px.pop("^VIX")
    return px.pct_change(), vix


def _vol(d: np.ndarray, C: np.ndarray, w: np.ndarray) -> float:
    return float(np.sqrt(w @ (np.outer(d, d) * C) @ w) * SQRT252)


def regime_decomposition(R: np.ndarray, gamma: np.ndarray, w: np.ndarray | None = None,
                         calm: int = 0, stress: int = 1) -> dict:
    """Calm->stress portfolio-vol change, split into a volatility and a
    correlation channel with a 2-player Shapley value (as in WP3)."""
    n = R.shape[1]
    w = np.ones(n) / n if w is None else w
    Sc, _ = weighted_cov(R, gamma[:, calm] + 1e-12)
    Ss, _ = weighted_cov(R, gamma[:, stress] + 1e-12)
    Cc, dc = corr_from_cov(Sc)
    Cs, ds = corr_from_cov(Ss)
    base, v_only, c_only, both = _vol(dc, Cc, w), _vol(ds, Cc, w), _vol(dc, Cs, w), _vol(ds, Cs, w)
    denom = both - base
    vol_share = 0.5 * ((v_only - base) + (both - c_only)) / denom if abs(denom) > 1e-12 else np.nan
    iu = np.triu_indices(n, 1)
    return {
        "calm_vol": base, "stress_vol": both,
        "vol_share": float(vol_share), "corr_share": float(1 - vol_share),
        "avg_pair_corr_calm": float(Cc[iu].mean()), "avg_pair_corr_stress": float(Cs[iu].mean()),
        "d_avg_pair_corr": float(Cs[iu].mean() - Cc[iu].mean()),
        "corr_calm": Cc, "corr_stress": Cs,
    }


def block_bootstrap(R: np.ndarray, gamma: np.ndarray, stat, n_boot: int = 300,
                    block: int = 21, seed: int = 0) -> np.ndarray:
    """Circular block bootstrap over days with regime weights held fixed
    (captures sampling noise in the conditional moments, not HMM uncertainty)."""
    rng = np.random.default_rng(seed)
    T = len(R)
    nb = int(np.ceil(T / block))
    out = []
    for _ in range(n_boot):
        starts = rng.integers(0, T, nb)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:T] % T
        try:
            out.append(stat(R[idx], gamma[idx]))
        except Exception:
            out.append(np.nan)
    return np.array(out, dtype=float)


def run_lengths(states: np.ndarray, target: int = 1) -> np.ndarray:
    """Lengths of consecutive runs where states == target."""
    s = (states == target).astype(int)
    d = np.diff(np.r_[0, s, 0])
    return np.where(d == -1)[0] - np.where(d == 1)[0]


def load_rates() -> pd.DataFrame:
    """10y yield (^TNX, percent) from 1986 and MOVE index from 2002, <= 2019-12-31."""
    df = pd.read_csv(RAW_DATA_DIR / "explore_rates_1986_2019.csv", index_col=0, parse_dates=True)
    assert df.index.max() <= EXPLORE_END, "exploration data leaked past 2019-12-31"
    return df
