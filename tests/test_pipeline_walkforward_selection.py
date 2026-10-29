from __future__ import annotations

import pandas as pd

from etf_optimizer.pipeline import PipelineConfig, run_research_pipeline
from etf_optimizer.selection.electre_tri import Criterion, Profile


def test_every_period_recategorization_records_category_change_rebalance():
    idx = pd.date_range("2020-01-31", periods=9, freq="ME")
    prices = pd.DataFrame(
        {
            "EARLY_WINNER": [100, 110, 121, 133, 120, 108, 97, 90, 85],
            "LATE_WINNER": [100, 95, 90, 86, 100, 116, 134, 155, 180],
        },
        index=idx,
    )
    config = PipelineConfig(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("preferred", {"cagr": 0.20})],
        strategy="equal_weight",
        train_size=3,
        test_size=3,
        step_size=3,
        periods_per_year=12,
        recategorization_policy="every_period",
    )

    result = run_research_pipeline(prices, volume=None, config=config)

    assert "category_change" in result.backtest.rebalance_events["event_type"].tolist()
    assert result.selection_by_rebalance["rebalance_date"].nunique() > len(result.backtest.weights)
    category_event_date = result.backtest.rebalance_events[
        result.backtest.rebalance_events["event_type"] == "category_change"
    ].index[0]
    assert result.backtest.weights.loc[category_event_date, "LATE_WINNER"] > 0.0


def test_category_confirmation_periods_waits_for_persistent_selection_before_trading():
    idx = pd.date_range("2020-01-31", periods=10, freq="ME")
    prices = pd.DataFrame(
        {
            "STABLE": [100, 106, 112, 119, 126, 133, 140, 147, 154, 161],
            "NOISY": [100, 94, 88, 120, 90, 130, 95, 140, 100, 150],
        },
        index=idx,
    )
    base_config = dict(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("preferred", {"cagr": 0.20})],
        strategy="equal_weight",
        train_size=3,
        test_size=3,
        step_size=3,
        periods_per_year=12,
        recategorization_policy="every_period",
    )

    immediate = run_research_pipeline(
        prices,
        volume=None,
        config=PipelineConfig(**base_config, category_confirmation_periods=1),
    )
    confirmed = run_research_pipeline(
        prices,
        volume=None,
        config=PipelineConfig(**base_config, category_confirmation_periods=2),
    )

    assert confirmed.backtest.rebalance_events["turnover"].sum() < immediate.backtest.rebalance_events[
        "turnover"
    ].sum()
    assert confirmed.backtest.rebalance_events["event_type"].tolist().count("category_change") < immediate.backtest.rebalance_events[
        "event_type"
    ].tolist().count("category_change")


def test_category_change_min_score_improvement_blocks_immaterial_recategorization():
    idx = pd.date_range("2020-01-31", periods=9, freq="ME")
    prices = pd.DataFrame(
        {
            "EARLY_WINNER": [100, 110, 121, 133, 120, 108, 97, 90, 85],
            "LATE_WINNER": [100, 95, 90, 86, 100, 116, 134, 155, 180],
        },
        index=idx,
    )
    base_config = dict(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("preferred", {"cagr": 0.20})],
        strategy="equal_weight",
        train_size=3,
        test_size=3,
        step_size=3,
        periods_per_year=12,
        recategorization_policy="every_period",
    )

    immediate = run_research_pipeline(
        prices,
        volume=None,
        config=PipelineConfig(**base_config, category_change_min_score_improvement=0.0),
    )
    material_only = run_research_pipeline(
        prices,
        volume=None,
        config=PipelineConfig(**base_config, category_change_min_score_improvement=1.1),
    )

    assert "category_change" in immediate.backtest.rebalance_events["event_type"].tolist()
    assert "category_change" not in material_only.backtest.rebalance_events["event_type"].tolist()
    assert material_only.backtest.rebalance_events["turnover"].sum() < immediate.backtest.rebalance_events[
        "turnover"
    ].sum()


def test_turnover_penalty_reduces_category_change_turnover():
    idx = pd.date_range("2020-01-31", periods=9, freq="ME")
    prices = pd.DataFrame(
        {
            "EARLY_WINNER": [100, 110, 121, 133, 120, 108, 97, 90, 85],
            "LATE_WINNER": [100, 95, 90, 86, 100, 116, 134, 155, 180],
        },
        index=idx,
    )
    base_config = dict(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("preferred", {"cagr": 0.20})],
        strategy="equal_weight",
        train_size=3,
        test_size=3,
        step_size=3,
        periods_per_year=12,
        recategorization_policy="every_period",
    )

    no_penalty = run_research_pipeline(
        prices,
        volume=None,
        config=PipelineConfig(**base_config, turnover_penalty=0.0),
    )
    penalized = run_research_pipeline(
        prices,
        volume=None,
        config=PipelineConfig(**base_config, turnover_penalty=0.75),
    )

    assert penalized.backtest.rebalance_events["turnover"].sum() < no_penalty.backtest.rebalance_events[
        "turnover"
    ].sum()
    assert "category_change" in penalized.backtest.rebalance_events["event_type"].tolist()


def test_pipeline_applies_category_exposure_cap_to_optimized_weights():
    idx = pd.date_range("2020-01-31", periods=8, freq="ME")
    prices = pd.DataFrame(
        {
            "CORN": [100, 105, 110, 116, 122, 128, 134, 141],
            "CANE": [100, 104, 109, 115, 121, 127, 133, 140],
            "SPY": [100, 103, 106, 109, 112, 115, 118, 121],
            "BND": [100, 101, 102, 103, 104, 105, 106, 107],
        },
        index=idx,
    )
    metadata = pd.DataFrame(
        {
            "ticker": ["CORN", "CANE", "SPY", "BND"],
            "name": ["Teucrium Corn Fund", "Teucrium Sugar Fund", "SPDR S&P 500 ETF", "Vanguard Total Bond Market ETF"],
        }
    )
    config = PipelineConfig(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("preferred", {"cagr": 0.01})],
        strategy="equal_weight",
        train_size=4,
        test_size=2,
        step_size=2,
        periods_per_year=12,
        asset_metadata=metadata,
        category_exposure_cap=0.35,
    )

    result = run_research_pipeline(prices, volume=None, config=config)

    first_weights = result.backtest.weights.iloc[0]
    assert first_weights[["CORN", "CANE"]].sum() <= 0.35 + 1e-12
    assert first_weights[["SPY", "BND"]].sum() >= 0.65 - 1e-12



def test_future_prices_do_not_change_first_walk_forward_electre_weights():
    idx = pd.date_range("2020-01-31", periods=12, freq="ME")
    base_prices = pd.DataFrame(
        {
            "TRAIN_WINNER": [100, 104, 108, 112, 116, 120, 121, 122, 123, 124, 125, 126],
            "FUTURE_WINNER": [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89],
        },
        index=idx,
    )
    future_changed_prices = base_prices.copy()
    future_changed_prices.loc[idx[6]:, "FUTURE_WINNER"] = [94, 130, 170, 220, 285, 370]

    config = PipelineConfig(
        criteria=[Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)],
        profiles=[Profile("acceptable", {"cagr": 0.05})],
        strategy="equal_weight",
        train_size=5,
        test_size=2,
        step_size=2,
        periods_per_year=12,
    )

    baseline = run_research_pipeline(base_prices, volume=None, config=config)
    with_future_spike = run_research_pipeline(future_changed_prices, volume=None, config=config)

    first_rebalance = baseline.backtest.weights.index[0]
    assert with_future_spike.backtest.weights.loc[first_rebalance].equals(
        baseline.backtest.weights.loc[first_rebalance]
    )
    assert baseline.backtest.weights.loc[first_rebalance, "FUTURE_WINNER"] == 0.0


def test_unsorted_price_index_cannot_leak_future_rows_into_first_electre_window():
    idx = pd.date_range("2020-01-31", periods=12, freq="ME")
    prices = pd.DataFrame(
        {
            "TRAIN_WINNER": [100, 104, 108, 112, 116, 120, 121, 122, 123, 124, 125, 126],
            "FUTURE_WINNER": [100, 99, 98, 97, 96, 95, 94, 130, 170, 220, 285, 370],
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

    sorted_result = run_research_pipeline(prices, volume=None, config=config)
    descending_input_result = run_research_pipeline(prices.iloc[::-1], volume=None, config=config)

    first_rebalance = sorted_result.backtest.weights.index[0]
    assert descending_input_result.backtest.weights.loc[first_rebalance].equals(
        sorted_result.backtest.weights.loc[first_rebalance]
    )
    assert sorted_result.backtest.weights.loc[first_rebalance, "FUTURE_WINNER"] == 0.0
