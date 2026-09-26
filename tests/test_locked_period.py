"""WP1 required test: fails if post-2015 (locked test period) data ever
reaches the pipeline. Exercises src.data.assert_no_locked_period_leakage,
the guard wired into every real-data-facing function per the pilot's
research-integrity rule."""
from __future__ import annotations

import pandas as pd
import pytest

from src.data import assert_no_locked_period_leakage


def test_locked_period_assertion_rejects_post_2015_data():
    df = pd.DataFrame(
        {"SPY": [1.0, 2.0]},
        index=pd.to_datetime(["2015-12-31", "2016-01-04"]),
    )
    with pytest.raises(AssertionError):
        assert_no_locked_period_leakage(df, cutoff="2015-12-31")


def test_locked_period_assertion_passes_for_valid_range():
    df = pd.DataFrame(
        {"SPY": [1.0, 2.0]},
        index=pd.to_datetime(["2015-12-29", "2015-12-31"]),
    )
    assert_no_locked_period_leakage(df, cutoff="2015-12-31")  # must not raise


def test_locked_period_assertion_handles_empty_df():
    df = pd.DataFrame({"SPY": []}, index=pd.DatetimeIndex([]))
    assert_no_locked_period_leakage(df, cutoff="2015-12-31")  # must not raise
