from __future__ import annotations

import numpy as np
import pandas as pd

from etf_optimizer.features import (
    annualized_return,
    annualized_volatility,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    compute_feature_table,
    tracking_error,
)


def test_annualized_return_uses_geometric_compounding():
    returns = pd.Series([0.01, 0.01, 0.01, 0.01])
    result = annualized_return(returns, periods_per_year=4)
    assert np.isclose(result, (1.01**4) - 1)


def test_risk_metrics_handle_drawdown_and_downside_risk():
    returns = pd.Series([0.10, -0.20, 0.05, -0.10, 0.04])
    assert max_drawdown(returns) < 0
    assert annualized_volatility(returns, periods_per_year=5) > 0
    assert np.isfinite(sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=5))
    assert np.isfinite(sortino_ratio(returns, risk_free_rate=0.0, periods_per_year=5))


def test_compute_feature_table_creates_expected_columns():
    prices = pd.DataFrame(
        {
            "AAA": [100, 101, 102, 103, 104],
            "BBB": [50, 49, 51, 50, 52],
        },
        index=pd.date_range("2024-01-01", periods=5),
    )
    volume = pd.DataFrame(
        {"AAA": [1000, 1200, 1100, 1300, 1250], "BBB": [500, 450, 600, 550, 700]},
        index=prices.index,
    )
    benchmark = pd.Series([0.001, 0.002, -0.001, 0.003], index=prices.index[1:])
    table = compute_feature_table(
        prices,
        volume=volume,
        benchmark_returns=benchmark,
        expense_ratios={"AAA": 0.0003, "BBB": 0.0010},
        periods_per_year=252,
    )
    assert set(
        [
            "cagr",
            "volatility",
            "sharpe",
            "sortino",
            "max_drawdown",
            "avg_dollar_volume",
            "liquidity",
            "tracking_error",
            "expense_ratio",
        ]
    ).issubset(table.columns)
    assert list(table.index) == ["AAA", "BBB"]
    assert table.loc["AAA", "liquidity"] == table.loc["AAA", "avg_dollar_volume"]
    assert table.loc["AAA", "expense_ratio"] == 0.0003


def test_tracking_error_is_annualized_active_return_volatility():
    returns = pd.Series([0.02, 0.01, -0.01, 0.03])
    benchmark = pd.Series([0.01, 0.00, 0.00, 0.02])
    expected = ((returns - benchmark).std(ddof=1)) * np.sqrt(4)
    assert np.isclose(tracking_error(returns, benchmark, periods_per_year=4), expected)
