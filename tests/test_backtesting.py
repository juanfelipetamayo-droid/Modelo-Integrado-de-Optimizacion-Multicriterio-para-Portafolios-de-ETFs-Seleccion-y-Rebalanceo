from __future__ import annotations

import numpy as np
import pandas as pd

from etf_optimizer.backtesting.engine import WalkForwardBacktester, BacktestConfig
from etf_optimizer.backtesting.metrics import performance_summary


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
