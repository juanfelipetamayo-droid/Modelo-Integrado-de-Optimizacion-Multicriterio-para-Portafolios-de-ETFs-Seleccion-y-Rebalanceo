from __future__ import annotations

import pandas as pd

from etf_optimizer.reporting.fold_performance import fold_performance_table


def test_fold_performance_table_splits_oos_returns_and_marks_worst_fold():
    idx = pd.date_range("2020-01-31", periods=6, freq="ME")
    strategy_returns = {
        "ELECTRE_MaxSharpe_walk_forward": pd.Series([0.10, -0.05, -0.30, -0.20, 0.04, 0.03], index=idx),
        "SPY_buy_hold": pd.Series([0.02, 0.01, -0.03, 0.02, 0.03, 0.02], index=idx),
    }

    table = fold_performance_table(strategy_returns, test_size=2, periods_per_year=12)

    assert set(table["strategy"]) == {"ELECTRE_MaxSharpe_walk_forward", "SPY_buy_hold"}
    electre = table[table["strategy"] == "ELECTRE_MaxSharpe_walk_forward"].reset_index(drop=True)
    assert electre["fold"].tolist() == [1, 2, 3]
    assert electre["start_date"].tolist() == ["2020-01-31", "2020-03-31", "2020-05-31"]
    assert electre["end_date"].tolist() == ["2020-02-29", "2020-04-30", "2020-06-30"]
    assert electre["n_observations"].tolist() == [2, 2, 2]
    assert electre["cumulative_return"].round(4).tolist() == [0.045, -0.44, 0.0712]
    assert electre["is_worst_strategy_fold"].tolist() == [False, True, False]


def test_fold_performance_table_aligns_strategies_and_rejects_bad_test_size():
    idx = pd.date_range("2020-01-31", periods=4, freq="ME")
    table = fold_performance_table(
        {
            "strategy": pd.Series([0.01, 0.02, 0.03, 0.04], index=idx),
            "late_benchmark": pd.Series([0.05, 0.06], index=idx[2:]),
        },
        test_size=2,
        periods_per_year=12,
    )

    assert table["strategy"].tolist() == ["strategy", "strategy", "late_benchmark"]
    assert table["fold"].tolist() == [1, 2, 1]

    try:
        fold_performance_table({"strategy": pd.Series([0.01], index=idx[:1])}, test_size=0, periods_per_year=12)
    except ValueError as exc:
        assert "test_size must be positive" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
