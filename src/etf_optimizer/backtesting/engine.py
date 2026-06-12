from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import pandas as pd

from etf_optimizer.optimization.rebalancing import apply_transaction_cost, compute_turnover

WeightDriftMode = Literal["constant_mix", "buy_and_hold"]
RebalancePolicy = Literal["calendar", "threshold"]


@dataclass(frozen=True)
class BacktestConfig:
    train_size: int
    test_size: int
    step_size: int
    cost_bps: float = 0.0
    weight_drift: WeightDriftMode = "constant_mix"
    rebalance_policy: RebalancePolicy = "calendar"
    drift_tolerance: float = 0.05


@dataclass(frozen=True)
class BacktestResult:
    portfolio_returns: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series
    effective_weights: pd.DataFrame
    rebalance_events: pd.DataFrame


def required_observations(train_size: int, test_size: int) -> int:
    """Minimum return observations needed for one walk-forward fold."""
    return train_size + test_size


class WalkForwardBacktester:
    """Walk-forward engine that prevents look-ahead bias by construction.

    Strategy functions receive only the in-sample training window. Returned weights
    are then applied to the following out-of-sample test window.
    """

    def __init__(self, config: BacktestConfig):
        if min(config.train_size, config.test_size, config.step_size) <= 0:
            raise ValueError("train_size, test_size and step_size must be positive")
        if config.weight_drift not in {"constant_mix", "buy_and_hold"}:
            raise ValueError("weight_drift must be 'constant_mix' or 'buy_and_hold'")
        if config.rebalance_policy not in {"calendar", "threshold"}:
            raise ValueError("rebalance_policy must be 'calendar' or 'threshold'")
        if config.drift_tolerance < 0:
            raise ValueError("drift_tolerance must be non-negative")
        self.config = config

    def _threshold_event_turnover(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series,
    ) -> tuple[bool, float, float]:
        drift = (current_weights - target_weights).abs()
        max_abs_drift = float(drift.max()) if not drift.empty else 0.0
        if self.config.rebalance_policy != "threshold" or max_abs_drift <= self.config.drift_tolerance:
            return False, max_abs_drift, 0.0
        return True, max_abs_drift, compute_turnover(current_weights, target_weights)

    def _apply_test_window(
        self,
        test: pd.DataFrame,
        weights: pd.Series,
        turnover: float,
    ) -> tuple[pd.Series, list[pd.Series], list[dict[str, float | str | pd.Timestamp]]]:
        invested_weights = weights[weights.abs() > 0.0].astype(float)
        invested_test = test[invested_weights.index]
        if invested_test.isna().any().any():
            missing_counts = invested_test.isna().sum()
            missing_assets = missing_counts[missing_counts > 0].index.tolist()
            raise ValueError(f"missing returns in test window for invested assets: {missing_assets}")

        net_values: list[float] = []
        effective_rows: list[pd.Series] = []
        event_rows: list[dict[str, float | str | pd.Timestamp]] = []
        target_weights = invested_weights / invested_weights.sum()
        current_weights = target_weights.copy()
        for period_idx, (date, period_returns) in enumerate(invested_test.iterrows()):
            event_turnover = 0.0
            if period_idx == 0:
                event_turnover = turnover
                event_rows.append(
                    {
                        "date": date,
                        "event_type": "calendar",
                        "turnover": event_turnover,
                        "max_abs_drift": 0.0,
                    }
                )
            else:
                should_rebalance, max_abs_drift, event_turnover = self._threshold_event_turnover(
                    current_weights,
                    target_weights,
                )
                if should_rebalance:
                    event_rows.append(
                        {
                            "date": date,
                            "event_type": "threshold",
                            "turnover": event_turnover,
                            "max_abs_drift": max_abs_drift,
                        }
                    )
                    current_weights = target_weights.copy()

            effective_rows.append(pd.Series(current_weights, name=date))
            period_return = float((period_returns * current_weights).sum())
            if event_turnover:
                period_return = apply_transaction_cost(period_return, event_turnover, self.config.cost_bps)
            net_values.append(period_return)
            if self.config.weight_drift == "buy_and_hold":
                growth = 1.0 + period_return
                if growth != 0:
                    current_weights = current_weights * (1.0 + period_returns) / growth
                    current_weights = current_weights / current_weights.sum()
            else:
                current_weights = target_weights.copy()
        return pd.Series(net_values, index=test.index), effective_rows, event_rows

    def run(self, returns: pd.DataFrame, strategy: Callable[[pd.DataFrame], pd.Series]) -> BacktestResult:
        returns = returns.sort_index().dropna(axis=1, how="all")
        portfolio_returns: list[pd.Series] = []
        weight_rows: list[pd.Series] = []
        effective_weight_rows: list[pd.Series] = []
        event_rows: list[dict[str, float | str | pd.Timestamp]] = []
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
            weight_rows.append(pd.Series(weights, name=rebalance_date))

            net, effective_rows, window_events = self._apply_test_window(test, weights, turnover)
            portfolio_returns.append(net)
            effective_weight_rows.extend(
                row.reindex(returns.columns, fill_value=0.0) for row in effective_rows
            )
            event_rows.extend(window_events)
            previous_weights = weights
            start += self.config.step_size

        if not portfolio_returns:
            actual = len(returns)
            required = required_observations(self.config.train_size, self.config.test_size)
            raise ValueError(
                "not enough observations for configured walk-forward windows "
                f"(actual={actual}, required={required}, "
                f"train_size={self.config.train_size}, test_size={self.config.test_size})"
            )

        rebalance_events = pd.DataFrame(event_rows)
        if not rebalance_events.empty:
            rebalance_events = rebalance_events.set_index("date").sort_index()
        turnover = (
            rebalance_events["turnover"]
            if not rebalance_events.empty
            else pd.Series(dtype=float)
        )
        return BacktestResult(
            portfolio_returns=pd.concat(portfolio_returns).sort_index(),
            weights=pd.DataFrame(weight_rows),
            turnover=turnover,
            effective_weights=pd.DataFrame(effective_weight_rows),
            rebalance_events=rebalance_events,
        )
