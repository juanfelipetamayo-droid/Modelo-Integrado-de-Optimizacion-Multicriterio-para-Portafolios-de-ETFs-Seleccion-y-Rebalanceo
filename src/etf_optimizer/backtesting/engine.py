from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from etf_optimizer.optimization.rebalancing import apply_transaction_cost, compute_turnover


@dataclass(frozen=True)
class BacktestConfig:
    train_size: int
    test_size: int
    step_size: int
    cost_bps: float = 0.0


@dataclass(frozen=True)
class BacktestResult:
    portfolio_returns: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series


class WalkForwardBacktester:
    """Walk-forward engine that prevents look-ahead bias by construction.

    Strategy functions receive only the in-sample training window. Returned weights
    are then applied to the following out-of-sample test window.
    """

    def __init__(self, config: BacktestConfig):
        if min(config.train_size, config.test_size, config.step_size) <= 0:
            raise ValueError("train_size, test_size and step_size must be positive")
        self.config = config

    def run(self, returns: pd.DataFrame, strategy: Callable[[pd.DataFrame], pd.Series]) -> BacktestResult:
        returns = returns.sort_index().dropna(axis=1, how="all")
        portfolio_returns: list[pd.Series] = []
        weight_rows: list[pd.Series] = []
        turnover_rows: dict[pd.Timestamp, float] = {}
        previous_weights = pd.Series(dtype=float)

        start = 0
        while start + self.config.train_size + self.config.test_size <= len(returns):
            train = returns.iloc[start : start + self.config.train_size]
            test = returns.iloc[
                start + self.config.train_size : start + self.config.train_size + self.config.test_size
            ]
            weights = strategy(train).astype(float)
            weights = weights / weights.sum()
            weights = weights.reindex(returns.columns, fill_value=0.0)
            rebalance_date = test.index[0]
            turnover = compute_turnover(previous_weights, weights)
            turnover_rows[rebalance_date] = turnover
            weight_rows.append(pd.Series(weights, name=rebalance_date))

            gross = test[weights.index].fillna(0.0).dot(weights)
            net = gross.copy()
            net.iloc[0] = apply_transaction_cost(float(net.iloc[0]), turnover, self.config.cost_bps)
            portfolio_returns.append(net)
            previous_weights = weights
            start += self.config.step_size

        if not portfolio_returns:
            raise ValueError("not enough observations for configured walk-forward windows")

        return BacktestResult(
            portfolio_returns=pd.concat(portfolio_returns).sort_index(),
            weights=pd.DataFrame(weight_rows),
            turnover=pd.Series(turnover_rows),
        )
