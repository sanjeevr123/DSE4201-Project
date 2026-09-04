"""
Return and portfolio-return calculation utilities.

Functions will be added only after the relevant financial concepts
have been understood and manually validated.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


def calculate_simple_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """
    Calculate daily simple returns.

        R_t = P_t / P_(t-1) - 1

    Input:
        prices: a Series or DataFrame of prices indexed by date, sorted
            ascending in time. Each column (if a DataFrame) is treated
            as an independent price series.

    Output:
        Simple returns of the same type/shape, with the first row NaN
        (no prior observation to compare against). No rows are dropped
        here — callers decide how to handle the leading NaN.

    Assumption:
        Input prices are already validated (positive, correctly
        ordered by date) by the caller.
    """
    return prices / prices.shift(1) - 1


def calculate_log_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """
    Calculate daily log returns.

        r_t = log(P_t) - log(P_(t-1))

    Input/Output: same shape and conventions as calculate_simple_returns.
    """
    return np.log(prices) - np.log(prices.shift(1))


def calculate_equal_weight_portfolio_returns(
    asset_returns: pd.DataFrame,
    assets: Sequence[str] | None = None,
) -> pd.Series:
    """
    Calculate a fixed equal-weight portfolio's simple return:

        portfolio_return_t = w' r_t,  w = [1/n, ..., 1/n]

    This is a TEMPORARY / PILOT portfolio construction: fixed equal
    weights, no rebalancing logic, no optimisation. It is built directly
    from each asset's own simple return series (not by averaging log
    returns), so the result is the exact equal-weight simple portfolio
    return.

    Input:
        asset_returns: DataFrame of per-asset SIMPLE returns, one column
            per asset, indexed by date.
        assets: optional explicit column subset/order to use as the
            portfolio constituents; defaults to all columns of
            asset_returns.

    Output:
        Series of equal-weight portfolio simple returns.
    """
    if assets is None:
        assets = list(asset_returns.columns)
    weight = 1.0 / len(assets)
    return (asset_returns[assets] * weight).sum(axis=1, skipna=False)


def rolling_volatility(returns: pd.Series, window: int = 21) -> pd.Series:
    """
    Trailing rolling standard deviation of a return series.

    The value at date t uses only observations dated at or before t
    (a trailing window: the current observation and the (window - 1)
    preceding ones). Rolling windows are never centred, to preserve
    correct time ordering and avoid look-ahead bias.

    This is a backward-looking DESCRIPTIVE statistic computed from
    already-observed returns. It is not, by itself, a forecast of
    future (e.g. tomorrow's) volatility.

    Input:
        returns: Series of returns indexed by date, sorted ascending.
        window: trailing window length in trading days (default 21).

    Output:
        Series of rolling standard deviations, NaN for the first
        (window - 1) observations where a full window is not yet
        available.
    """
    return returns.rolling(window=window, center=False, min_periods=window).std()
