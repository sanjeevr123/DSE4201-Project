"""
Exploratory step 1: which ETF universes have a calm->stress CORRELATION shift?

The pilot (SPY/IEF/GLD, 2010-2015) found no correlation breakdown, so the
D-vs-B test had nothing to detect. This screen asks, cheaply and
descriptively (no forecasting, no 2020+ data), where a correlation channel
exists. Regimes = 2-state SPY Gaussian HMM, same as the pilot.

Two windows: "full" (from first common date, includes 2008) and "post2010".

Run: .venv/bin/python scripts/explore_01_universe_screen.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine import fit_hmm  # noqa: E402
from src.explore import block_bootstrap, load_explore_returns, regime_decomposition  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output" / "explore"
OUT.mkdir(parents=True, exist_ok=True)

UNIVERSES = {
    "U1 pilot: SPY/IEF/GLD": ["SPY", "IEF", "GLD"],
    "U2 SPY/TLT/GLD": ["SPY", "TLT", "GLD"],
    "U3 SPY/IEF/HYG (credit)": ["SPY", "IEF", "HYG"],
    "U4 SPY/EFA/EEM (global eq)": ["SPY", "EFA", "EEM"],
    "U5 SPY/IEF/GLD/EEM": ["SPY", "IEF", "GLD", "EEM"],
    "U6 SPY/IEF/GLD/DBC/VNQ": ["SPY", "IEF", "GLD", "DBC", "VNQ"],
    "U7 8-asset multi-asset": ["SPY", "TLT", "IEF", "GLD", "HYG", "EEM", "VNQ", "DBC"],
    "U8 sectors XLU/XLK/XLF/XLE": ["XLU", "XLK", "XLF", "XLE"],
    "U9 SPY/LQD/GLD": ["SPY", "LQD", "GLD"],
    "U10 risk assets HYG/EEM/VNQ/DBC": ["HYG", "EEM", "VNQ", "DBC"],
}
SINGLES = ["IEF", "TLT", "LQD", "GLD", "HYG", "EEM", "EFA", "VNQ", "DBC",
           "XLU", "XLK", "XLF", "XLE"]
WINDOWS = {"full": None, "post2010": "2010-01-01"}


def hmm_gamma(spy: np.ndarray) -> np.ndarray:
    return fit_hmm(spy).predict_proba(spy.reshape(-1, 1))


def screen(cols: list[str], R_all: pd.DataFrame, start: str | None, boot: bool = True) -> dict:
    df = R_all[sorted(set(cols) | {"SPY"})].dropna()
    if start:
        df = df.loc[start:]
    gamma = hmm_gamma(df["SPY"].values)
    X = df[cols].values
    d = regime_decomposition(X, gamma)
    res = {"start": str(df.index[0].date()), "n_days": len(df),
           "stress_share": float(gamma[:, 1].mean())}
    res.update({k: v for k, v in d.items() if not k.startswith("corr_calm") and not k.startswith("corr_stress")})
    if boot:
        bs = block_bootstrap(X, gamma, lambda r, g: regime_decomposition(r, g)["d_avg_pair_corr"])
        res["d_avg_pair_corr_ci90"] = [float(np.nanpercentile(bs, 5)), float(np.nanpercentile(bs, 95))]
        bs2 = block_bootstrap(X, gamma, lambda r, g: regime_decomposition(r, g)["corr_share"])
        res["corr_share_ci90"] = [float(np.nanpercentile(bs2, 5)), float(np.nanpercentile(bs2, 95))]
    return res


def main() -> None:
    R, _ = load_explore_returns()
    out = {"universes": {}, "singles_vs_spy": {}}

    for name, cols in UNIVERSES.items():
        out["universes"][name] = {"assets": cols}
        for wname, start in WINDOWS.items():
            out["universes"][name][wname] = screen(cols, R, start)
            print(f"{name:34s} {wname:8s} corr_share="
                  f"{out['universes'][name][wname]['corr_share']:+.2f}  "
                  f"dCorr={out['universes'][name][wname]['d_avg_pair_corr']:+.2f}")

    # single asset vs SPY: calm vs stress correlation with SPY
    for a in SINGLES:
        out["singles_vs_spy"][a] = {}
        for wname, start in WINDOWS.items():
            df = R[["SPY", a]].dropna()
            if start:
                df = df.loc[start:]
            gamma = hmm_gamma(df["SPY"].values)
            X = df.values
            d = regime_decomposition(X, gamma)
            f = lambda r, g, k=0: regime_decomposition(r, g)["corr_stress"][0, 1] - regime_decomposition(r, g)["corr_calm"][0, 1]
            bs = block_bootstrap(X, gamma, f)
            out["singles_vs_spy"][a][wname] = {
                "corr_calm": float(d["corr_calm"][0, 1]), "corr_stress": float(d["corr_stress"][0, 1]),
                "delta": float(d["corr_stress"][0, 1] - d["corr_calm"][0, 1]),
                "delta_ci90": [float(np.nanpercentile(bs, 5)), float(np.nanpercentile(bs, 95))],
                "start": str(df.index[0].date()),
            }

    (OUT / "universe_screen.json").write_text(json.dumps(out, indent=2))
    print("wrote", OUT / "universe_screen.json")


if __name__ == "__main__":
    main()
