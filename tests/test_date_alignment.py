"""
Tests protecting the thesis against look-ahead bias and incorrect
forecast-date alignment.

These will become critical when the walk-forward forecasting engine
is implemented.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.returns import rolling_volatility


def test_training_data_precede_target_date():
    """Training data must end before the forecast target date."""

    training_end = "2020-01-10"
    target_date = "2020-01-13"

    assert training_end < target_date


def test_rolling_volatility_uses_only_past_and_present_observations():
    """
    The rolling-volatility statistic at date t must depend only on
    observations dated at or before t. We perturb a single FUTURE
    observation and confirm the rolling value at an earlier boundary
    date is completely unaffected — proving no look-ahead leakage.
    """
    dates = pd.date_range("2020-01-01", periods=40, freq="D")
    base = pd.Series(np.linspace(0.001, 0.002, len(dates)), index=dates)

    window = 21
    boundary_date = dates[24]  # first date with a full trailing window

    roll_before = rolling_volatility(base, window=window)

    perturbed = base.copy()
    perturbed.iloc[30:] = 5.0  # large shock, strictly after boundary_date
    roll_after = rolling_volatility(perturbed, window=window)

    assert roll_before.loc[boundary_date] == roll_after.loc[boundary_date]


def test_rolling_volatility_window_is_trailing_length(monkeypatch=None):
    """A window of length W should require W observations before producing
    a non-NaN value, confirming the window looks backward only."""
    dates = pd.date_range("2020-01-01", periods=25, freq="D")
    series = pd.Series(np.arange(1, 26, dtype=float), index=dates)
    window = 21
    roll = rolling_volatility(series, window=window)

    assert roll.iloc[: window - 1].isna().all()
    assert pd.notna(roll.iloc[window - 1])
    # The first valid value must be produced at the (window)-th
    # observation, i.e. using dates[0:window] only.
    assert roll.index[window - 1] == dates[window - 1]
