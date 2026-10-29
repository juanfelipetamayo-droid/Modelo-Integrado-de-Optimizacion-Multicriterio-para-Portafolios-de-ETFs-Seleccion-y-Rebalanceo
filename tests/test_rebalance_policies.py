from __future__ import annotations

import pandas as pd

from etf_optimizer.backtesting.engine import BacktestConfig, WalkForwardBacktester


def _equal_split_strategy(train: pd.DataFrame) -> pd.Series:
    return pd.Series({"WINNER": 0.5, "LOSER": 0.5})


def test_threshold_rebalance_resets_weights_when_drift_exceeds_tolerance_and_records_event():
    idx = pd.date_range("2024-01-31", periods=4, freq="ME")
    returns = pd.DataFrame(
        {
            "WINNER": [0.0, 1.0, 1.0, 0.0],
            "LOSER": [0.0, 0.0, 0.0, 0.0],
        },
        index=idx,
    )
    bt = WalkForwardBacktester(
        BacktestConfig(
            train_size=1,
            test_size=3,
            step_size=3,
            cost_bps=0,
            weight_drift="buy_and_hold",
            rebalance_policy="threshold",
            drift_tolerance=0.10,
        )
    )

    result = bt.run(returns, _equal_split_strategy)

    assert result.portfolio_returns.tolist() == [0.5, 0.5, 0.0]
    assert result.effective_weights.loc[idx[1], "WINNER"] == 0.5
    assert result.effective_weights.loc[idx[2], "WINNER"] == 0.5
    assert result.rebalance_events.loc[idx[1], "event_type"] == "calendar"
    assert result.rebalance_events.loc[idx[2], "event_type"] == "threshold"
    assert result.rebalance_events.loc[idx[2], "max_abs_drift"] > 0.10


def test_calendar_rebalance_policy_does_not_reset_intrawindow_drift():
    idx = pd.date_range("2024-01-31", periods=4, freq="ME")
    returns = pd.DataFrame(
        {
            "WINNER": [0.0, 1.0, 1.0, 0.0],
            "LOSER": [0.0, 0.0, 0.0, 0.0],
        },
        index=idx,
    )
    bt = WalkForwardBacktester(
        BacktestConfig(
            train_size=1,
            test_size=3,
            step_size=3,
            cost_bps=0,
            weight_drift="buy_and_hold",
            rebalance_policy="calendar",
        )
    )

    result = bt.run(returns, _equal_split_strategy)

    assert result.portfolio_returns.tolist() == [0.5, 2 / 3, 0.0]
    assert result.effective_weights.loc[idx[2], "WINNER"] == 2 / 3
    assert result.rebalance_events["event_type"].tolist() == ["calendar"]
