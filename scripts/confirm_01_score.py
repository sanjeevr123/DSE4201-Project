"""
Frozen scoring of the confirmatory run (docs/preregistration_confirmatory.md; docs/THESIS_PLAN.md section 4).

  .venv/bin/python scripts/confirm_01_score.py pseudo     # DRY RUN on 2016-2019: a pipeline check, not evidence
  .venv/bin/python scripts/confirm_01_score.py holdout    # the frozen scoring of the 2020-2025 run

Same code path for both modes. The run is validated first (plan 4.10: expected day count, finite VaR/ES with ES <= VaR < 0 for the
primary arms, raw-file hash, and in hold-out mode git_head equal to the commit of the tag spec-freeze-v1). Nothing is scored if
validation fails. Only declared arms are scored (no Kendall arms, HS or EWMA, no model confidence set).

SIGN CONVENTION. Loss differences are richer minus baseline, d_t = FZ0_t(RSC_P_N) - FZ0_t(CCC_S_N); negative means the
regime-switching SPY-IEF model is better. FZ0 is lower-is-better. Z2 (Acerbi-Szekely) is sum(hit_t y_t / e_t)/(T alpha) - 1 with
returns y and negative ES e: it is 0 in expectation under a correct model and POSITIVE when realised tail returns are worse than the
forecast ES, i.e. when risk is underestimated.

PRIMARY TEST. H0: mu >= 0, H1: mu < 0, tail level alpha = 5% (a property of the forecast), test one-sided at 5%: reject if t < -1.6449.
t = mean(d)/SE with a Bartlett-kernel HAC variance, lags = floor(4 (T/100)^(2/9)). Always reported: two-sided 95% CI mean +/- 1.96 SE,
both p-values, minimum detectable differences 2.8016 SE (two-sided 5%, 80% power) and 2.4865 SE (one-sided 5%, 80% power).
Outcomes in order: O1 t < -1.6449; O4 t > +1.96; O3 lower one-sided bound mean - 1.6449 SE > -SESOI; O2 otherwise.
Output: output/confirm/<mode>/ (tables, figure, RESULT.md, manifest.json with SHA-256 of every file).
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from confirm_00_run import EXPECTED_DAYS, OUT as CONF, PRIMARY_ARMS, freeze_tag_commit, sha256_file, validate_output  # noqa: E402
from src.engine import acerbi_szekely_z2, fz0  # noqa: E402
from src.explore_inference import gw_test  # noqa: E402

ALPHAS = (0.05, 0.025)
Z_ONE, Z_TWO = 1.6449, 1.96                    # one-sided 5% critical value; two-sided 5% critical value
MDE_TWO, MDE_ONE = 2.8016, 2.4865              # 1.96 + 0.8416 ; 1.6449 + 0.8416
EXPECTED_RAW_SHA256 = "0ab8c7f353a7223e154cc3ee4cc3656c465dded45c19269fc24efba371150e29"
Z2_DRAWS, Z2_SEED, SPA_REPS = 5000, 20261104, 2000
FOCUS_YEAR = {"holdout": 2022, "pseudo": 2018}   # pseudo: arbitrary year, only to exercise the code
POWER_FILE = ROOT / "output" / "explore" / "ladder" / "power_1508_summary.csv"
SESOI_FILE = CONF / "sesoi.json"
LADDER = [("B vs A", "B|pooled|N", "A|pooled|N"), ("D vs B", "D|pooled|N", "B|pooled|N"),
          ("CCC vs B", "CCC_S_N", "B|pooled|N"), ("RSC vs D", "RSC_S_N", "D|pooled|N"),
          ("RSC vs CCC", "RSC_S_N", "CCC_S_N"), ("DCC vs RSC", "DCC_N", "RSC_S_N")]


# ------------------------------------------------------------------ forecast access
def forecast(res: dict, arm: str, alpha: float):
    """(VaR, ES) of an arm from whichever block holds it."""
    for block in ("L2", "S", "B"):
        if arm in res[block]["V"][alpha]:
            return res[block]["V"][alpha][arm], res[block]["E"][alpha][arm]
    raise KeyError(arm)


def losses(res: dict, arm: str, alpha: float) -> np.ndarray:
    v, e = forecast(res, arm, alpha)
    return fz0(res["y"], v, e, alpha)


# ------------------------------------------------------------------ inference
def hac_lrv(d: np.ndarray, lags: int | None = None) -> tuple[float, int]:
    """Bartlett-kernel long-run variance of d, the same formula as engine.dm_test."""
    T = len(d)
    if lags is None:
        lags = int(np.floor(4 * (T / 100) ** (2 / 9)))
    dc = d - d.mean()
    lrv = dc @ dc / T
    for L in range(1, lags + 1):
        lrv += 2 * (1 - L / (lags + 1)) * (dc[L:] @ dc[:-L] / T)
    return float(lrv), lags


def dm_stats(d: np.ndarray) -> dict:
    lrv, lags = hac_lrv(d)
    n, m = len(d), float(d.mean())
    if not lrv > 0:
        raise ValueError("the loss difference has zero long-run variance (identical forecasts?); the test is undefined")
    se = float(np.sqrt(lrv / n))
    t = m / se
    return dict(n=n, lags=lags, mean_diff=m, se=se, t=t, p_one_sided=float(stats.norm.cdf(t)),
                p_two_sided=float(2 * (1 - stats.norm.cdf(abs(t)))), ci_lo=m - Z_TWO * se, ci_hi=m + Z_TWO * se,
                lower_bound_one_sided=m - Z_ONE * se, mde_two_sided=MDE_TWO * se, mde_one_sided=MDE_ONE * se)


def classify(t: float, lower_bound: float, sesoi: float) -> str:
    """Outcome label, tested in this order. Negative t means the switching model has lower loss."""
    if t < -Z_ONE:
        return "O1"
    if t > Z_TWO:
        return "O4"
    if lower_bound > -sesoi:
        return "O3"
    return "O2"


def power_text() -> str:
    p = pd.read_csv(POWER_FILE)
    p = p[(p.alpha == 0.05) & (p.step == "pair_with_margins")].set_index("scenario").one_sided
    return (f"{100 * p['S1_moderate_breakdown']:.1f}% for the moderate and {100 * p['S2_strong_breakdown']:.1f}% for the strong "
            "simulated shift, one-sided 5% test, 1,508 days")


def frozen_sentence(outcome: str, s: dict, sesoi: float) -> str:
    d, a, b = f"{s['mean_diff']:+.4f}", f"{s['ci_lo']:+.4f}", f"{s['ci_hi']:+.4f}"
    if outcome == "O1":
        return ("The hold-out data provide statistical evidence at the one-sided 5% level that letting the SPY-IEF correlation switch "
                f"with the regime lowers expected FZ0 loss relative to constant correlation (difference {d}, 95% CI [{a}, {b}]). "
                f"This is one test on one six-year sample containing a single stock-bond reversal; simulated power was {power_text()}.")
    if outcome == "O4":
        return f"The hold-out data provide evidence that the switching specification has higher expected FZ0 loss ({d}, 95% CI [{a}, {b}])."
    if outcome == "O3":
        return (f"The data are inconsistent, at the one-sided 5% level, with an improvement larger than SESOI = {sesoi:g} FZ0 units. "
                "Improvements smaller than this, and any degradation, are not excluded.")
    return ("The hold-out data neither establish an improvement nor exclude one. "
            f"The estimate is {d} (95% CI [{a}, {b}]); an improvement of at least {s['mde_one_sided']:.4f} (the minimum detectable "
            "difference for the one-sided 5% test, 80% power) would have been detected with 80% probability, and smaller improvements, "
            "including none, are consistent with the data.")


# ------------------------------------------------------------------ calibration
def kupiec_lr(hits: np.ndarray, alpha: float) -> float:
    n, x = len(hits), hits.sum()
    ph = x / n
    if x == 0:
        return float(-2 * n * np.log(1 - alpha))
    if x == n:
        return float(-2 * n * np.log(alpha))
    return float(-2 * ((n - x) * np.log(1 - alpha) + x * np.log(alpha) - (n - x) * np.log(1 - ph) - x * np.log(ph)))


def christoffersen_lr(hits: np.ndarray) -> float:
    h = hits.astype(int)
    n00, n01 = np.sum((h[:-1] == 0) & (h[1:] == 0)), np.sum((h[:-1] == 0) & (h[1:] == 1))
    n10, n11 = np.sum((h[:-1] == 1) & (h[1:] == 0)), np.sum((h[:-1] == 1) & (h[1:] == 1))
    p01, p11 = n01 / max(n00 + n01, 1), n11 / max(n10 + n11, 1)
    p = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)

    def ll(a, b, pr):
        pr = min(max(pr, 1e-12), 1 - 1e-12)
        return a * np.log(1 - pr) + b * np.log(pr)

    return float(-2 * (ll(n00 + n10, n01 + n11, p) - ll(n00, n01, p01) - ll(n10, n11, p11)))


def z2_simulate(w: np.ndarray, sd: np.ndarray, mu: np.ndarray, v: np.ndarray, e: np.ndarray, alpha: float, z2_obs: float,
                draws: int = Z2_DRAWS, seed: int = Z2_SEED, chunk: int = 500) -> dict:
    """Simulation p-values of Z2 from the model's own daily predictive distribution, taking the stated VaR and ES as given.
    Each draw simulates a whole sample y_t ~ sum_k w_tk N(mu_t, sd_tk^2) and recomputes Z2. w, sd: (T, K); mu: (T,)."""
    rng = np.random.default_rng(seed)
    T, K = w.shape
    cum = np.cumsum(w, axis=1)[:, :-1]
    z2 = np.empty(draws)
    for s in range(0, draws, chunk):
        m = min(chunk, draws - s)
        comp = (rng.random((m, T))[..., None] > cum[None]).sum(-1) if K > 1 else np.zeros((m, T), int)
        y = mu[None] + sd[np.arange(T)[None], comp] * rng.standard_normal((m, T))
        z2[s:s + m] = (((y <= v[None]) * y / e[None]).sum(1)) / (T * alpha) - 1.0
    p_under = (1 + np.sum(z2 >= z2_obs)) / (1 + draws)                    # risk underestimated: Z2 large and positive
    p_over = (1 + np.sum(z2 <= z2_obs)) / (1 + draws)
    return dict(z2_sim_mean=float(z2.mean()), z2_sim_sd=float(z2.std()), p_underestimated=float(p_under),
                p_two_sided=float(min(1.0, 2 * min(p_under, p_over))))


def mixture(res: dict, arm: str):
    d = res["L2"]["diag"]
    if arm == "RSC_P_N":
        return d["mix_w"], d["mix_sd_rscp"], d["mix_mu"]
    return np.ones((len(d["mix_mu"]), 1)), d["mix_sd_ccc"][:, None], d["mix_mu"]


def calibration(res: dict) -> pd.DataFrame:
    y, rows = res["y"], []
    for a in ALPHAS:
        for k, arm in enumerate(PRIMARY_ARMS):
            v, e = forecast(res, arm, a)
            hits = (y <= v).astype(float)
            lr_uc, lr_ind = kupiec_lr(hits, a), christoffersen_lr(hits)
            z2 = acerbi_szekely_z2(y, v, e, a)
            w, sd, mu = mixture(res, arm)
            sim = z2_simulate(w, sd, mu, v, e, a, z2, seed=Z2_SEED + 10 * k + int(a * 1000))
            rows.append(dict(arm=arm, alpha=a, n=len(y), hits=int(hits.sum()), hit_rate=hits.mean(),
                             kupiec_lr=lr_uc, kupiec_p=1 - stats.chi2.cdf(lr_uc, 1), independence_lr=lr_ind,
                             independence_p=1 - stats.chi2.cdf(lr_ind, 1), cc_lr=lr_uc + lr_ind,
                             cc_p=1 - stats.chi2.cdf(lr_uc + lr_ind, 2), z2=z2, z2_p_underestimated=sim["p_underestimated"],
                             z2_p_two_sided=sim["p_two_sided"], z2_sim_mean=sim["z2_sim_mean"],
                             mean_es_exceedance_ratio=float(np.mean(y[hits == 1] / e[hits == 1])) if hits.sum() else np.nan))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ secondary analyses
def lagged_corr(prior: np.ndarray, rets: np.ndarray, window: int = 63) -> np.ndarray:
    """Correlation of SPY and IEF daily returns over the `window` returns before each forecast day (known at t-1)."""
    both = np.vstack([prior[:, :2], rets[:, :2]])
    L = len(prior)
    out = np.empty(len(rets))
    for i in range(len(rets)):
        seg = both[L + i - window:L + i]
        out[i] = np.corrcoef(seg[:, 0], seg[:, 1])[0, 1]
    return out


def ladder_table(res: dict) -> pd.DataFrame:
    rows = []
    for name, rich, base in LADDER:
        s = dm_stats(losses(res, rich, 0.05) - losses(res, base, 0.05))
        rows.append(dict(step=name, richer=rich, baseline=base, **{k: s[k] for k in
                         ("n", "mean_diff", "se", "ci_lo", "ci_hi", "t", "p_two_sided", "mde_two_sided")}))
    return pd.DataFrame(rows)


def focus_year_table(res: dict, d: np.ndarray, year: int) -> pd.DataFrame:
    m = np.asarray(pd.DatetimeIndex(res["dates"]).year == year)
    s = dm_stats(d[m]) if m.sum() > 10 else None
    return pd.DataFrame([dict(year=year, n=int(m.sum()), mean_diff=s and s["mean_diff"], se=s and s["se"], ci_lo=s and s["ci_lo"],
                              ci_hi=s and s["ci_hi"], note="interval only, not tested")])


def gw_table(res: dict, d: np.ndarray) -> pd.DataFrame:
    c = lagged_corr(res["prior_returns"], res["returns"])
    g = gw_test(d, np.c_[np.ones(len(d)), c])
    pos = c > 0
    return pd.DataFrame([dict(n=len(d), gw_stat=g["stat"], df=g["df"], gw_p=g["p"], coef_const=g["coef"][0],
                              coef_lagcorr=g["coef"][1], share_pos_corr=pos.mean(), n_pos=int(pos.sum()),
                              mean_d_pos=d[pos].mean() if pos.any() else np.nan,
                              mean_d_nonpos=d[~pos].mean() if (~pos).any() else np.nan)])


def alt_table(res: dict) -> pd.DataFrame:
    rows = []
    for label, rich, base, a in (("alpha 2.5%, Gaussian chain", "RSC_P_N", "CCC_S_N", 0.025),
                                 ("alpha 5%, Student-t chain", "RSC_P_t", "CCC_S_t", 0.05),
                                 ("alpha 2.5%, Student-t chain", "RSC_P_t", "CCC_S_t", 0.025)):
        s = dm_stats(losses(res, rich, a) - losses(res, base, a))
        rows.append(dict(analysis=label, alpha=a, richer=rich, baseline=base, **{k: s[k] for k in
                         ("n", "mean_diff", "se", "ci_lo", "ci_hi", "t", "p_two_sided", "mde_two_sided")}))
    return pd.DataFrame(rows)


def spa_table(res: dict) -> pd.DataFrame:
    from arch.bootstrap import SPA
    cands = {"B": "B|pooled|t", "D": "D|pooled|t", "RSC": "RSC_S_t", "RSC_P": "RSC_P_t"}
    L = pd.DataFrame({k: losses(res, arm, 0.05) for k, arm in cands.items()})
    bench = losses(res, "GARCHt", 0.05)
    spa = SPA(bench, L.values, reps=SPA_REPS, seed=0)
    spa.compute()
    pv = spa.pvalues
    return pd.DataFrame([dict(benchmark="GARCHt", n=len(L), reps=SPA_REPS, seed=0, p_consistent=float(pv["consistent"]),
                              p_upper=float(pv["upper"]), best_candidate=L.mean().idxmin(),
                              best_minus_benchmark=float(L.mean().min() - bench.mean()))])


def md_table(df: pd.DataFrame) -> str:
    """Markdown table without the optional tabulate dependency; floats to 5 significant figures."""
    fmt = lambda x: f"{x:.5g}" if isinstance(x, (float, np.floating)) else str(x)
    rows = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    rows += ["| " + " | ".join(fmt(x) for x in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(rows)


def diagnostics(res: dict) -> dict:
    d = res["L2"]["diag"]
    return dict(psd_repairs=int(sum(sum(v) for v in d["psd_repairs"].values())),
                psd_matrices=int(sum(len(v) for v in d["psd_repairs"].values())), margin_fallbacks=list(map(int, d["margin_fallbacks"])),
                dcc_refits=res["B"]["diag"]["dcc_refits"], dcc_fallbacks=res["B"]["diag"]["dcc_fallbacks"],
                git_head=res["git_head"], freeze_tag=res["freeze_tag"], raw_sha256=res["raw_sha256"], runtime_s=res["runtime_s"],
                python=res["python"].split()[0])


# ------------------------------------------------------------------ validation and figure
def validate_run(res: dict, mode: str) -> None:
    """Plan 4.10 item 6. Raises SystemExit/AssertionError; nothing is scored after a failure."""
    assert res["mode"] == mode, f"pickle is mode {res['mode']}, scoring {mode}"
    validate_output(res, mode)
    assert res["raw_sha256"] == EXPECTED_RAW_SHA256, "raw file hash differs from the frozen value"
    assert "diag" in res["L2"] and "prior_returns" in res, "run lacks the diagnostics the scorer needs"
    assert len(res["prior_returns"]) >= 64, "fewer than 64 prior returns saved"
    if mode == "holdout":
        tag = freeze_tag_commit()
        assert tag is not None, "tag spec-freeze-v1 does not exist"
        assert res["git_head"] == tag == res["freeze_tag"], "run was not made at the tagged commit"


def cumulative_plot(res: dict, d: np.ndarray, year: int, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    dates = pd.DatetimeIndex(res["dates"])
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(dates, np.cumsum(d), color="#111111", lw=1.4)
    ax.axhline(0, color="#777777", lw=0.8)
    ax.axvspan(pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"), color="#d4d4d4", zorder=0, label=f"{year}")
    ax.set_xlabel("Forecast date")
    ax.set_ylabel("Cumulative FZ0 difference (loss units)")
    ax.set_title("Cumulative d_t = FZ0(RSC_P_N) - FZ0(CCC_S_N), tail level 5%; falling = switching model better", fontsize=9, loc="left")
    ax.legend(frameon=False, loc="best")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------ main
def score(res: dict, mode: str, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    validate_run(res, mode)
    sesoi = json.loads(SESOI_FILE.read_text())["sesoi_declared"]
    d = losses(res, "RSC_P_N", 0.05) - losses(res, "CCC_S_N", 0.05)
    s = dm_stats(d)
    outcome = classify(s["t"], s["lower_bound_one_sided"], sesoi)
    primary = dict(mode=mode, outcome=outcome, sesoi=sesoi, sentence=frozen_sentence(outcome, s, sesoi),
                   sesoi_comparison=dict(lower_bound=s["lower_bound_one_sided"], excludes_improvement_larger_than_sesoi=bool(s["lower_bound_one_sided"] > -sesoi)),
                   **s)
    (out / "primary.json").write_text(json.dumps(primary, indent=2))
    tables = {"calibration": calibration(res), "secondary_ladder": ladder_table(res),
              "secondary_focus_year": focus_year_table(res, d, FOCUS_YEAR[mode]), "secondary_gw_conditional": gw_table(res, d),
              "secondary_alpha_and_t_chain": alt_table(res), "secondary_spa": spa_table(res)}
    for name, t in tables.items():
        t.to_csv(out / f"{name}.csv", index=False)
    diag = diagnostics(res)
    (out / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    cumulative_plot(res, d, FOCUS_YEAR[mode], out / "cumulative_d.png")
    banner = "DRY RUN (2016-2019): a pipeline check; it enters no argument for the hypothesis.\n\n" if mode == "pseudo" else ""
    md = [f"# Result ({mode})", "", banner + f"**Outcome: {outcome}**", "", primary["sentence"], "",
          "## Primary test: RSC_P_N vs CCC_S_N, tail level 5%, one-sided 5% test (preregistered)", "",
          "Loss difference richer minus baseline; negative means the switching model is better.", "",
          f"| n | mean diff | HAC SE | 95% CI (two-sided) | t | p (one-sided) | p (two-sided) | lower 95% one-sided bound | MDE two-sided (2.8016 SE) | MDE one-sided (2.4865 SE) |",
          "|---|---|---|---|---|---|---|---|---|---|",
          f"| {s['n']} | {s['mean_diff']:+.5f} | {s['se']:.5f} | [{s['ci_lo']:+.5f}, {s['ci_hi']:+.5f}] | {s['t']:+.3f} | "
          f"{s['p_one_sided']:.4f} | {s['p_two_sided']:.4f} | {s['lower_bound_one_sided']:+.5f} | {s['mde_two_sided']:.5f} | {s['mde_one_sided']:.5f} |",
          "", f"SESOI = {sesoi:g}; lower bound {'above' if primary['sesoi_comparison']['excludes_improvement_larger_than_sesoi'] else 'not above'} -{sesoi:g}.",
          f"Simulated power at 1,508 days: {power_text()}.", "", "## Secondary (unadjusted, labelled secondary)", ""]
    for name, t in tables.items():
        md += [f"### {name}", "", md_table(t), ""]
    md += ["### diagnostics", "", "```", json.dumps(diag, indent=2), "```", ""]
    (out / "RESULT.md").write_text("\n".join(md))
    (out / "manifest.json").write_text(json.dumps({p.name: sha256_file(p) for p in sorted(out.iterdir())
                                                   if p.is_file() and p.name != "manifest.json"}, indent=2))
    return primary


def main(mode: str):
    res = pickle.load(open(CONF / f"{mode}_forecasts.pkl", "rb"))
    p = score(res, mode, CONF / mode)
    print(f"{mode}: outcome {p['outcome']}  mean {p['mean_diff']:+.5f}  SE {p['se']:.5f}  t {p['t']:+.3f}  -> {CONF / mode}")
    print(p["sentence"])


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in EXPECTED_DAYS:
        sys.exit(__doc__)
    main(sys.argv[1])
