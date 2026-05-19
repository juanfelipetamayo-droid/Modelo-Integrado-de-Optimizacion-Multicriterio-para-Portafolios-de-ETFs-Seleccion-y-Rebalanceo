from __future__ import annotations

import pandas as pd
import pytest

from etf_optimizer.backtesting.benchmarks import (
    benchmark_spy,
    benchmark_60_40,
    benchmark_equal_weight,
    benchmark_min_variance,
    benchmark_max_sharpe,
    run_benchmark_comparison,
)


@pytest.fixture
def sample_returns():
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    return pd.DataFrame({
        "SPY": [0.01] * 24,
        "BND": [0.003] * 24,
        "QQQ": [0.015] * 24,
        "IWM": [0.005] * 24,
    }, index=idx)


def test_benchmark_spy(sample_returns):
    result = benchmark_spy(sample_returns)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_returns)
    assert result.name == "SPY"


def test_benchmark_spy_missing_ticker():
    rets = pd.DataFrame({"QQQ": [0.01] * 10})
    with pytest.raises(ValueError):
        benchmark_spy(rets, spy_ticker="SPY")


def test_benchmark_60_40(sample_returns):
    result = benchmark_60_40(sample_returns)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_returns)
    assert result.iloc[0] == pytest.approx(0.6 * 0.01 + 0.4 * 0.003)


def test_benchmark_60_40_normalizes_drifted_weights():
    rets = pd.DataFrame({"SPY": [0.10, 0.10], "BND": [0.00, 0.00]})
    result = benchmark_60_40(rets, rebalance_periods=12)
    first = 0.6 * 0.10
    drifted_equity_weight = 0.6 * 1.10 / (1.0 + first)
    assert result.iloc[0] == pytest.approx(first)
    assert result.iloc[1] == pytest.approx(drifted_equity_weight * 0.10)


def test_benchmark_60_40_missing_ticker():
    rets = pd.DataFrame({"SPY": [0.01] * 10})
    with pytest.raises(ValueError):
        benchmark_60_40(rets, bond_ticker="BND")


def test_benchmark_equal_weight(sample_returns):
    result = benchmark_equal_weight(sample_returns)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_returns)


def test_benchmark_min_variance(sample_returns):
    result = benchmark_min_variance(sample_returns, periods_per_year=12)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_returns)


def test_benchmark_max_sharpe(sample_returns):
    result = benchmark_max_sharpe(sample_returns, periods_per_year=12)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_returns)


def test_run_benchmark_comparison(sample_returns):
    funcs = {
        "SPY": lambda r: benchmark_spy(r),
        "EW": lambda r: benchmark_equal_weight(r),
    }
    result = run_benchmark_comparison(sample_returns, funcs)
    assert isinstance(result, pd.DataFrame)
    assert "SPY" in result.columns
    assert "EW" in result.columns
