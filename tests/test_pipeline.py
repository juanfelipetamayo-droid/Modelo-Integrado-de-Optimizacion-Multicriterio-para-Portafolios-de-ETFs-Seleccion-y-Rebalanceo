from __future__ import annotations

import pandas as pd

from etf_optimizer.pipeline import PipelineConfig, run_research_pipeline
from etf_optimizer.selection.electre_tri import Criterion, Profile


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
