"""Tests for the pre-freeze code changes (docs/decisions_log.md, "Pre-freeze code hygiene"): repair and fallback counters,
saved diagnostics, run validation, freeze tag lookup, marker configuration. Synthetic data only."""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import confirm_00_run as c0  # noqa: E402
from src import explore_routes as er  # noqa: E402
from src import explore_wf as ewf  # noqa: E402
from src.engine import mix_var_es  # noqa: E402
from src.returns import calculate_equal_weight_portfolio_returns  # noqa: E402


def _returns(T=480, seed=3):
    rng = np.random.default_rng(seed)
    C = np.array([[1, -0.3, 0.1], [-0.3, 1, 0.2], [0.1, 0.2, 1.0]])
    z = rng.standard_normal((T, 3)) @ np.linalg.cholesky(C).T
    vol = np.where(rng.random(T) < 0.15, 0.02, 0.008)[:, None]
    return z * vol * np.array([1.0, 0.4, 0.9])


def _run(R, start=300, **kw):
    prov = ewf.HMMProvider("t", R[:, 0], K=2)
    return er.run_rs_corr(R, np.ones(3) / 3, prov, (0.05,), start, window=300, refit=21, margin_refit=63, **kw)


# ---------------------------------------------------------------- PSD repair counter
def test_needs_repair_matches_nearest_corr():
    bad = np.array([[1, 0.9, -0.9], [0.9, 1, 0.9], [-0.9, 0.9, 1.0]])
    good = np.array([[1, -0.3, 0.1], [-0.3, 1, 0.2], [0.1, 0.2, 1.0]])
    assert er.needs_repair(bad) and not er.needs_repair(good)
    assert not np.allclose(er.nearest_corr(bad), bad) and np.allclose(er.nearest_corr(good), good)


def test_pair_variant_counts_repairs_and_keeps_output():
    pooled = np.array([[1, 0.9, 0.9], [0.9, 1, 0.9], [0.9, 0.9, 1.0]])
    regime = np.array([[1, -0.9, 0.0], [-0.9, 1, 0.0], [0.0, 0.0, 1.0]])   # entry (0,1) -> -0.9 breaks PSD
    rep = []
    with_flag = er.pair_variant(pooled, regime, (0, 1), repairs=rep)
    assert rep == [True]
    assert np.array_equal(with_flag, er.pair_variant(pooled, regime, (0, 1)))
    ok = []
    er.pair_variant(pooled, np.eye(3) * 0 + pooled, (0, 1), repairs=ok)
    assert ok == [False]


# ---------------------------------------------------------------- run_rs_corr diagnostics
def test_run_rs_corr_diag_is_complete_and_consistent_with_forecasts():
    R = _returns()
    out = _run(R)
    d = out["diag"]
    t0s = list(range(300, 480, 21))
    assert sorted(d["psd_repairs"]) == t0s and all(len(v) == 2 for v in d["psd_repairs"].values())
    assert sorted(d["margin_params"]) == t0s and d["margin_fallbacks"] == []
    assert all(len(p) == 4 for p in d["margin_params"].values())
    assert sorted(d["corr_pair"]) == t0s
    cp = d["corr_pair"][300]
    assert set(cp) == {"pooled", "regime", "rscp"} and len(cp["regime"]) == 2 and len(cp["rscp"]) == 2
    assert np.all(np.isnan(d["mix_w"][:300])) and np.allclose(d["mix_w"][300:].sum(axis=1), 1)
    w = np.ones(3) / 3
    for t in (300, 350, 479):                       # the stored mixtures reproduce the stored VaR/ES exactly
        mu = np.full(2, d["mix_mu"][t])
        v, e = mix_var_es(d["mix_w"][t], mu, d["mix_sd_rscp"][t], 0.05)
        assert np.isclose(v, out["V"][0.05]["RSC_P_N"][t], rtol=0, atol=1e-12)
        assert np.isclose(e, out["E"][0.05]["RSC_P_N"][t], rtol=0, atol=1e-12)
        v, e = mix_var_es(np.array([1.0]), mu[:1], np.array([d["mix_sd_ccc"][t]]), 0.05)
        assert np.isclose(v, out["V"][0.05]["CCC_S_N"][t], rtol=0, atol=1e-12)
    assert w.sum() == pytest.approx(1)


def test_run_rs_corr_counts_margin_fallbacks_and_keeps_previous_parameters(monkeypatch):
    R = _returns()
    real, calls = er.fit_margins, {"n": 0}

    def flaky(Rw):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("optimiser failed")
        return real(Rw)

    monkeypatch.setattr(er, "fit_margins", flaky)
    out = _run(R)
    d = out["diag"]
    assert d["margin_fallbacks"] == [300 + 63]
    for t0 in (363, 384, 405):                       # fallback refit and the two blocks after it share the old parameters
        assert all(np.array_equal(a, b) for a, b in zip(d["margin_params"][t0], d["margin_params"][342]))
    assert np.all(np.isfinite(out["V"][0.05]["RSC_P_N"][300:]))


def test_run_rs_corr_still_raises_when_first_margin_fit_fails(monkeypatch):
    monkeypatch.setattr(er, "fit_margins", lambda Rw: (_ for _ in ()).throw(RuntimeError("no fit")))
    with pytest.raises(RuntimeError):
        _run(_returns())


# ---------------------------------------------------------------- DCC fallback
def _fake_dcc_optimum(monkeypatch, x):
    """Replace only explore_wf's DCC optimiser result (arch uses scipy's own minimize and must not be touched)."""
    from scipy import optimize as real
    fake = SimpleNamespace(minimize=lambda *a, **k: SimpleNamespace(x=np.array(x)), minimize_scalar=real.minimize_scalar)
    monkeypatch.setattr(ewf, "optimize", fake)


def test_fit_dcc_reports_fallback(monkeypatch):
    R = _returns(300)
    w = np.ones(3) / 3
    _fake_dcc_optimum(monkeypatch, [-0.1, 0.5])
    d = ewf.fit_dcc(R, w)
    assert d["fallback"] is True and d["a"] == 0.0 and d["b"] == 0.0


def test_fit_dcc_no_fallback_on_valid_optimum(monkeypatch):
    R = _returns(300)
    _fake_dcc_optimum(monkeypatch, [0.03, 0.94])
    d = ewf.fit_dcc(R, np.ones(3) / 3)
    assert d["fallback"] is False and d["a"] == 0.03 and d["b"] == 0.94


def test_run_benchmarks_counts_dcc_refits_and_fallbacks(monkeypatch):
    R = _returns()
    _fake_dcc_optimum(monkeypatch, [-0.1, 0.5])
    out = ewf.run_benchmarks(R, np.ones(3) / 3, (0.05,), 300, window=300, refit=21, dcc=True)
    assert out["diag"] == {"dcc_refits": 3, "dcc_fallbacks": 3}


# ---------------------------------------------------------------- confirm_00_run
def _res(n=5, mode="holdout"):
    v, e = np.full(n, -0.02), np.full(n, -0.03)
    L2 = {"V": {a: {m: v.copy() for m in c0.PRIMARY_ARMS} for a in c0.ALPHAS},
          "E": {a: {m: e.copy() for m in c0.PRIMARY_ARMS} for a in c0.ALPHAS}}
    return {"y": np.zeros(n), "dates": np.arange(n), "returns": np.zeros((n, 3)), "L2": L2}


def _validate(res, n=5):
    saved = dict(c0.EXPECTED_DAYS)
    c0.EXPECTED_DAYS["holdout"] = n
    try:
        c0.validate_output(res, "holdout")
    finally:
        c0.EXPECTED_DAYS.update(saved)


def test_expected_day_counts():
    assert c0.EXPECTED_DAYS == {"pseudo": 1006, "holdout": 1508}


def test_validate_output_accepts_good_run():
    _validate(_res())


def test_validate_output_rejects_wrong_count():
    with pytest.raises(AssertionError, match="forecast days"):
        _validate(_res(4), n=5)


@pytest.mark.parametrize("arm", c0.PRIMARY_ARMS)
def test_validate_output_rejects_nan_positive_var_and_es_above_var(arm):
    r = _res()
    r["L2"]["V"][0.05][arm][2] = np.nan
    with pytest.raises(AssertionError, match="non-finite"):
        _validate(r)
    r = _res()
    r["L2"]["V"][0.025][arm][1] = 0.001
    with pytest.raises(AssertionError, match="VaR not negative"):
        _validate(r)
    r = _res()
    r["L2"]["E"][0.05][arm][0] = -0.01               # ES above VaR
    with pytest.raises(AssertionError, match="ES above VaR"):
        _validate(r)


def test_freeze_tag_commit_is_none_without_tag(monkeypatch):
    monkeypatch.setattr(c0, "_git", lambda *a: "")
    assert c0.freeze_tag_commit() is None
    monkeypatch.setattr(c0, "_git", lambda *a: "abc123")
    assert c0.freeze_tag_commit() == "abc123"


def test_freeze_tag_commit_never_returns_the_rev_expression():
    assert c0.freeze_tag_commit() in (None,) or len(c0.freeze_tag_commit()) == 40


def test_sha256_file(tmp_path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"abc")
    assert c0.sha256_file(p) == hashlib.sha256(b"abc").hexdigest()


# ---------------------------------------------------------------- documentation and configuration
def test_returns_docstring_says_rebalanced_daily():
    doc = calculate_equal_weight_portfolio_returns.__doc__
    assert "rebalanced to equal weights every day" in doc and "no rebalancing logic" not in doc


def test_holdout_marker_is_registered_and_excluded_by_default(pytestconfig):
    assert any(m.startswith("holdout_data") for m in pytestconfig.getini("markers"))
    addopts = pytestconfig.getini("addopts")
    assert "not holdout_data" in (" ".join(addopts) if isinstance(addopts, list) else addopts)
