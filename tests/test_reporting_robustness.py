from __future__ import annotations

import pandas as pd
import pytest

from etf_optimizer.reporting.robustness import (
    bootstrap_metric_intervals,
    cost_sensitivity_table,
    electre_sensitivity_table,
)
from etf_optimizer.selection.electre_tri import Criterion, Profile


def test_cost_sensitivity_reprices_net_returns_from_turnover_and_base_cost():
    idx = pd.date_range("2024-01-31", periods=4, freq="ME")
    net = pd.Series([0.009, 0.020, -0.010, 0.030], index=idx, name="strategy")
    turnover = pd.Series([1.0, 0.5], index=[idx[0], idx[2]])

    table = cost_sensitivity_table(
        net,
        turnover,
        base_cost_bps=10.0,
        cost_bps_grid=[0.0, 10.0, 20.0],
        periods_per_year=12,
    )

    assert table["cost_bps"].tolist() == [0.0, 10.0, 20.0]
    assert table.loc[table["cost_bps"] == 0.0, "total_return"].iloc[0] > table.loc[
        table["cost_bps"] == 20.0, "total_return"
    ].iloc[0]
    assert table.loc[table["cost_bps"] == 10.0, "mean_rebalance_cost"].iloc[0] == 0.00075


def test_bootstrap_metric_intervals_are_reproducible_and_include_columns():
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    returns = pd.Series([0.01, 0.02, -0.01, 0.015] * 6, index=idx)

    first = bootstrap_metric_intervals(returns, n_bootstrap=100, random_state=7, periods_per_year=12)
    second = bootstrap_metric_intervals(returns, n_bootstrap=100, random_state=7, periods_per_year=12)

    assert first.equals(second)
    assert {"metric", "estimate", "ci_lower", "ci_upper", "n_bootstrap"}.issubset(first.columns)
    assert set(first["metric"]) >= {"cagr", "volatility", "sharpe", "max_drawdown"}
    assert (first["ci_lower"] <= first["ci_upper"]).all()


def test_cost_sensitivity_rejects_invalid_cost_inputs():
    idx = pd.date_range("2024-01-31", periods=2, freq="ME")
    returns = pd.Series([0.01, 0.02], index=idx)
    turnover = pd.Series([1.0], index=[idx[0]])

    with pytest.raises(ValueError, match="cost_bps_grid"):
        cost_sensitivity_table(
            returns,
            turnover,
            base_cost_bps=10.0,
            cost_bps_grid=[10.0, -1.0],
            periods_per_year=12,
        )
    with pytest.raises(ValueError, match="turnover"):
        cost_sensitivity_table(
            returns,
            pd.Series([-0.1], index=[idx[0]]),
            base_cost_bps=10.0,
            cost_bps_grid=[10.0],
            periods_per_year=12,
        )


def test_electre_sensitivity_table_records_selected_assets_by_parameter_case():
    features = pd.DataFrame(
        {
            "cagr": [0.12, 0.02, 0.08],
            "volatility": [0.10, 0.05, 0.22],
            "sharpe": [1.0, 0.4, 0.5],
            "sortino": [1.5, 0.8, 0.6],
        },
        index=["AAA", "BBB", "CCC"],
    )
    criteria = [
        Criterion("cagr", weight=0.35, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("volatility", weight=0.25, preference_direction="min", q=0.0, p=0.02, v=0.10),
        Criterion("sharpe", weight=0.25, preference_direction="max", q=0.0, p=0.1, v=0.3),
        Criterion("sortino", weight=0.15, preference_direction="max", q=0.0, p=0.1, v=0.3),
    ]
    profiles = [Profile("acceptable", {"cagr": 0.03, "volatility": 0.25, "sharpe": 0.3, "sortino": 0.4})]

    table = electre_sensitivity_table(
        features,
        criteria,
        profiles,
        lambda_values=[0.65, 0.75],
        weight_multipliers=[{"cagr": 1.0}, {"cagr": 1.25, "volatility": 0.8}],
    )

    assert table.shape[0] == 12
    assert {"case_id", "lambda_cut", "ticker", "selected", "category"}.issubset(table.columns)
    assert set(table["ticker"]) == {"AAA", "BBB", "CCC"}
    assert table.groupby("case_id")["ticker"].nunique().eq(3).all()
