from __future__ import annotations

import pandas as pd
import pytest

from etf_optimizer.backtesting.benchmarks import (
    benchmark_equal_weight_walk_forward,
    benchmark_max_sharpe_walk_forward,
    benchmark_min_variance_walk_forward,
)
from etf_optimizer.backtesting.engine import BacktestConfig


def test_walk_forward_max_sharpe_estimates_weights_from_training_window_only():
    returns = pd.DataFrame(
        {
            "TRAIN_WINNER": [0.02, 0.021, 0.019, -0.50, -0.50, -0.50],
            "FUTURE_WINNER": [-0.01, -0.011, -0.009, 0.50, 0.50, 0.50],
        },
        index=pd.date_range("2020-01-31", periods=6, freq="ME"),
    )
    config = BacktestConfig(train_size=3, test_size=3, step_size=3, cost_bps=0.0)

    result = benchmark_max_sharpe_walk_forward(returns, config, periods_per_year=12)

    rebalance_date = returns.index[3]
    assert result.weights.loc[rebalance_date, "TRAIN_WINNER"] > result.weights.loc[rebalance_date, "FUTURE_WINNER"]
    assert (result.portfolio_returns < 0.0).all()


def test_walk_forward_min_variance_estimates_weights_from_training_window_only():
    returns = pd.DataFrame(
        {
            "TRAIN_LOW_VAR": [0.01, 0.011, 0.009, -0.50, 0.50, -0.50],
            "FUTURE_LOW_VAR": [0.20, -0.20, 0.20, 0.01, 0.011, 0.009],
        },
        index=pd.date_range("2020-01-31", periods=6, freq="ME"),
    )
    config = BacktestConfig(train_size=3, test_size=3, step_size=3, cost_bps=0.0)

    result = benchmark_min_variance_walk_forward(returns, config, periods_per_year=12)

    rebalance_date = returns.index[3]
    assert result.weights.loc[rebalance_date, "TRAIN_LOW_VAR"] > result.weights.loc[rebalance_date, "FUTURE_LOW_VAR"]


def test_walk_forward_equal_weight_aligns_returns_to_out_of_sample_windows():
    returns = pd.DataFrame(
        {
            "A": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08],
            "B": [0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01],
            "C": [0.02] * 8,
        },
        index=pd.date_range("2020-01-31", periods=8, freq="ME"),
    )
    config = BacktestConfig(train_size=3, test_size=2, step_size=2, cost_bps=0.0)

    result = benchmark_equal_weight_walk_forward(returns, config)

    expected_index = returns.index[[3, 4, 5, 6]]
    assert result.portfolio_returns.index.tolist() == expected_index.tolist()
    assert result.weights.shape[0] == 2
    assert result.weights.to_numpy().ravel() == pytest.approx([1.0 / 3.0] * 6)
