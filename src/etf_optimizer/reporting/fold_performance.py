from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from etf_optimizer.backtesting.metrics import performance_summary


def _fold_slices(length: int, test_size: int) -> list[tuple[int, int]]:
    return [(start, min(start + test_size, length)) for start in range(0, length, test_size)]


def fold_performance_table(
    strategy_returns: Mapping[str, pd.Series],
    *,
    test_size: int,
    periods_per_year: int,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """Summarize performance per OOS fold for each strategy.

    The input returns are already out-of-sample. ``test_size`` is therefore the
    number of return periods in each evaluation fold, not the training-window
    length.
    """
    if not strategy_returns:
        raise ValueError("strategy_returns must contain at least one strategy")
    if test_size <= 0:
        raise ValueError("test_size must be positive")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    rows: list[dict[str, float | int | str | bool]] = []
    for strategy_name, returns in strategy_returns.items():
        clean = pd.Series(returns, dtype="float64").dropna()
        if clean.empty:
            continue
        strategy_rows: list[dict[str, float | int | str | bool]] = []
        for fold_idx, (start, end) in enumerate(_fold_slices(len(clean), test_size), start=1):
            fold_returns = clean.iloc[start:end]
            if fold_returns.empty:
                continue
            metrics = performance_summary(fold_returns, risk_free_rate, periods_per_year)
            cumulative_return = float((1.0 + fold_returns).prod() - 1.0)
            row: dict[str, float | int | str | bool] = {
                "strategy": strategy_name,
                "fold": fold_idx,
                "start_date": fold_returns.index[0].strftime("%Y-%m-%d"),
                "end_date": fold_returns.index[-1].strftime("%Y-%m-%d"),
                "n_observations": int(len(fold_returns)),
                "cumulative_return": cumulative_return,
                "cagr": float(metrics["cagr"]),
                "volatility": float(metrics["volatility"]),
                "sharpe": float(metrics["sharpe"]),
                "sortino": float(metrics["sortino"]),
                "max_drawdown": float(metrics["max_drawdown"]),
                "calmar": float(metrics["calmar"]),
                "is_worst_strategy_fold": False,
            }
            strategy_rows.append(row)

        if strategy_rows:
            worst_idx = min(range(len(strategy_rows)), key=lambda i: float(strategy_rows[i]["cumulative_return"]))
            strategy_rows[worst_idx]["is_worst_strategy_fold"] = True
            rows.extend(strategy_rows)

    return pd.DataFrame(rows)[
        [
            "strategy",
            "fold",
            "start_date",
            "end_date",
            "n_observations",
            "cumulative_return",
            "cagr",
            "volatility",
            "sharpe",
            "sortino",
            "max_drawdown",
            "calmar",
            "is_worst_strategy_fold",
        ]
    ]
