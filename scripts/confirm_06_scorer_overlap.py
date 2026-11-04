"""
Dry-run step 5: rows of the dry-run scorer output (output/confirm/pseudo/) that overlap existing exploration results are compared with
them. Overlap: the six ladder steps against `ladder_dm_table.csv` (universe U1_pilot, period 2016_2019, pooled mean, Gaussian chain,
tail level 5%) and the primary comparison against `routes_dm_table.csv` (HMM_SPY2, pseudo_2016_2019, RSC_P_N vs CCC_S_N, both tail
levels). The two paths differ in the HMM chain start (cold in 2016 against warm since 2010) and the margin-refit anchor, and the two
downloads differ by up to 2.5e-6 in daily returns, so exact agreement is not expected (docs/THESIS_PLAN.md 4.11). Pipeline check only.

  .venv/bin/python scripts/confirm_06_scorer_overlap.py
Output: output/confirm/pseudo_scorer_vs_exploration.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONF, EXP = ROOT / "output" / "confirm", ROOT / "output" / "explore"
STEP = {"B vs A": "regime_vol", "D vs B": "static_corr", "CCC vs B": "margin_pooledcorr", "RSC vs D": "margin_effect",
        "RSC vs CCC": "corr_with_margins", "DCC vs RSC": "regime_vs_smooth"}


def main():
    mine = pd.read_csv(CONF / "pseudo" / "secondary_ladder.csv").set_index("step")
    lad = pd.read_csv(EXP / "ladder" / "ladder_dm_table.csv")
    lad = lad[(lad.universe == "U1_pilot") & (lad.period == "2016_2019") & (lad.mean_set == "pooled") & (lad.chain == "N")
              & (lad.alpha == 0.05)].set_index("step")
    rows = []
    for name, key in STEP.items():
        rows.append(dict(row=f"ladder {name}", n_dryrun=int(mine.loc[name, "n"]), n_exploration=int(lad.loc[key, "n"]),
                         mean_diff_dryrun=mine.loc[name, "mean_diff"], mean_diff_exploration=lad.loc[key, "mean_diff"],
                         se_dryrun=mine.loc[name, "se"], se_exploration=lad.loc[key, "se"],
                         t_dryrun=mine.loc[name, "t"], t_exploration=lad.loc[key, "t"]))
    prim = pd.read_json(CONF / "pseudo" / "primary.json", typ="series")
    rt = pd.read_csv(EXP / "routes" / "routes_dm_table.csv")
    rt = rt[(rt.provider == "HMM_SPY2") & (rt.period == "pseudo_2016_2019") & (rt["first"] == "RSC_P_N") & (rt.second == "CCC_S_N")]
    r5 = rt[rt.alpha == 0.05].iloc[0]
    rows.append(dict(row="primary RSC_P_N vs CCC_S_N, tail 5%", n_dryrun=int(prim["n"]), n_exploration=int(r5.n),
                     mean_diff_dryrun=prim["mean_diff"], mean_diff_exploration=r5.mean_diff, se_dryrun=prim["se"],
                     se_exploration=abs(r5.mean_diff / r5.t), t_dryrun=prim["t"], t_exploration=r5.t))
    alt = pd.read_csv(CONF / "pseudo" / "secondary_alpha_and_t_chain.csv")
    a25 = alt[(alt.alpha == 0.025) & (alt.richer == "RSC_P_N")].iloc[0]
    r25 = rt[rt.alpha == 0.025].iloc[0]
    rows.append(dict(row="RSC_P_N vs CCC_S_N, tail 2.5%", n_dryrun=int(a25.n), n_exploration=int(r25.n),
                     mean_diff_dryrun=a25.mean_diff, mean_diff_exploration=r25.mean_diff, se_dryrun=a25.se,
                     se_exploration=abs(r25.mean_diff / r25.t), t_dryrun=a25.t, t_exploration=r25.t))
    df = pd.DataFrame(rows)
    df["abs_diff_mean_diff"] = (df.mean_diff_dryrun - df.mean_diff_exploration).abs()
    df["abs_diff_t"] = (df.t_dryrun - df.t_exploration).abs()
    df.to_csv(CONF / "pseudo_scorer_vs_exploration.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 20, "display.float_format", lambda x: f"{x:.5f}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
