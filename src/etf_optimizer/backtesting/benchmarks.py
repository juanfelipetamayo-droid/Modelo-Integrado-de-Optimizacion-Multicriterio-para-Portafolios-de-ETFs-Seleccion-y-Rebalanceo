from __future__ import annotations

from typing import Callable

import pandas as pd

from etf_optimizer.backtesting.engine import BacktestConfig, BacktestResult, WalkForwardBacktester
from etf_optimizer.optimization.portfolio import (
    equal_weight,
    max_sharpe_weights,
    min_variance_weights,
    ledoit_wolf_covariance,
    sample_covariance,
)


def benchmark_spy(
    returns: pd.DataFrame,
    spy_ticker: str = "SPY",
) -> pd.Series:
    """Single-asset benchmark: buy and hold SPY."""
    if spy_ticker not in returns.columns:
        raise ValueError(f"{spy_ticker} not in returns DataFrame")
    return returns[spy_ticker]


def benchmark_60_40(
    returns: pd.DataFrame,
    equity_ticker: str = "SPY",
    bond_ticker: str = "BND",
    equity_weight: float = 0.6,
    rebalance_periods: int = 12,
) -> pd.Series:
    """Fixed-weight 60/40 portfolio with periodic rebalancing."""
    for t in [equity_ticker, bond_ticker]:
        if t not in returns.columns:
            raise ValueError(f"{t} not in returns DataFrame")

    weights = pd.Series({equity_ticker: equity_weight, bond_ticker: 1.0 - equity_weight})
    portfolio = pd.Series(index=returns.index, dtype=float)

    for i in range(len(returns)):
        if i % rebalance_periods == 0:
            weights = pd.Series({equity_ticker: equity_weight, bond_ticker: 1.0 - equity_weight})
        r = returns.iloc[i][weights.index]
        period_return = float((r * weights).sum())
        portfolio.iloc[i] = period_return
        # Let weights drift after returns, normalized by portfolio growth.
        weights = weights * (1.0 + r) / (1.0 + period_return)

    return portfolio


def benchmark_equal_weight(
    returns: pd.DataFrame,
) -> pd.Series:
    """Equal-weight portfolio of all available assets, rebalanced each period."""
    w = equal_weight(returns.columns)
    return returns.dot(w)


def benchmark_min_variance(
    returns: pd.DataFrame,
    periods_per_year: int = 252,
    max_weight: float | None = None,
) -> pd.Series:
    """Minimum-variance portfolio (no expected return input)."""
    cov = (
        ledoit_wolf_covariance(returns, periods_per_year)
        if len(returns) > returns.shape[1]
        else sample_covariance(returns, periods_per_year)
    )
    w = min_variance_weights(cov, max_weight=max_weight)
    return returns.dot(w)


def benchmark_max_sharpe(
    returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    max_weight: float | None = None,
) -> pd.Series:
    """Maximum Sharpe ratio portfolio (in-sample)."""
    cov = (
        ledoit_wolf_covariance(returns, periods_per_year)
        if len(returns) > returns.shape[1]
        else sample_covariance(returns, periods_per_year)
    )
    expected = returns.mean() * periods_per_year
    w = max_sharpe_weights(expected, cov, risk_free_rate=risk_free_rate, max_weight=max_weight)
    return returns.dot(w)


def run_benchmark_comparison(
    returns: pd.DataFrame,
    benchmark_funcs: dict[str, Callable[[pd.DataFrame], pd.Series]],
) -> pd.DataFrame:
    """Run multiple benchmark strategies and return a DataFrame of portfolio returns."""
    results: dict[str, pd.Series] = {}
    for name, func in benchmark_funcs.items():
        try:
            results[name] = func(returns)
        except Exception:
            results[name] = pd.Series(index=returns.index, dtype=float)
    return pd.DataFrame(results)


def run_walk_forward_benchmarks(
    returns: pd.DataFrame,
    config: BacktestConfig,
    strategies: dict[str, Callable[[pd.DataFrame], pd.Series]],
) -> dict[str, BacktestResult]:
    """Run multiple strategies through the walk-forward backtester."""
    bt = WalkForwardBacktester(config)
    results: dict[str, BacktestResult] = {}
    for name, strategy_fn in strategies.items():
        try:
            results[name] = bt.run(returns, strategy_fn)
        except Exception:
            continue
    return results
