"""
Tests for financial-return calculations.

Includes:
- hard-coded small-price known-answer checks (not pandas-vs-pandas);
- manual checks against real pilot ETF data, using independently
  hand-computed values (see notes/pilot_eda.md Section "Return
  construction" for how these were derived from data/processed files);
- equal-weight portfolio construction checks;
- a rolling-window trailing-window check.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.returns import (
    calculate_equal_weight_portfolio_returns,
    calculate_log_returns,
    calculate_simple_returns,
    rolling_volatility,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


# ---------------------------------------------------------------------
# Hard-coded known-answer tests (no dependency on downloaded data)
# ---------------------------------------------------------------------

def test_simple_return_known_value():
    """100 -> 105 should give a simple return of exactly 0.05."""
    prices = pd.Series([100.0, 105.0])
    returns = calculate_simple_returns(prices)
    assert np.isnan(returns.iloc[0])
    assert np.isclose(returns.iloc[1], 0.05)


def test_simple_return_known_series():
    """A short hard-coded price path with hand-computed expected returns."""
    prices = pd.Series([100.0, 110.0, 99.0, 99.0])
    expected = [np.nan, 0.10, -0.10, 0.0]
    returns = calculate_simple_returns(prices)
    assert np.isnan(returns.iloc[0])
    np.testing.assert_allclose(returns.iloc[1:], expected[1:], atol=1e-12)


def test_log_return_known_value():
    """100 -> 105 should give a log return of log(1.05)."""
    prices = pd.Series([100.0, 105.0])
    returns = calculate_log_returns(prices)
    assert np.isclose(returns.iloc[1], np.log(1.05))


def test_equal_weight_portfolio_known_values():
    """Three assets with hand-picked returns and known equal-weight average."""
    asset_returns = pd.DataFrame(
        {
            "SPY": [0.01, -0.02],
            "IEF": [0.00, 0.01],
            "GLD": [0.02, 0.00],
        }
    )
    expected = pd.Series([(0.01 + 0.00 + 0.02) / 3, (-0.02 + 0.01 + 0.00) / 3])
    portfolio = calculate_equal_weight_portfolio_returns(
        asset_returns, assets=["SPY", "IEF", "GLD"]
    )
    np.testing.assert_allclose(portfolio, expected, atol=1e-12)


def test_portfolio_not_built_from_averaged_log_returns():
    """
    The equal-weight portfolio's SIMPLE return must be the weighted
    average of asset SIMPLE returns, not the (exponentiated) average of
    asset LOG returns — the two are not numerically identical.
    """
    asset_returns = pd.DataFrame({"SPY": [0.05], "IEF": [-0.03], "GLD": [0.10]})
    portfolio = calculate_equal_weight_portfolio_returns(
        asset_returns, assets=["SPY", "IEF", "GLD"]
    )

    log_avg = np.log1p(asset_returns).mean(axis=1)
    wrong_portfolio = np.expm1(log_avg)

    assert not np.isclose(portfolio.iloc[0], wrong_portfolio.iloc[0])
    assert np.isclose(portfolio.iloc[0], (0.05 - 0.03 + 0.10) / 3)


# ---------------------------------------------------------------------
# Manual validation against the actual downloaded pilot dataset
# (Section 15/16 of the pilot task spec).
#
# Expected values below were independently hand-computed from
# data/processed/pilot_adjusted_prices.csv as:
#     P_t / P_(t-1) - 1
# for the given ticker and date, using the immediately preceding
# available trading date in the pilot dataset.
# ---------------------------------------------------------------------

PILOT_DATA_AVAILABLE = (PROCESSED_DIR / "pilot_adjusted_prices.csv").exists()

MANUAL_SIMPLE_RETURN_CHECKS = [
    # (date, ticker, expected_simple_return)
    ("2010-01-05", "SPY", 0.00264770),
    ("2010-01-05", "IEF", 0.00439081),
    ("2010-01-05", "GLD", -0.00091080),
    ("2020-03-10", "SPY", 0.05174490),
    ("2020-03-10", "IEF", -0.01835694),
    ("2020-03-10", "GLD", -0.02110134),
    ("2023-11-01", "SPY", 0.01066477),
    ("2023-11-01", "IEF", 0.01151770),
    ("2023-11-01", "GLD", -0.00315064),
]

MANUAL_PORTFOLIO_RETURN_CHECKS = [
    ("2010-01-05", 0.002042568996640667),
    ("2020-03-10", 0.004095541324609466),
    ("2023-11-01", 0.006343943901702533),
]


@pytest.mark.skipif(not PILOT_DATA_AVAILABLE, reason="pilot data not downloaded")
def test_simple_returns_match_manual_calculation_on_pilot_data():
    prices = pd.read_csv(
        PROCESSED_DIR / "pilot_adjusted_prices.csv", index_col="Date", parse_dates=True
    )
    simple_returns = calculate_simple_returns(prices)
    for date_str, ticker, expected in MANUAL_SIMPLE_RETURN_CHECKS:
        actual = simple_returns.loc[pd.Timestamp(date_str), ticker]
        assert np.isclose(actual, expected, atol=1e-6), (
            f"{ticker} on {date_str}: expected {expected}, got {actual}"
        )


@pytest.mark.skipif(not PILOT_DATA_AVAILABLE, reason="pilot data not downloaded")
def test_log_return_matches_manual_calculation_on_pilot_data():
    prices = pd.read_csv(
        PROCESSED_DIR / "pilot_adjusted_prices.csv", index_col="Date", parse_dates=True
    )
    log_returns = calculate_log_returns(prices)
    date_str, ticker, expected_simple = MANUAL_SIMPLE_RETURN_CHECKS[0]
    expected_log = np.log(1 + expected_simple)
    actual = log_returns.loc[pd.Timestamp(date_str), ticker]
    assert np.isclose(actual, expected_log, atol=1e-6)


@pytest.mark.skipif(not PILOT_DATA_AVAILABLE, reason="pilot data not downloaded")
def test_equal_weight_portfolio_matches_manual_calculation_on_pilot_data():
    simple_returns = pd.read_csv(
        PROCESSED_DIR / "pilot_simple_returns.csv", index_col="Date", parse_dates=True
    )
    portfolio_returns = calculate_equal_weight_portfolio_returns(
        simple_returns, assets=["SPY", "IEF", "GLD"]
    )
    for date_str, expected in MANUAL_PORTFOLIO_RETURN_CHECKS:
        actual = portfolio_returns.loc[pd.Timestamp(date_str)]
        assert np.isclose(actual, expected, atol=1e-9), (
            f"portfolio return on {date_str}: expected {expected}, got {actual}"
        )


# ---------------------------------------------------------------------
# Rolling-volatility trailing-window behaviour
# ---------------------------------------------------------------------

def test_rolling_volatility_is_trailing_not_centred():
    """
    A rolling window must only use observations at or before date t.
    We construct a series where the second half has much larger moves
    than the first half, and check that the rolling std at a date near
    the boundary reflects only PAST values, not future ones.
    """
    quiet = pd.Series([0.0, 0.001, -0.001, 0.0005, -0.0005] * 6)  # 30 quiet obs
    volatile = pd.Series([0.10, -0.10, 0.12, -0.11, 0.09] * 6)  # 30 volatile obs
    series = pd.concat([quiet, volatile], ignore_index=True)

    window = 10
    roll = rolling_volatility(series, window=window)

    # The value exactly at the last quiet-period index (index 29) should
    # be computed purely from quiet-period data and therefore be small,
    # even though large volatile-period values immediately follow.
    boundary_idx = len(quiet) - 1
    assert roll.iloc[boundary_idx] < 0.01

    # A centred window would have pulled in the volatile future values
    # and inflated this figure; confirm it does not match a centred
    # computation.
    centred_at_boundary = series.rolling(window=window, center=True).std().iloc[boundary_idx]
    assert roll.iloc[boundary_idx] != pytest.approx(centred_at_boundary)


def test_rolling_volatility_min_periods_produces_leading_nans():
    series = pd.Series(np.arange(1, 30, dtype=float))
    window = 21
    roll = rolling_volatility(series, window=window)
    assert roll.iloc[: window - 1].isna().all()
    assert not np.isnan(roll.iloc[window - 1])
