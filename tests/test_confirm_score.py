"""Tests for scripts/confirm_01_score.py on synthetic data with known answers: HAC arithmetic, the one-sided sign, the four outcomes,
CI and minimum detectable difference multipliers, Z2 sign convention and simulation p-values, coverage tests against the engine,
no look-ahead in the lagged correlation, run validation, and an end-to-end run that is reproducible."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import confirm_00_run as c0  # noqa: E402
import confirm_01_score as sc  # noqa: E402
from src.engine import christoffersen_ind, dm_test, kupiec  # noqa: E402


# ------------------------------------------------------------------ HAC, sign, CI, MDE
def test_hac_known_answer_alternating_series():
    # d = 0.5 + (+1, -1, ...), n = 100, lags = 4: autocovariances (n-L)/n (-1)^L, lrv = 1 + 2*(-0.792+0.588-0.388+0.192) = 0.2
    d = 0.5 + np.tile([1.0, -1.0], 50)
    lrv, lags = sc.hac_lrv(d)
    assert lags == 4 and lrv == pytest.approx(0.2)
    s = sc.dm_stats(d)
    assert s["se"] == pytest.approx(np.sqrt(0.2 / 100)) and s["t"] == pytest.approx(0.5 / np.sqrt(0.002))


def test_t_matches_engine_dm_test():
    rng = np.random.default_rng(0)
    l1, l2 = rng.normal(size=400), rng.normal(size=400)
    t, p = dm_test(l1, l2)
    s = sc.dm_stats(l1 - l2)
    assert s["t"] == pytest.approx(t) and s["p_two_sided"] == pytest.approx(p)


def test_identical_forecasts_give_a_clear_error_not_a_division_by_zero():
    with pytest.raises(ValueError, match="zero long-run variance"):
        sc.dm_stats(np.zeros(100))


def test_lag_rule_at_hold_out_length_is_seven():
    assert sc.hac_lrv(np.random.default_rng(1).normal(size=1508))[1] == 7


def test_iid_standard_error_is_close_to_sd_over_root_n():
    d = np.random.default_rng(2).normal(0.0, 1.0, 200_000)
    assert sc.dm_stats(d)["se"] == pytest.approx(d.std() / np.sqrt(len(d)), rel=0.03)


def test_interval_and_detectable_difference_multipliers():
    s = sc.dm_stats(np.random.default_rng(3).normal(-0.002, 0.03, 1500))
    assert s["ci_lo"] == pytest.approx(s["mean_diff"] - 1.96 * s["se"]) and s["ci_hi"] == pytest.approx(s["mean_diff"] + 1.96 * s["se"])
    assert s["mde_two_sided"] == pytest.approx(2.8016 * s["se"]) and s["mde_one_sided"] == pytest.approx(2.4865 * s["se"])
    assert s["lower_bound_one_sided"] == pytest.approx(s["mean_diff"] - 1.6449 * s["se"])


def test_one_sided_sign_negative_difference_is_improvement():
    rng = np.random.default_rng(4)
    noise = rng.normal(0, 0.01, 1500)
    better, worse = sc.dm_stats(-0.003 + noise), sc.dm_stats(0.003 + noise)
    assert better["t"] < 0 < worse["t"]
    assert better["p_one_sided"] < 0.01 and worse["p_one_sided"] > 0.99          # P(T <= t): small when the richer model is better
    assert stats.norm.cdf(-1.6449) == pytest.approx(0.05, abs=1e-4)


# ------------------------------------------------------------------ the four outcomes
def test_classify_each_outcome():
    assert sc.classify(-2.0, -0.01, 0.002) == "O1"
    assert sc.classify(2.5, 0.01, 0.002) == "O4"
    assert sc.classify(-1.0, -0.0005, 0.002) == "O3"        # lower bound above -SESOI: improvements larger than SESOI excluded
    assert sc.classify(-1.0, -0.0030, 0.002) == "O2"
    assert sc.classify(0.5, -0.0030, 0.002) == "O2"


def test_classify_boundaries_are_strict_and_ordered():
    assert sc.classify(-1.6449, -0.01, 0.002) != "O1"        # reject only if t < -1.6449
    assert sc.classify(1.96, 0.0, 0.002) != "O4"             # significantly worse only if t > +1.96
    assert sc.classify(-3.0, 0.5, 0.002) == "O1"             # O1 is tested before O3
    assert sc.classify(2.1, 0.5, 0.002) == "O4"              # O4 before O3 even though lower bound > -SESOI


def test_outcomes_from_simulated_loss_differences():
    rng = np.random.default_rng(5)
    noise = rng.normal(0, 0.01, 1500)
    out = {}
    def centred(sd):                                         # sample mean exactly 0, sample sd exactly sd: no dependence on the draw
        x = rng.normal(size=1500)
        return (x - x.mean()) / x.std() * sd

    noise, small, wide = centred(0.01), centred(0.006), centred(0.05)
    for name, d in (("O1", -0.004 + noise), ("O4", 0.004 + noise), ("O3", small), ("O2", -0.0005 + wide)):
        s = sc.dm_stats(d)
        out[name] = sc.classify(s["t"], s["lower_bound_one_sided"], 0.002)
        if name == "O3":                                     # precise estimate near zero: improvement larger than SESOI excluded
            assert -1.6449 <= s["t"] <= 1.96 and s["lower_bound_one_sided"] > -0.002
        if name == "O2":                                     # imprecise: neither established nor excluded
            assert -1.6449 <= s["t"] <= 1.96 and s["lower_bound_one_sided"] < -0.002
    assert out == {"O1": "O1", "O4": "O4", "O3": "O3", "O2": "O2"}


def test_frozen_sentences_carry_the_numbers_and_never_say_no_effect():
    s = sc.dm_stats(np.random.default_rng(6).normal(-0.0015, 0.04, 1508))
    for o in ("O1", "O2", "O3", "O4"):
        text = sc.frozen_sentence(o, s, 0.002)
        assert "no effect" not in text.lower()
    assert f"{s['mean_diff']:+.4f}" in sc.frozen_sentence("O1", s, 0.002)
    assert "SESOI = 0.002" in sc.frozen_sentence("O3", s, 0.002)
    assert f"{s['mde_one_sided']:.4f}" in sc.frozen_sentence("O2", s, 0.002)
    assert "35.2%" in sc.frozen_sentence("O1", s, 0.002)


# ------------------------------------------------------------------ calibration tests
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_coverage_tests_agree_with_engine(seed):
    h = (np.random.default_rng(seed).random(900) < 0.06).astype(float)
    assert 1 - stats.chi2.cdf(sc.kupiec_lr(h, 0.05), 1) == pytest.approx(kupiec(h, 0.05))
    assert 1 - stats.chi2.cdf(sc.christoffersen_lr(h), 1) == pytest.approx(christoffersen_ind(h))


def test_kupiec_edge_cases_match_engine():
    for h in (np.zeros(500), np.ones(50)):
        assert 1 - stats.chi2.cdf(sc.kupiec_lr(h, 0.05), 1) == pytest.approx(kupiec(h, 0.05))


def _gauss_forecast(T, seed, scale=1.0, alpha=0.05):
    rng = np.random.default_rng(seed)
    y = rng.normal(0, 0.01, T)                         # the truth: sd 0.01
    sd = np.full(T, 0.01 * scale)                      # the model's sd; scale < 1 understates risk
    z = stats.norm.ppf(alpha)
    return y, sd * z, -sd * stats.norm.pdf(z) / alpha, sd


def test_z2_sign_convention_positive_when_risk_is_underestimated():
    from src.engine import acerbi_szekely_z2
    T = 2000
    for scale, sign in ((1.0, 0), (0.7, 1), (1.3, -1)):
        y, v, e, sd = _gauss_forecast(T, 7, scale)
        z2 = acerbi_szekely_z2(y, v, e, 0.05)
        if sign == 0:
            assert abs(z2) < 0.4
        else:
            assert np.sign(z2) == sign
    y, v, e, sd = _gauss_forecast(T, 7, 0.7)                 # understated forecasts: the simulation p-value flags underestimation
    sim = sc.z2_simulate(np.ones((T, 1)), sd[:, None], np.zeros(T), v, e, 0.05, acerbi_szekely_z2(y, v, e, 0.05), draws=1000)
    assert sim["p_underestimated"] < 0.01
    y, v, e, sd = _gauss_forecast(T, 7, 1.3)
    sim = sc.z2_simulate(np.ones((T, 1)), sd[:, None], np.zeros(T), v, e, 0.05, acerbi_szekely_z2(y, v, e, 0.05), draws=1000)
    assert sim["p_underestimated"] > 0.9


def test_z2_simulation_is_centred_under_the_model_and_seeded():
    T = 1500
    y, v, e, sd = _gauss_forecast(T, 8)
    args = (np.ones((T, 1)), sd[:, None], np.zeros(T), v, e, 0.05, 0.0)
    a, b = sc.z2_simulate(*args, draws=1000), sc.z2_simulate(*args, draws=1000)
    assert abs(a["z2_sim_mean"]) < 0.02 and a == b


def test_z2_simulation_handles_two_component_mixtures():
    T = 800
    w = np.tile([0.7, 0.3], (T, 1))
    sd = np.tile([0.008, 0.02], (T, 1))
    sim = sc.z2_simulate(w, sd, np.zeros(T), np.full(T, -0.016), np.full(T, -0.025), 0.05, 0.0, draws=300)
    assert np.isfinite(sim["z2_sim_mean"]) and 0 < sim["p_two_sided"] <= 1


# ------------------------------------------------------------------ conditional test input
def test_lagged_correlation_uses_only_earlier_returns():
    rng = np.random.default_rng(9)
    prior, rets = rng.normal(size=(64, 3)), rng.normal(size=(120, 3))
    c = sc.lagged_corr(prior, rets)
    both = np.vstack([prior, rets])
    assert c[0] == pytest.approx(np.corrcoef(both[1:64, 0], both[1:64, 1])[0, 1])        # the 63 returns before day 0
    rets2 = rets.copy()
    rets2[50:, :2] += 5.0                                                                  # change returns from day 50 on
    c2 = sc.lagged_corr(prior, rets2)
    assert np.array_equal(c[:51], c2[:51])                                                  # day 50's value is untouched, day 51's is not
    assert c[51] != c2[51]


# ------------------------------------------------------------------ run validation and end to end
def synthetic_res(n=300, mode="pseudo", seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2018-01-01", periods=n)
    sd0 = np.full(n, 0.01)
    y = rng.normal(0, sd0)
    arms = {"S": ["A|pooled|N", "B|pooled|N", "D|pooled|N", "B|pooled|t", "D|pooled|t"],
            "L2": ["CCC_S_N", "RSC_S_N", "RSC_P_N", "CCC_S_t", "RSC_S_t", "RSC_P_t"], "B": ["DCC_N", "GARCHt"]}
    q = {0.05: (-1.645, -2.063), 0.025: (-1.96, -2.338)}
    res = {"mode": mode, "y": y, "dates": dates, "returns": rng.normal(0, 0.01, (n, 3)), "prior_returns": rng.normal(0, 0.01, (64, 3)),
           "raw_sha256": sc.EXPECTED_RAW_SHA256, "git_head": "abc", "freeze_tag": None, "runtime_s": 1.0, "python": "3.9.6 test"}
    for blk, names in arms.items():
        res[blk] = {"V": {a: {} for a in q}, "E": {a: {} for a in q}}
        for a, (zv, ze) in q.items():
            for nm in names:
                s = sd0 * rng.uniform(0.95, 1.05, n)
                res[blk]["V"][a][nm], res[blk]["E"][a][nm] = zv * s, ze * s
    res["L2"]["diag"] = {"psd_repairs": {0: [False, False], 21: [False, True]}, "margin_fallbacks": [],
                         "mix_w": np.tile([0.7, 0.3], (n, 1)), "mix_sd_rscp": np.c_[sd0 * 0.9, sd0 * 1.2],
                         "mix_sd_ccc": sd0, "mix_mu": np.zeros(n)}
    res["B"]["diag"] = {"dcc_refits": 3, "dcc_fallbacks": 1}
    return res


@pytest.fixture
def small_run(monkeypatch):
    monkeypatch.setitem(c0.EXPECTED_DAYS, "pseudo", 300)
    monkeypatch.setitem(c0.EXPECTED_DAYS, "holdout", 300)
    return synthetic_res()


def test_validate_run_accepts_a_good_dry_run(small_run):
    sc.validate_run(small_run, "pseudo")


def test_validate_run_refuses_bad_runs(small_run):
    r = dict(small_run, raw_sha256="0" * 64)
    with pytest.raises(AssertionError, match="raw file hash"):
        sc.validate_run(r, "pseudo")
    with pytest.raises(AssertionError, match="mode"):
        sc.validate_run(small_run, "holdout")
    r = synthetic_res(299)
    with pytest.raises(AssertionError, match="forecast days"):
        sc.validate_run(r, "pseudo")
    r = synthetic_res()
    r["L2"]["V"][0.05]["RSC_P_N"][5] = np.nan
    with pytest.raises(AssertionError, match="non-finite"):
        sc.validate_run(r, "pseudo")


def test_validate_run_holdout_needs_the_tag_and_a_descendant_commit_with_unchanged_forecast_code(small_run, monkeypatch):
    r = dict(small_run, mode="holdout")
    monkeypatch.setattr(sc, "freeze_tag_commit", lambda: None)
    with pytest.raises(AssertionError, match="does not exist"):
        sc.validate_run(r, "holdout")
    tag = sc._git("rev-list", "--max-parents=0", "HEAD")   # the root commit: an ancestor of every later commit
    head = sc._git("rev-parse", "HEAD")
    monkeypatch.setattr(sc, "freeze_tag_commit", lambda: tag)
    with pytest.raises(AssertionError, match="different freeze-tag"):
        sc.validate_run(dict(r, git_head=head, freeze_tag="other"), "holdout")
    with pytest.raises(AssertionError, match="does not descend"):
        sc.validate_run(dict(r, git_head="0" * 40, freeze_tag=tag), "holdout")
    monkeypatch.setattr(sc, "_git", lambda *a: "src/engine.py" if a[0] == "diff" else "")
    with pytest.raises(AssertionError, match="determine the forecasts"):
        sc.validate_run(dict(r, git_head=head, freeze_tag=tag), "holdout")


def test_score_end_to_end_writes_everything_and_is_reproducible(small_run, tmp_path):
    p1 = sc.score(small_run, "pseudo", tmp_path / "a")
    p2 = sc.score(small_run, "pseudo", tmp_path / "b")
    assert p1["outcome"] in {"O1", "O2", "O3", "O4"} and p1["n"] == 300
    for name in ("primary.json", "RESULT.md", "manifest.json", "calibration.csv", "secondary_ladder.csv", "secondary_focus_year.csv",
                 "secondary_gw_conditional.csv", "secondary_alpha_and_t_chain.csv", "secondary_spa.csv", "diagnostics.json",
                 "cumulative_d.png"):
        assert (tmp_path / "a" / name).exists(), name
    assert json.loads((tmp_path / "a" / "diagnostics.json").read_text())["psd_repairs"] == 1
    cal = pd.read_csv(tmp_path / "a" / "calibration.csv")
    assert set(cal.arm) == set(c0.PRIMARY_ARMS) and len(cal) == 4
    assert len(pd.read_csv(tmp_path / "a" / "secondary_ladder.csv")) == 6
    assert "DRY RUN" in (tmp_path / "a" / "RESULT.md").read_text()
    man = json.loads((tmp_path / "a" / "manifest.json").read_text())
    assert man["primary.json"] == c0.sha256_file(tmp_path / "a" / "primary.json")
    for name in ("primary.json", "calibration.csv", "secondary_spa.csv"):               # seeded: identical across runs
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    assert p1 == p2


def test_score_only_touches_declared_arms(small_run, tmp_path):
    for blk in ("S", "L2", "B"):
        for a in sc.ALPHAS:
            small_run[blk]["V"][a]["HS" if blk == "B" else "CCC_M"] = np.full(300, np.nan)     # undeclared arms may be garbage
            small_run[blk]["E"][a]["HS" if blk == "B" else "CCC_M"] = np.full(300, np.nan)
    sc.score(small_run, "pseudo", tmp_path)
