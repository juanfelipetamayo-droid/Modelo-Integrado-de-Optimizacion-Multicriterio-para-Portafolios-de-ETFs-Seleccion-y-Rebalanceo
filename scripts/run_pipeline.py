from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from etf_optimizer.pipeline import PipelineConfig, run_research_pipeline
from etf_optimizer.selection.electre_tri import Criterion, Profile


def default_config() -> PipelineConfig:
    # Conservative starting profile; calibrate these thresholds in the thesis sensitivity analysis.
    criteria = [
        Criterion("cagr", 0.30, "max", q=0.01, p=0.03, v=0.08),
        Criterion("sharpe", 0.30, "max", q=0.10, p=0.30, v=0.70),
        Criterion("volatility", 0.20, "min", q=0.02, p=0.05, v=0.15),
        Criterion("max_drawdown", 0.20, "min", q=0.03, p=0.08, v=0.20),
    ]
    profiles = [Profile("acceptable", {"cagr": 0.05, "sharpe": 0.4, "volatility": 0.35, "max_drawdown": -0.35})]
    return PipelineConfig(criteria=criteria, profiles=profiles)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ETF research MVP pipeline from parquet price data.")
    parser.add_argument("--prices", type=Path, required=True, help="Parquet file with adjusted close prices")
    parser.add_argument("--volume", type=Path, default=None, help="Optional parquet file with volumes")
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()

    prices = pd.read_parquet(args.prices)
    volume = pd.read_parquet(args.volume) if args.volume else None
    result = run_research_pipeline(prices, volume, default_config())

    args.out.mkdir(parents=True, exist_ok=True)
    result.features.to_csv(args.out / "features.csv")
    result.selection.to_csv(args.out / "electre_selection.csv")
    result.backtest.portfolio_returns.to_csv(args.out / "portfolio_returns.csv", header=["return"])
    result.backtest.weights.to_csv(args.out / "weights.csv")
    result.summary.to_csv(args.out / "summary.csv")
    print(result.summary)
    print("Selected assets:", ", ".join(result.selected_assets))


if __name__ == "__main__":
    main()
