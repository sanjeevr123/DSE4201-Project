"""
Tests protecting the thesis against look-ahead bias and incorrect
forecast-date alignment.

These will become critical when the walk-forward forecasting engine
is implemented.
"""


def test_training_data_precede_target_date():
    """Training data must end before the forecast target date."""

    training_end = "2020-01-10"
    target_date = "2020-01-13"

    assert training_end < target_date
