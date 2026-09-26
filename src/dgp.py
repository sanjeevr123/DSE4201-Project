"""
WP2 data-generating processes: a 2-state Markov-switching multivariate
Student-t model for 3 assets (equity-like, bond-like, gold-like), used to
test whether the pilot design can detect the correlation-breakdown effect
at all.

Two calibrations, per docs/PILOT_PROMPT.md:
  - "stylised": the assumed, hand-set parameters given in config/pilot.yaml
    (wp2 section), not estimated from data.
  - "calibrated": vols/correlations/transition probabilities estimated
    in-sample from the 2004-2015 archived real data (HMM-weighted moments),
    as a second, independent calibration check.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.config import get_config
from src.data import (
    RAW_DATA_DIR,
    assert_no_locked_period_leakage,
    build_adjusted_price_panel,
    raw_snapshot_exists_for_range,
)
from src.engine import fit_hmm, weighted_cov, corr_from_cov

REPO_ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_CACHE = REPO_ROOT / "data" / "metadata" / "wp2_calibrated_dgp.json"


def corr_matrix(a: float, b: float, c: float) -> np.ndarray:
    """3x3 correlation matrix from (eq-bond, eq-gold, bond-gold) pairwise correlations."""
    return np.array([[1, a, b], [a, 1, c], [b, c, 1]])


def cov_matrix(vol: np.ndarray, corr: np.ndarray) -> np.ndarray:
    return np.outer(vol, vol) * corr


class DGPParams:
    """Container for one DGP calibration's parameters."""

    def __init__(self, vol_calm, vol_stress, p_calm_calm, p_stress_stress, calm_corr, df):
        self.vol_calm = np.asarray(vol_calm)
        self.vol_stress = np.asarray(vol_stress)
        self.transmat = np.array([[p_calm_calm, 1 - p_calm_calm],
                                   [1 - p_stress_stress, p_stress_stress]])
        self.calm_corr = np.asarray(calm_corr)  # 3x3
        self.df = df


def stylised_params() -> DGPParams:
    wp2 = get_config()["wp2"]
    return DGPParams(
        vol_calm=wp2["vol_calm"],
        vol_stress=wp2["vol_stress"],
        p_calm_calm=wp2["p_calm_calm"],
        p_stress_stress=wp2["p_stress_stress"],
        calm_corr=corr_matrix(*wp2["calm_corr"]),
        df=wp2["df"],
    )


def calibrate_from_real_data(force_recompute: bool = False) -> DGPParams:
    """In-sample HMM-weighted calibration of vol/correlation/transition
    parameters from the archived 2004-2015 real data. Cached to
    data/metadata/wp2_calibrated_dgp.json since it only needs computing once
    and the pilot must never touch data beyond the locked-period cutoff, so
    this fit is done exactly once, deliberately, not on every call.
    """
    if not force_recompute and CALIBRATION_CACHE.exists():
        with open(CALIBRATION_CACHE) as f:
            saved = json.load(f)
        return DGPParams(
            vol_calm=saved["vol_calm"], vol_stress=saved["vol_stress"],
            p_calm_calm=saved["p_calm_calm"], p_stress_stress=saved["p_stress_stress"],
            calm_corr=np.array(saved["calm_corr"]), df=saved["df"],
        )

    cfg = get_config()
    tickers = cfg["data"]["tickers"]
    cutoff = cfg["dates"]["pilot_forecast_end"]  # 2015-12-31

    filename = raw_snapshot_exists_for_range(cfg["data"]["download_start"])
    if filename is None:
        raise RuntimeError(
            "No archived raw snapshot found for the WP0 download start date. "
            "Run `python -m src.run_pilot` (WP0) before calibrating the DGP."
        )
    raw = pd.read_csv(RAW_DATA_DIR / filename, index_col="Date", parse_dates=True)
    panel = build_adjusted_price_panel(raw, tickers)
    panel = panel.loc[:cutoff].dropna()
    assert_no_locked_period_leakage(panel, cutoff=cutoff)

    R = panel.pct_change().dropna()
    Rv = R.values
    df_t = 6  # Student-t degrees of freedom kept fixed to match the stylised DGP family

    hmm = fit_hmm(Rv[:, 0])
    gamma = hmm.predict_proba(Rv[:, :1])

    S_calm, _ = weighted_cov(Rv, gamma[:, 0])
    S_stress, _ = weighted_cov(Rv, gamma[:, 1])
    C_calm, d_calm = corr_from_cov(S_calm)
    _, d_stress = corr_from_cov(S_stress)

    p_calm_calm = float(hmm.transmat_[0, 0])
    p_stress_stress = float(hmm.transmat_[1, 1])

    saved = {
        "vol_calm": d_calm.tolist(),
        "vol_stress": d_stress.tolist(),
        "p_calm_calm": p_calm_calm,
        "p_stress_stress": p_stress_stress,
        "calm_corr": C_calm.tolist(),
        "df": df_t,
        "note": (
            "Calibrated in-sample on 2004-11-18..2015-12-31 real SPY/IEF/GLD "
            "returns (HMM-weighted regime moments). Stress-state correlation "
            "is NOT calibrated here -- scenarios S0-S3 supply the stress "
            "correlation being tested, exactly as for the stylised DGP."
        ),
    }
    CALIBRATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CALIBRATION_CACHE, "w") as f:
        json.dump(saved, f, indent=2)

    return DGPParams(
        vol_calm=d_calm, vol_stress=d_stress,
        p_calm_calm=p_calm_calm, p_stress_stress=p_stress_stress,
        calm_corr=C_calm, df=df_t,
    )


def get_dgp_params(name: str) -> DGPParams:
    if name == "stylised":
        return stylised_params()
    if name == "calibrated":
        return calibrate_from_real_data()
    raise ValueError(f"Unknown DGP calibration: {name!r}")


def simulate(
    params: DGPParams,
    stress_corr: np.ndarray,
    T: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Simulate T days from the 2-state Markov-switching multivariate-t DGP.

    Returns (R, S, pred, true_covs):
      R: T x 3 simulated returns.
      S: T true regime labels (0=calm, 1=stress).
      pred: T x 2 oracle one-step predictive state probabilities P(S_t|S_{t-1}),
            known exactly since this is the true generating chain.
      true_covs: {"B": [cov0, cov1], "D": [cov0, cov1]} oracle covariances.
        Oracle_B deliberately keeps the calm correlation in BOTH states (the
        vol-only truth matching model B's own structural assumption), so
        that Oracle_D - Oracle_B isolates the correlation channel under
        perfect regime knowledge. See src/engine.py's build_variants
        docstring for the same B/D distinction under estimation.
    """
    P = params.transmat
    S = np.empty(T, dtype=int)
    S[0] = 0
    for t in range(1, T):
        S[t] = rng.random() < P[S[t - 1], 1]

    cov_calm = cov_matrix(params.vol_calm, params.calm_corr)
    cov_stress = cov_matrix(params.vol_stress, stress_corr)
    covs = [cov_calm, cov_stress]
    L = [np.linalg.cholesky(c) for c in covs]

    z = rng.standard_normal((T, 3))
    g = rng.chisquare(params.df, T) / params.df
    z = z / np.sqrt(g)[:, None] * np.sqrt((params.df - 2) / params.df)  # unit-variance t

    R = np.empty((T, 3))
    for k in range(2):
        m = S == k
        R[m] = z[m] @ L[k].T

    pred = np.vstack([[1.0, 0.0], P[S[:-1]]])
    true_covs = {
        "B": [cov_calm, cov_matrix(params.vol_stress, params.calm_corr)],
        "D": covs,
    }
    return R, S, pred, true_covs
