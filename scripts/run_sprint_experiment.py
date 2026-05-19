from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from etf_optimizer.backtesting.benchmarks import (
    benchmark_spy,
    benchmark_60_40,
    benchmark_equal_weight,
    benchmark_min_variance,
    benchmark_max_sharpe,
)
from etf_optimizer.data.fetcher import compute_price_coverage
from etf_optimizer.features import returns_from_prices
from etf_optimizer.pipeline import PipelineConfig, run_research_pipeline
from etf_optimizer.reporting.tables import (
    build_strategy_comparison,
    build_equity_curves,
    build_drawdowns,
    write_comparison_tables,
)
from etf_optimizer.reporting.plots import plot_equity_curves, coverage_plot_summary
from etf_optimizer.selection.electre_tri import Criterion, Profile

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sprint experiment: broad universe backtest.")
    parser.add_argument("--universe", type=Path, required=True, help="Path to universe CSV")
    parser.add_argument("--prices", type=Path, default=None, help="Path to prices parquet (close)")
    parser.add_argument("--volume", type=Path, default=None, help="Path to volume parquet")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--rebalance", choices=["monthly", "quarterly", "annual"], default="annual")
    parser.add_argument("--cost-bps", type=float, default=10.0, help="Transaction cost in bps")
    parser.add_argument("--out", type=Path, default=Path("results/sprint_universe_v0"))
    args = parser.parse_args()

    rebalance_map = {"monthly": 1, "quarterly": 3, "annual": 12}
    test_size = rebalance_map[args.rebalance]

    universe = pd.read_csv(args.universe)
    logger.info("Universe loaded: %d funds", len(universe))

    if args.prices:
        prices = pd.read_parquet(args.prices).loc[args.start : args.end].resample("ME").last()
        volume = pd.read_parquet(args.volume).loc[args.start : args.end].resample("ME").sum() if args.volume else None

        rets = returns_from_prices(prices)
        universe_tickers = set(universe["ticker"].dropna().str.upper().unique())
        available_tickers = [t for t in rets.columns if t in universe_tickers]
        rets = rets[available_tickers]

        coverage = compute_price_coverage(list(universe_tickers), prices, args.start, args.end)
        logger.info("Price coverage:\n%s", coverage.to_string(index=False))
    else:
        idx = pd.date_range(args.start, args.end, freq="ME")
        repeats = (len(idx) // 4) + 1
        synthetic_rets = pd.DataFrame(
            {
                "SPY": ([0.008, -0.004, 0.012, 0.006] * repeats)[: len(idx)],
                "BND": ([0.002, 0.001, -0.001, 0.003] * repeats)[: len(idx)],
                "QQQ": ([0.012, -0.008, 0.018, 0.004] * repeats)[: len(idx)],
                "IWM": ([0.006, -0.006, 0.010, 0.005] * repeats)[: len(idx)],
                "TLT": ([0.004, 0.006, -0.004, 0.002] * repeats)[: len(idx)],
            },
            index=idx,
        )
        prices = (1.0 + synthetic_rets).cumprod() * 100.0
        volume = pd.DataFrame(1_000_000, index=idx, columns=prices.columns)
        rets = returns_from_prices(prices)
        available_tickers = list(rets.columns)
        coverage = pd.DataFrame()
        logger.info("No price file provided; using synthetic prices for structural test.")

    logger.info("Eligible universe: %d tickers with price data", len(available_tickers))

    criteria = [
        Criterion("cagr", weight=0.35, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("volatility", weight=0.25, preference_direction="min", q=0.0, p=0.02, v=0.10),
        Criterion("sharpe", weight=0.25, preference_direction="max", q=0.0, p=0.10, v=0.30),
        Criterion("sortino", weight=0.15, preference_direction="max", q=0.0, p=0.10, v=0.30),
    ]
    profiles = [
        Profile("acceptable", {"cagr": 0.03, "volatility": 0.25, "sharpe": 0.3, "sortino": 0.4}),
    ]

    train_months = 36
    pipe_config = PipelineConfig(
        criteria=criteria,
        profiles=profiles,
        strategy="max_sharpe",
        train_size=train_months,
        test_size=test_size,
        step_size=test_size,
        cost_bps=args.cost_bps,
        periods_per_year=12,
    )

    pipe_result = run_research_pipeline(
        prices,
        volume,
        pipe_config,
    )
    logger.info("ELECTRE selected %d assets", len(pipe_result.selected_assets))

    strategy_returns: dict[str, pd.Series] = {
        "ELECTRE_MaxSharpe": pipe_result.backtest.portfolio_returns,
    }

    if "SPY" in rets.columns:
        strategy_returns["SPY"] = benchmark_spy(rets)
    if all(t in rets.columns for t in ["SPY", "BND"]):
        strategy_returns["60/40_SPY_BND"] = benchmark_60_40(rets)
    if len(available_tickers) >= 3:
        strategy_returns["EqualWeight"] = benchmark_equal_weight(rets[available_tickers])
        strategy_returns["MinVariance"] = benchmark_min_variance(rets[available_tickers], periods_per_year=12)
        strategy_returns["MaxSharpe"] = benchmark_max_sharpe(rets[available_tickers], periods_per_year=12)

    comparison = build_strategy_comparison(strategy_returns, periods_per_year=12)
    equity = build_equity_curves(strategy_returns)
    drawdowns = build_drawdowns(strategy_returns)

    paths = write_comparison_tables(comparison, equity, drawdowns, args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    pipe_result.features.to_csv(args.out / "features_table.csv")
    pipe_result.selection.to_csv(args.out / "electre_selection.csv")
    pipe_result.backtest.weights.to_csv(args.out / "electre_weights.csv")
    if not coverage.empty:
        coverage.to_csv(args.out / "coverage_report.csv", index=False)
    logger.info("Results written to %s", args.out)

    for name, p in paths.items():
        logger.info("  %s: %s", name, p)

    summary_text = plot_equity_curves(equity, "Sprint Universe v0 — Equity Curves")
    logger.info("Equity curve summary:\n%s", summary_text)

    if not coverage.empty:
        cov_summary = coverage_plot_summary(coverage)
        logger.info("Coverage summary:\n%s", cov_summary)


if __name__ == "__main__":
    main()
