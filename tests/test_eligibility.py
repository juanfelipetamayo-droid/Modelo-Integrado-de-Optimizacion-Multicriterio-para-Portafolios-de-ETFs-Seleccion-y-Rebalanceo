from __future__ import annotations

import pandas as pd
from pandas.testing import assert_series_equal

from etf_optimizer.data.eligibility import (
    compute_avg_dollar_volume,
    filter_by_history,
    filter_by_liquidity,
)


def test_filter_by_history_uses_coverage_pct_and_first_valid_cutoff():
    coverage = pd.DataFrame(
        {
            "ticker": ["SPY", "LATE", "THIN", "EMPTY"],
            "coverage_pct": [0.95, 0.95, 0.70, 1.0],
            "first_valid": ["2020-01-02", "2021-06-01", "2020-01-02", None],
        }
    )

    eligible = filter_by_history(coverage, min_coverage_pct=0.80, min_first_valid="2021-01-01")

    expected = pd.Series(
        [True, False, False, False],
        index=pd.Index(["SPY", "LATE", "THIN", "EMPTY"], name="ticker"),
        name="history_eligible",
    )
    assert_series_equal(eligible, expected)


def test_filter_by_history_accepts_coverage_index_without_first_valid_cutoff():
    coverage = pd.DataFrame(
        {"coverage_pct": [0.80, 0.799]},
        index=pd.Index(["SPY", "QQQ"], name="ticker"),
    )

    eligible = filter_by_history(coverage, min_coverage_pct=0.80)

    expected = pd.Series(
        [True, False],
        index=pd.Index(["SPY", "QQQ"], name="ticker"),
        name="history_eligible",
    )
    assert_series_equal(eligible, expected)


def test_compute_avg_dollar_volume_aligns_prices_and_volume_without_filling_missing_values():
    idx = pd.date_range("2021-01-01", periods=3, freq="D")
    prices = pd.DataFrame(
        {
            "SPY": [100.0, 110.0, None],
            "QQQ": [200.0, None, 220.0],
            "NO_VOLUME": [10.0, 11.0, 12.0],
        },
        index=idx,
    )
    volume = pd.DataFrame(
        {
            "SPY": [10.0, 20.0, 30.0],
            "QQQ": [5.0, 0.0, None],
            "EXTRA": [1.0, 1.0, 1.0],
        },
        index=idx,
    )

    avg_dollar_volume = compute_avg_dollar_volume(prices, volume)

    expected = pd.Series(
        {"SPY": 1600.0, "QQQ": 1000.0},
        name="avg_dollar_volume",
    )
    assert_series_equal(avg_dollar_volume, expected)


def test_filter_by_liquidity_uses_minimum_average_dollar_volume_threshold():
    avg_dollar_volume = pd.Series(
        {"SPY": 1_000_000.0, "QQQ": 999_999.99, "EMPTY": float("nan")},
        name="avg_dollar_volume",
    )

    eligible = filter_by_liquidity(avg_dollar_volume, min_avg_dollar_volume=1_000_000.0)

    expected = pd.Series(
        {"SPY": True, "QQQ": False, "EMPTY": False},
        name="liquidity_eligible",
    )
    assert_series_equal(eligible, expected)
