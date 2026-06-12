from __future__ import annotations

import pandas as pd
import pytest

from etf_optimizer.data.sec_universe import PointInTimeETFUniverseProvider
from etf_optimizer.pipeline import PipelineConfig, _make_strategy, _optimize_weights, run_research_pipeline
from etf_optimizer.selection.electre_tri import Criterion, Profile


def test_strategy_rejects_missing_training_returns_instead_of_zero_filling():
    strategy = _make_strategy(
        PipelineConfig(criteria=[], profiles=[], strategy="equal_weight"),
        selected_assets=["AAA", "BBB"],
    )
    train_returns = pd.DataFrame(
        {
            "AAA": [0.01, None, 0.02],
            "BBB": [0.02, 0.01, 0.03],
        }
    )

    with pytest.raises(ValueError, match="missing returns"):
        strategy(train_returns)




def test_max_sharpe_strategy_falls_back_to_min_variance_when_optimizer_fails(monkeypatch):
    calls: list[str] = []

    def fail_max_sharpe(*args, **kwargs):
        calls.append("max_sharpe")
        raise RuntimeError("solver failed")

    def succeed_min_variance(cov: pd.DataFrame, max_weight: float | None = None) -> pd.Series:
        calls.append("min_variance")
        return pd.Series({"AAA": 0.25, "BBB": 0.75})

    monkeypatch.setattr("etf_optimizer.pipeline.max_sharpe_weights", fail_max_sharpe)
    monkeypatch.setattr("etf_optimizer.pipeline.min_variance_weights", succeed_min_variance)
    train = pd.DataFrame({"AAA": [0.01, 0.02, 0.01], "BBB": [0.02, 0.01, 0.03]})

    weights, diagnostics = _optimize_weights(
        train,
        PipelineConfig(criteria=[], profiles=[], strategy="max_sharpe", optimizer_fallback=True),
    )

    assert weights.to_dict() == {"AAA": 0.25, "BBB": 0.75}
    assert calls == ["max_sharpe", "min_variance"]
    assert diagnostics == [
        {"strategy": "max_sharpe", "status": "failed", "error": "solver failed"},
        {"strategy": "min_variance", "status": "success", "error": ""},
    ]


def test_max_sharpe_strategy_raises_when_fallback_is_disabled(monkeypatch):
    def fail_max_sharpe(*args, **kwargs):
        raise RuntimeError("solver failed")

    monkeypatch.setattr("etf_optimizer.pipeline.max_sharpe_weights", fail_max_sharpe)
    train = pd.DataFrame({"AAA": [0.01, 0.02, 0.01], "BBB": [0.02, 0.01, 0.03]})

    with pytest.raises(RuntimeError, match="solver failed"):
        _optimize_weights(
            train,
            PipelineConfig(criteria=[], profiles=[], strategy="max_sharpe", optimizer_fallback=False),
        )


def test_run_research_pipeline_wires_features_selection_optimization_and_backtest():
    idx = pd.date_range("2020-01-31", periods=18, freq="ME")
    prices = pd.DataFrame(
        {
            "GOOD": [100, 101, 103, 104, 106, 108, 109, 111, 113, 115, 117, 119, 120, 122, 124, 126, 128, 130],
            "MID": [100, 100, 101, 101, 102, 103, 103, 104, 104, 105, 106, 106, 107, 108, 108, 109, 110, 110],
            "BAD": [100, 90, 91, 85, 86, 80, 82, 78, 79, 75, 76, 74, 73, 72, 71, 70, 69, 68],
        },
        index=idx,
    )
    volume = pd.DataFrame(1000, index=idx, columns=prices.columns)
    criteria = [
        Criterion("cagr", weight=0.5, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("volatility", weight=0.2, preference_direction="min", q=0.0, p=0.05, v=0.2),
        Criterion("sharpe", weight=0.3, preference_direction="max", q=0.0, p=0.2, v=0.6),
    ]
    profiles = [Profile("acceptable", {"cagr": 0.05, "volatility": 0.30, "sharpe": 0.2})]

    result = run_research_pipeline(
        prices,
        volume,
        PipelineConfig(criteria=criteria, profiles=profiles, train_size=6, test_size=3, step_size=3),
    )

    assert not result.features.empty
    assert "category" in result.selection.columns
    assert "GOOD" in result.selected_assets
    assert not result.backtest.portfolio_returns.empty
    assert "strategy" in result.summary.index


def test_run_research_pipeline_records_electre_selection_for_each_rebalance():
    idx = pd.date_range("2020-01-31", periods=12, freq="ME")
    prices = pd.DataFrame(
        {
            "GOOD": [100, 104, 108, 112, 116, 120, 121, 122, 123, 124, 125, 126],
            "BAD": [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89],
        },
        index=idx,
    )
    volume = pd.DataFrame(
        {
            "GOOD": [1_000] * len(idx),
            "BAD": [500] * len(idx),
        },
        index=idx,
    )
    config = PipelineConfig(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("acceptable", {"cagr": 0.05})],
        strategy="equal_weight",
        train_size=5,
        test_size=2,
        step_size=2,
        periods_per_year=12,
    )

    result = run_research_pipeline(prices, volume, config)

    expected_columns = [
        "rebalance_date",
        "ticker",
        "selected",
        "category",
        "thesis_category",
        "cagr",
        "volatility",
        "sharpe",
        "sortino",
        "liquidity",
        "avg_dollar_volume",
    ]
    assert result.selection_by_rebalance.columns.tolist() == expected_columns
    assert set(result.selection_by_rebalance["rebalance_date"]) == set(result.backtest.weights.index)
    assert result.selection_by_rebalance["rebalance_date"].nunique() == len(result.backtest.weights)
    assert set(result.selection_by_rebalance["ticker"]) == {"GOOD", "BAD"}
    first_rebalance = result.backtest.weights.index[0]
    first_rows = result.selection_by_rebalance[
        result.selection_by_rebalance["rebalance_date"] == first_rebalance
    ].set_index("ticker")
    assert bool(first_rows.loc["GOOD", "selected"])
    assert not bool(first_rows.loc["BAD", "selected"])


def test_run_research_pipeline_uses_point_in_time_universe_at_each_rebalance():
    idx = pd.date_range("2020-01-31", periods=14, freq="ME")
    prices = pd.DataFrame(
        {
            "OLD": [100, 102, 104, 106, 108, 110, 111, 112, 113, 114, 115, 116, 117, 118],
            "NEW": [100, 100, 100, 100, 100, 100, 105, 110, 115, 120, 126, 132, 138, 145],
        },
        index=idx,
    )
    volume = pd.DataFrame(1_000_000, index=idx, columns=prices.columns)
    provider = PointInTimeETFUniverseProvider(
        pd.DataFrame(
            {
                "ticker": ["OLD", "NEW"],
                "fund_id": ["OLD", "NEW"],
                "first_seen_date": ["2020-01-01", "2020-08-01"],
                "last_seen_date": ["2020-09-30", "2021-12-31"],
                "inception_date": ["2019-01-01", "2020-08-01"],
                "termination_date": [None, None],
                "is_etf_candidate": [True, True],
            }
        )
    )
    config = PipelineConfig(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("acceptable", {"cagr": 0.01})],
        strategy="equal_weight",
        train_size=4,
        test_size=3,
        step_size=3,
        periods_per_year=12,
        universe_provider=provider,
        universe_min_age_months=0,
    )

    result = run_research_pipeline(prices, volume, config)

    first_rebalance = result.backtest.weights.index[0]
    later_rebalance = result.backtest.weights.index[-1]
    first_tickers = set(
        result.selection_by_rebalance.loc[
            result.selection_by_rebalance["rebalance_date"] == first_rebalance,
            "ticker",
        ]
    )
    later_tickers = set(
        result.selection_by_rebalance.loc[
            result.selection_by_rebalance["rebalance_date"] == later_rebalance,
            "ticker",
        ]
    )
    assert first_tickers == {"OLD"}
    assert later_tickers == {"NEW"}
    assert result.backtest.weights.loc[first_rebalance, "NEW"] == 0.0
    assert result.backtest.weights.loc[later_rebalance, "OLD"] == 0.0


def test_run_research_pipeline_writes_separated_goal3_fold_artifacts(tmp_path):
    idx = pd.date_range("2020-01-31", periods=12, freq="ME")
    prices = pd.DataFrame(
        {
            "GOOD": [100, 104, 108, 112, 116, 120, 121, 122, 123, 124, 125, 126],
            "MID": [100, 101, 102, 103, 104, 105, 105, 106, 106, 107, 107, 108],
            "BAD": [100, 98, 96, 94, 92, 90, 89, 88, 87, 86, 85, 84],
        },
        index=idx,
    )
    volume = pd.DataFrame(1_000_000, index=idx, columns=prices.columns)
    artifact_dir = tmp_path / "fold_artifacts"
    config = PipelineConfig(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("acceptable", {"cagr": 0.02})],
        strategy="equal_weight",
        train_size=5,
        test_size=2,
        step_size=2,
        periods_per_year=12,
        fold_artifacts_dir=artifact_dir,
    )

    result = run_research_pipeline(prices, volume, config)

    assert result.fold_artifacts is not None
    assert len(result.fold_artifacts) == len(result.backtest.weights)
    expected_files = {
        "universe_snapshot.csv",
        "criteria_matrix.csv",
        "electre_assignments.csv",
        "flowsort_assignments.csv",
        "selected_etfs.csv",
        "portfolio_weights.csv",
        "fold_performance.csv",
        "classification_diagnostics.csv",
    }
    fold_dirs = sorted(path for path in artifact_dir.iterdir() if path.is_dir())
    assert len(fold_dirs) == len(result.backtest.weights)
    for fold_dir in fold_dirs:
        assert {path.name for path in fold_dir.iterdir()} == expected_files
        diagnostics = pd.read_csv(fold_dir / "classification_diagnostics.csv")
        assert "electre_flowsort_agreement_rate" in diagnostics.columns
        weights = pd.read_csv(fold_dir / "portfolio_weights.csv")
        assert "allocation_method" in weights.columns
        performance = pd.read_csv(fold_dir / "fold_performance.csv")
        assert "n_periods" in performance.columns


def test_run_research_pipeline_supports_thesis_aligned_selection_cardinality_and_peer_groups():
    idx = pd.date_range("2021-01-31", periods=16, freq="ME")
    data = {f"ETF{i:02d}": [100 + i + step * (1 + i / 100) for step in range(len(idx))] for i in range(12)}
    prices = pd.DataFrame(data, index=idx)
    volume = pd.DataFrame(1_000_000, index=idx, columns=prices.columns)
    metadata = pd.DataFrame(
        {
            "ticker": list(prices.columns),
            "peer_group": ["equity_broad"] * 6 + ["fixed_income"] * 6,
        }
    )
    criteria = [Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)]
    profiles = [Profile("minimum", {"cagr": 0.01}), Profile("preferred", {"cagr": 0.05})]

    result = run_research_pipeline(
        prices,
        volume,
        PipelineConfig(
            criteria=criteria,
            profiles=profiles,
            strategy="equal_weight",
            train_size=6,
            test_size=2,
            step_size=2,
            periods_per_year=12,
            asset_metadata=metadata,
            use_peer_group_profiles=True,
            peer_group_min_size=3,
            thesis_selection_min_assets=10,
            thesis_selection_max_assets=10,
        ),
    )

    first_rebalance = result.selection_by_rebalance["rebalance_date"].min()
    first_selected = result.selection_by_rebalance[
        (result.selection_by_rebalance["rebalance_date"] == first_rebalance)
        & (result.selection_by_rebalance["selected"])
    ]
    assert len(first_selected) == 10
    assert {"peer_group", "profile_scope", "thesis_category"}.issubset(result.selection_by_rebalance.columns)
