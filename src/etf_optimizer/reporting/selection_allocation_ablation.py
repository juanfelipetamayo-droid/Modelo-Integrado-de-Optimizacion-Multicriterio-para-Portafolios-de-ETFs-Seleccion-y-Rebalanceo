from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal

import numpy as np
import pandas as pd

from etf_optimizer.backtesting.engine import BacktestConfig, BacktestResult, WalkForwardBacktester
from etf_optimizer.optimization.portfolio import equal_weight, ledoit_wolf_covariance, max_sharpe_weights, min_variance_weights
from etf_optimizer.pipeline import _select_assets
from etf_optimizer.reporting.classification_diagnostics import default_electre_criteria, default_electre_profiles
from etf_optimizer.reporting.tables import build_drawdowns, build_equity_curves, build_strategy_comparison
from etf_optimizer.selection.electre_tri import AssignmentMode, ElectreTri

AllocationName = Literal["equal_weight", "inverse_vol", "min_variance", "max_sharpe"]
SelectionName = Literal["universe", "electre"]


@dataclass(frozen=True)
class AblationResult:
    strategy_returns: dict[str, pd.Series]
    backtests: dict[str, BacktestResult]
    strategy_comparison: pd.DataFrame
    equity_curves: pd.DataFrame
    drawdowns: pd.DataFrame
    ablation_grid: pd.DataFrame


def _fold_id(path: Path) -> int:
    match = re.search(r"fold_(\d+)_", path.name)
    if not match:
        raise ValueError(f"cannot parse fold id from {path}")
    return int(match.group(1))


def _fold_dirs(stage_artifacts_dir: Path) -> list[Path]:
    return sorted([path for path in stage_artifacts_dir.glob("fold_*_*") if path.is_dir()], key=_fold_id)


def _load_fold_maps(results_dir: Path) -> tuple[dict[pd.Timestamp, list[str]], dict[pd.Timestamp, pd.DataFrame]]:
    universe_by_date: dict[pd.Timestamp, list[str]] = {}
    criteria_by_date: dict[pd.Timestamp, pd.DataFrame] = {}
    for fold_dir in _fold_dirs(results_dir / "fold_stage_artifacts"):
        universe = pd.read_csv(fold_dir / "universe_snapshot.csv")
        criteria = pd.read_csv(fold_dir / "criteria_matrix.csv").set_index("ticker")
        assignments = pd.read_csv(fold_dir / "electre_assignments.csv")
        if assignments.empty:
            continue
        # The rebalance date is stored in each fold diagnostic file and matches the
        # first OOS return date used by WalkForwardBacktester.
        diag = pd.read_csv(fold_dir / "classification_diagnostics.csv")
        rebalance_date = pd.Timestamp(diag.loc[0, "rebalance_date"])
        tickers = universe["ticker"].dropna().astype(str).tolist() if "ticker" in universe.columns else criteria.index.astype(str).tolist()
        universe_by_date[rebalance_date] = tickers
        criteria_by_date[rebalance_date] = criteria
    return universe_by_date, criteria_by_date


def _inverse_vol_weights(train_returns: pd.DataFrame) -> pd.Series:
    vol = train_returns.std(ddof=1).replace(0.0, np.nan)
    inv = 1.0 / vol
    inv = inv.replace([np.inf, -np.inf], np.nan).dropna()
    if inv.empty:
        return equal_weight(train_returns.columns)
    return inv / inv.sum()


def _allocate(train_returns: pd.DataFrame, allocation: AllocationName, *, periods_per_year: int = 12, max_weight: float | None = 0.25) -> pd.Series:
    clean = train_returns.dropna(axis=0, how="any")
    if clean.shape[1] == 0:
        raise ValueError("no assets available for allocation")
    if allocation == "equal_weight":
        return equal_weight(clean.columns)
    if allocation == "inverse_vol":
        return _inverse_vol_weights(clean)
    cov = ledoit_wolf_covariance(clean) if clean.shape[0] > 1 else clean.cov()
    if allocation == "min_variance":
        try:
            return min_variance_weights(cov, max_weight=max_weight)
        except Exception:
            return equal_weight(clean.columns)
    if allocation == "max_sharpe":
        expected = clean.mean() * periods_per_year
        try:
            return max_sharpe_weights(expected, cov, risk_free_rate=0.0, max_weight=max_weight)
        except Exception:
            try:
                return min_variance_weights(cov, max_weight=max_weight)
            except Exception:
                return equal_weight(clean.columns)
    raise ValueError(f"unknown allocation: {allocation}")


def _strategy_name(
    selection: SelectionName,
    allocation: AllocationName,
    *,
    assignment: AssignmentMode | None = None,
    use_veto: bool | None = None,
) -> str:
    allocation_label = {
        "equal_weight": "EqualWeight",
        "inverse_vol": "InverseVol",
        "min_variance": "MinVariance",
        "max_sharpe": "MaxSharpe",
    }[allocation]
    if selection == "universe":
        return f"Universe_{allocation_label}_walk_forward"
    veto_label = "with_veto" if use_veto else "no_veto"
    return f"ELECTRE_{assignment}_{veto_label}_{allocation_label}_walk_forward"


def run_selection_allocation_ablation(
    prices_path: Path,
    baseline_results_dir: Path,
    *,
    train_size: int = 36,
    test_size: int = 3,
    step_size: int = 3,
    cost_bps: float = 10.0,
    periods_per_year: int = 12,
    weight_drift: Literal["constant_mix", "buy_and_hold"] = "buy_and_hold",
    rebalance_policy: Literal["calendar", "threshold"] = "calendar",
    drift_tolerance: float = 0.05,
    max_weight: float | None = 0.25,
) -> AblationResult:
    prices = pd.read_parquet(prices_path).sort_index()
    prices.index = pd.to_datetime(prices.index)
    prices = prices.resample("ME").last()
    returns = prices.pct_change(fill_method=None).dropna(how="all")
    universe_by_date, criteria_by_date = _load_fold_maps(baseline_results_dir)
    criteria = default_electre_criteria()
    profiles = default_electre_profiles()
    returns_index = returns.index
    config = BacktestConfig(
        train_size=train_size,
        test_size=test_size,
        step_size=step_size,
        cost_bps=cost_bps,
        weight_drift=weight_drift,
        rebalance_policy=rebalance_policy,
        drift_tolerance=drift_tolerance,
    )
    backtester = WalkForwardBacktester(config)

    def make_strategy(
        selection: SelectionName,
        allocation: AllocationName,
        *,
        assignment: AssignmentMode = "pessimistic",
        use_veto: bool = False,
    ):
        def strategy(train_returns: pd.DataFrame) -> pd.Series:
            future_return_dates = returns_index[returns_index > train_returns.index[-1]]
            if future_return_dates.empty:
                raise ValueError("cannot infer rebalance date after training window")
            rebalance_date = pd.Timestamp(future_return_dates[0])
            if rebalance_date not in universe_by_date:
                raise ValueError(f"missing fold universe for rebalance date {rebalance_date.date()}")
            candidate_tickers = [ticker for ticker in universe_by_date[rebalance_date] if ticker in train_returns.columns]
            if selection == "electre":
                matrix = criteria_by_date[rebalance_date]
                matrix = matrix.loc[[ticker for ticker in matrix.index.astype(str) if ticker in candidate_tickers]]
                model = ElectreTri(criteria, profiles, lambda_cut=0.75, assignment=assignment, use_veto=use_veto)
                selected = _select_assets(model.assign(matrix))
                candidate_tickers = [ticker for ticker in selected if ticker in train_returns.columns]
            if not candidate_tickers:
                raise ValueError(f"no assets selected for {selection} at {rebalance_date.date()}")
            train_subset = train_returns[candidate_tickers].dropna(axis=0, how="any")
            if train_subset.shape[1] == 0 or train_subset.empty:
                raise ValueError(f"no complete training rows for {selection} at {rebalance_date.date()}")
            return _allocate(train_subset, allocation, periods_per_year=periods_per_year, max_weight=max_weight)

        return strategy

    strategy_returns: dict[str, pd.Series] = {}
    backtests: dict[str, BacktestResult] = {}
    rows: list[dict[str, object]] = []

    for allocation in ["equal_weight", "min_variance", "max_sharpe"]:
        name = _strategy_name("universe", allocation)  # type: ignore[arg-type]
        backtest = backtester.run(returns, make_strategy("universe", allocation))  # type: ignore[arg-type]
        strategy_returns[name] = backtest.portfolio_returns
        backtests[name] = backtest
        rows.append({"strategy": name, "selection": "universe", "allocation": allocation, "assignment": "none", "use_veto": False})

    for assignment in ["pessimistic", "optimistic"]:
        for use_veto in [False, True]:
            for allocation in ["equal_weight", "inverse_vol", "min_variance", "max_sharpe"]:
                name = _strategy_name("electre", allocation, assignment=assignment, use_veto=use_veto)  # type: ignore[arg-type]
                backtest = backtester.run(
                    returns,
                    make_strategy("electre", allocation, assignment=assignment, use_veto=use_veto),  # type: ignore[arg-type]
                )
                strategy_returns[name] = backtest.portfolio_returns
                backtests[name] = backtest
                rows.append(
                    {
                        "strategy": name,
                        "selection": "electre",
                        "allocation": allocation,
                        "assignment": assignment,
                        "use_veto": use_veto,
                    }
                )

    comparison = build_strategy_comparison(strategy_returns, periods_per_year=periods_per_year)
    equity = build_equity_curves(strategy_returns)
    drawdowns = build_drawdowns(strategy_returns)
    grid = pd.DataFrame(rows).merge(comparison.reset_index(), on="strategy", how="left")
    turnover_rows = []
    for strategy_name, backtest in backtests.items():
        turnover_rows.append(
            {
                "strategy": strategy_name,
                "avg_turnover": float(backtest.turnover.mean()) if not backtest.turnover.empty else np.nan,
                "total_turnover": float(backtest.turnover.sum()) if not backtest.turnover.empty else np.nan,
                "rebalance_events": int(backtest.rebalance_events.shape[0]),
            }
        )
    grid = grid.merge(pd.DataFrame(turnover_rows), on="strategy", how="left")
    return AblationResult(strategy_returns, backtests, comparison, equity, drawdowns, grid)


def write_selection_allocation_ablation(result: AblationResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.strategy_comparison.to_csv(output_dir / "strategy_comparison.csv")
    result.ablation_grid.to_csv(output_dir / "ablation_grid.csv", index=False)
    result.equity_curves.to_csv(output_dir / "equity_curves.csv")
    result.drawdowns.to_csv(output_dir / "drawdowns.csv")
    pd.DataFrame(result.strategy_returns).to_csv(output_dir / "strategy_returns.csv")
    turnover_rows = []
    for strategy, backtest in result.backtests.items():
        turnover_rows.append(
            {
                "strategy": strategy,
                "avg_turnover": float(backtest.turnover.mean()) if not backtest.turnover.empty else np.nan,
                "total_turnover": float(backtest.turnover.sum()) if not backtest.turnover.empty else np.nan,
                "rebalance_events": int(backtest.rebalance_events.shape[0]),
            }
        )
    pd.DataFrame(turnover_rows).to_csv(output_dir / "turnover_summary.csv", index=False)
