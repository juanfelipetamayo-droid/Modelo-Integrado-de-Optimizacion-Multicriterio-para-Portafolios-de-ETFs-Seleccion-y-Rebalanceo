from __future__ import annotations

import numpy as np
import pandas as pd

import pytest

from etf_optimizer.backtesting.engine import WalkForwardBacktester, BacktestConfig, required_observations
from etf_optimizer.backtesting.metrics import performance_summary
from etf_optimizer.features import returns_from_prices


def test_performance_summary_contains_core_academic_metrics():
    returns = pd.Series([0.01, -0.02, 0.03, 0.01, -0.01], index=pd.date_range("2024-01-01", periods=5))
    summary = performance_summary(returns, periods_per_year=252)
    for col in ["cagr", "volatility", "sharpe", "sortino", "max_drawdown", "calmar"]:
        assert col in summary
    assert np.isfinite(summary["sharpe"])


def test_walk_forward_backtester_runs_without_lookahead():
    idx = pd.date_range("2020-01-31", periods=12, freq="ME")
    returns = pd.DataFrame(
        {"A": [0.01] * 12, "B": [0.005, -0.01, 0.02, 0.01, 0.0, 0.005, 0.02, 0.01, -0.01, 0.01, 0.02, 0.01]},
        index=idx,
    )

    def strategy(train_returns: pd.DataFrame) -> pd.Series:
        assert train_returns.index.max() < idx[6] or train_returns.index.max() < returns.index[-1]
        return pd.Series(1 / train_returns.shape[1], index=train_returns.columns)

    bt = WalkForwardBacktester(BacktestConfig(train_size=6, test_size=3, step_size=3, cost_bps=0))
    result = bt.run(returns, strategy)
    assert not result.portfolio_returns.empty
    assert result.weights.shape[0] == 2


def test_walk_forward_backtester_rejects_missing_test_returns_instead_of_zero_filling():
    idx = pd.date_range("2020-01-31", periods=6, freq="ME")
    returns = pd.DataFrame(
        {"A": [0.01, 0.01, 0.01, None, 0.02, 0.02], "B": [0.01] * 6},
        index=idx,
    )
    bt = WalkForwardBacktester(BacktestConfig(train_size=3, test_size=3, step_size=3, cost_bps=0))

    with pytest.raises(ValueError, match="missing returns in test window"):
        bt.run(returns, lambda train: pd.Series(0.5, index=train.columns))


def test_required_observations_is_train_plus_test_window():
    assert required_observations(train_size=36, test_size=12) == 48


def test_walk_forward_backtester_can_simulate_buy_and_hold_weight_drift_between_rebalances():
    idx = pd.date_range("2024-01-31", periods=4, freq="ME")
    returns = pd.DataFrame(
        {
            "WINNER": [0.0, 1.0, 0.0, 0.0],
            "LOSER": [0.0, 0.0, 0.0, 0.0],
        },
        index=idx,
    )
    def strategy(train: pd.DataFrame) -> pd.Series:
        return pd.Series({"WINNER": 0.5, "LOSER": 0.5})

    bt = WalkForwardBacktester(
        BacktestConfig(train_size=1, test_size=3, step_size=3, cost_bps=0, weight_drift="buy_and_hold")
    )

    result = bt.run(returns, strategy)

    # First OOS month has equal weights; after WINNER doubles, its portfolio weight drifts to 2/3.
    assert result.portfolio_returns.tolist() == [0.5, 0.0, 0.0]
    assert result.weights.loc[idx[1], "WINNER"] == 0.5
    assert result.effective_weights.loc[idx[2], "WINNER"] == 2 / 3


def test_walk_forward_backtester_preserves_constant_mix_mode_for_legacy_comparisons():
    idx = pd.date_range("2024-01-31", periods=4, freq="ME")
    returns = pd.DataFrame(
        {
            "WINNER": [0.0, 1.0, 1.0, 0.0],
            "LOSER": [0.0, 0.0, 0.0, 0.0],
        },
        index=idx,
    )
    def strategy(train: pd.DataFrame) -> pd.Series:
        return pd.Series({"WINNER": 0.5, "LOSER": 0.5})

    result = WalkForwardBacktester(
        BacktestConfig(train_size=1, test_size=3, step_size=3, cost_bps=0, weight_drift="constant_mix")
    ).run(returns, strategy)

    assert result.portfolio_returns.tolist() == [0.5, 0.5, 0.0]
    assert result.effective_weights.loc[idx[2], "WINNER"] == 0.5


def test_walk_forward_backtester_reports_window_diagnostics_for_annual_2021_2024():
    prices = pd.DataFrame(
        {"SPY": np.linspace(100.0, 150.0, 48)},
        index=pd.date_range("2021-01-31", periods=48, freq="ME"),
    )
    returns = returns_from_prices(prices)
    bt = WalkForwardBacktester(BacktestConfig(train_size=36, test_size=12, step_size=12, cost_bps=0))

    with pytest.raises(ValueError) as excinfo:
        bt.run(returns, lambda train: pd.Series(1.0, index=train.columns))

    message = str(excinfo.value)
    assert "not enough observations" in message
    assert "actual=47" in message
    assert "required=48" in message
    assert "train_size=36" in message
    assert "test_size=12" in message
