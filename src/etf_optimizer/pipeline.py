from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from etf_optimizer.backtesting.engine import BacktestConfig, BacktestResult, WalkForwardBacktester
from etf_optimizer.backtesting.metrics import performance_summary
from etf_optimizer.features import compute_feature_table, returns_from_prices
from etf_optimizer.optimization.portfolio import (
    equal_weight,
    ledoit_wolf_covariance,
    max_sharpe_weights,
    min_variance_weights,
    sample_covariance,
)
from etf_optimizer.selection.electre_tri import Criterion, ElectreTri, Profile

StrategyName = Literal["equal_weight", "min_variance", "max_sharpe"]


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for the research MVP pipeline."""

    criteria: list[Criterion]
    profiles: list[Profile]
    lambda_cut: float = 0.75
    strategy: StrategyName = "max_sharpe"
    covariance: Literal["sample", "ledoit_wolf"] = "ledoit_wolf"
    train_size: int = 36
    test_size: int = 12
    step_size: int = 12
    cost_bps: float = 10.0
    periods_per_year: int = 12
    risk_free_rate: float = 0.0
    max_weight: float | None = 0.25


@dataclass(frozen=True)
class PipelineResult:
    features: pd.DataFrame
    selection: pd.DataFrame
    selected_assets: list[str]
    backtest: BacktestResult
    summary: pd.DataFrame


def _select_assets(selection: pd.DataFrame) -> list[str]:
    selected = [idx for idx, row in selection.iterrows() if str(row["category"]).startswith("above_")]
    if not selected:
        # Fallback: keep the highest-credibility assets so the research pipeline remains runnable.
        credibility_cols = [col for col in selection.columns if col.startswith("credibility_")]
        if not credibility_cols:
            raise ValueError("selection output has no credibility columns")
        selected = selection[credibility_cols].max(axis=1).sort_values(ascending=False).head(5).index.tolist()
    return selected


def _make_strategy(config: PipelineConfig, selected_assets: list[str]):
    def strategy(train_returns: pd.DataFrame) -> pd.Series:
        train = train_returns[selected_assets].dropna(axis=1, how="all").fillna(0.0)
        if train.shape[1] == 0:
            raise ValueError("no selected assets available in training window")
        if config.strategy == "equal_weight":
            return equal_weight(train.columns)
        cov = (
            ledoit_wolf_covariance(train, config.periods_per_year)
            if config.covariance == "ledoit_wolf" and len(train) > train.shape[1]
            else sample_covariance(train, config.periods_per_year)
        )
        if config.strategy == "min_variance":
            return min_variance_weights(cov, max_weight=config.max_weight)
        expected_returns = train.mean() * config.periods_per_year
        return max_sharpe_weights(
            expected_returns,
            cov,
            risk_free_rate=config.risk_free_rate,
            max_weight=config.max_weight,
        )

    return strategy


def run_research_pipeline(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    config: PipelineConfig,
) -> PipelineResult:
    """Run the thesis MVP: features → ELECTRE Tri → optimization → walk-forward test.

    This is intentionally transparent rather than overly automated. Researchers can
    inspect each intermediate output and report the methodology in a thesis appendix.
    """
    features = compute_feature_table(
        prices,
        volume=volume,
        risk_free_rate=config.risk_free_rate,
        periods_per_year=config.periods_per_year,
    ).dropna(subset=[criterion.name for criterion in config.criteria if criterion.name in features_columns(config.criteria)])
    model = ElectreTri(config.criteria, config.profiles, config.lambda_cut)
    selection = model.assign(features[[criterion.name for criterion in config.criteria]])
    selected_assets = _select_assets(selection)
    returns = returns_from_prices(prices[selected_assets]).dropna(how="all")
    backtester = WalkForwardBacktester(
        BacktestConfig(
            train_size=config.train_size,
            test_size=config.test_size,
            step_size=config.step_size,
            cost_bps=config.cost_bps,
        )
    )
    backtest = backtester.run(returns, _make_strategy(config, selected_assets))
    summary = pd.DataFrame(
        {
            "strategy": performance_summary(
                backtest.portfolio_returns,
                risk_free_rate=config.risk_free_rate,
                periods_per_year=config.periods_per_year,
            )
        }
    ).T
    summary["avg_turnover"] = float(backtest.turnover.mean())
    summary["selected_assets"] = len(selected_assets)
    return PipelineResult(features, selection, selected_assets, backtest, summary)


def features_columns(criteria: list[Criterion]) -> list[str]:
    return [criterion.name for criterion in criteria]
