from __future__ import annotations

import pandas as pd

from etf_optimizer.reporting.holdings_attribution import fold_holdings_attribution_table


def test_fold_holdings_attribution_sums_weighted_contributions_by_fold_and_ticker():
    idx = pd.date_range("2020-01-31", periods=4, freq="ME")
    returns = pd.DataFrame(
        {
            "AAA": [0.10, -0.20, 0.05, 0.00],
            "BBB": [0.00, -0.10, 0.02, 0.04],
        },
        index=idx,
    )
    weights = pd.DataFrame(
        {
            "AAA": [0.6, 0.5, 0.2, 0.0],
            "BBB": [0.4, 0.5, 0.8, 1.0],
        },
        index=idx,
    )
    metadata = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "fund_family": ["Family A", "Family B"],
            "category": ["Equity", "Bond"],
        }
    )

    table = fold_holdings_attribution_table(
        returns,
        weights,
        test_size=2,
        metadata=metadata,
        min_abs_weight=0.0,
    )

    aaa_fold1 = table[(table["fold"] == 1) & (table["ticker"] == "AAA")].iloc[0]
    assert aaa_fold1["start_date"] == "2020-01-31"
    assert aaa_fold1["end_date"] == "2020-02-29"
    assert aaa_fold1["n_observations"] == 2
    assert aaa_fold1["avg_weight"] == 0.55
    assert round(aaa_fold1["total_contribution"], 6) == -0.04
    assert round(aaa_fold1["asset_cumulative_return"], 6) == -0.12
    assert aaa_fold1["fund_family"] == "Family A"
    assert aaa_fold1["category"] == "Equity"

    fold2 = table[table["fold"] == 2].sort_values("total_contribution")
    assert fold2["ticker"].tolist() == ["AAA", "BBB"]
    assert round(float(fold2[fold2["ticker"] == "BBB"]["total_contribution"].iloc[0]), 6) == 0.056


def test_fold_holdings_attribution_filters_zero_weight_assets_and_rejects_bad_test_size():
    idx = pd.date_range("2020-01-31", periods=2, freq="ME")
    returns = pd.DataFrame({"AAA": [0.01, 0.02], "ZERO": [0.50, 0.50]}, index=idx)
    weights = pd.DataFrame({"AAA": [1.0, 1.0], "ZERO": [0.0, 0.0]}, index=idx)

    table = fold_holdings_attribution_table(returns, weights, test_size=2, min_abs_weight=0.001)

    assert table["ticker"].tolist() == ["AAA"]

    try:
        fold_holdings_attribution_table(returns, weights, test_size=0)
    except ValueError as exc:
        assert "test_size must be positive" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
