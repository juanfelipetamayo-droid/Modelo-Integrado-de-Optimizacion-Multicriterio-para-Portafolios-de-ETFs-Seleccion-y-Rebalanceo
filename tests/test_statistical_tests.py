from __future__ import annotations

import pandas as pd
import pytest

from etf_optimizer.reporting.statistical_tests import paired_benchmark_tests_table


def test_paired_benchmark_tests_table_reports_metric_differences_and_claims():
    idx = pd.date_range("2020-01-31", periods=36, freq="ME")
    strategy = pd.Series([0.020, 0.018, 0.022, 0.019, 0.021, 0.020] * 6, index=idx)
    weak = pd.Series([0.010, 0.009, 0.011, 0.010, 0.009, 0.010] * 6, index=idx)
    strong = pd.Series([0.030, 0.028, 0.032, 0.031, 0.029, 0.030] * 6, index=idx)

    table = paired_benchmark_tests_table(
        strategy,
        {"weak_benchmark": weak, "strong_benchmark": strong},
        n_bootstrap=300,
        random_state=11,
        periods_per_year=12,
    )

    assert set(table["benchmark"]) == {"weak_benchmark", "strong_benchmark"}
    assert set(table["metric"]) >= {"cagr", "sharpe", "max_drawdown"}
    expected_columns = {
        "benchmark",
        "metric",
        "strategy_value",
        "benchmark_value",
        "difference",
        "ci_lower",
        "ci_upper",
        "confidence_level",
        "n_observations",
        "n_bootstrap",
        "conclusion",
    }
    assert expected_columns.issubset(table.columns)

    weak_cagr = table[(table["benchmark"] == "weak_benchmark") & (table["metric"] == "cagr")].iloc[0]
    strong_cagr = table[(table["benchmark"] == "strong_benchmark") & (table["metric"] == "cagr")].iloc[0]
    assert weak_cagr["difference"] > 0
    assert weak_cagr["ci_lower"] > 0
    assert weak_cagr["conclusion"] == "strategy_positive"
    assert strong_cagr["difference"] < 0
    assert strong_cagr["ci_upper"] < 0
    assert strong_cagr["conclusion"] == "strategy_negative"


def test_paired_benchmark_tests_aligns_dates_and_rejects_short_overlap():
    strategy = pd.Series(
        [0.01, 0.02, 0.03, 0.04],
        index=pd.date_range("2024-01-31", periods=4, freq="ME"),
    )
    benchmark = pd.Series(
        [0.00, 0.01, 0.02, 0.03],
        index=pd.date_range("2024-02-29", periods=4, freq="ME"),
    )

    table = paired_benchmark_tests_table(
        strategy,
        {"shifted": benchmark},
        n_bootstrap=50,
        random_state=3,
        periods_per_year=12,
        min_observations=3,
    )

    assert table["n_observations"].unique().tolist() == [3]

    with pytest.raises(ValueError, match="at least 4 overlapping observations"):
        paired_benchmark_tests_table(
            strategy,
            {"shifted": benchmark},
            n_bootstrap=50,
            random_state=3,
            periods_per_year=12,
            min_observations=4,
        )
