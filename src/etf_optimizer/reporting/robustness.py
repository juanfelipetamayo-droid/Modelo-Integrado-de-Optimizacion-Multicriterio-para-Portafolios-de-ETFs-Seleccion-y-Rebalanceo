from __future__ import annotations

from collections.abc import Iterable, Mapping

import numpy as np
import pandas as pd

from etf_optimizer.backtesting.metrics import performance_summary
from etf_optimizer.selection.electre_tri import Criterion, ElectreTri, Profile


def _cost_impact(turnover: pd.Series, cost_bps: float) -> pd.Series:
    return pd.Series(turnover, dtype="float64") * (float(cost_bps) / 10_000.0)


def reprice_returns_for_cost(
    net_returns: pd.Series,
    turnover: pd.Series,
    *,
    base_cost_bps: float,
    target_cost_bps: float,
) -> pd.Series:
    """Reprice a net walk-forward return series under a different transaction-cost level.

    The backtester subtracts transaction costs on rebalance dates only. This helper
    first reconstructs the gross return at each rebalance date from the observed
    net series and base cost, then applies the target cost. Non-rebalance periods
    are unchanged. It is intended for controlled sensitivity analysis, not as a
    substitute for re-optimizing strategies under different cost assumptions.
    """
    repriced = pd.Series(net_returns, dtype="float64").copy()
    aligned_turnover = pd.Series(turnover, dtype="float64").reindex(repriced.index, fill_value=0.0)
    repriced = repriced + _cost_impact(aligned_turnover, base_cost_bps)
    repriced = repriced - _cost_impact(aligned_turnover, target_cost_bps)
    repriced.name = net_returns.name
    return repriced


def _validate_cost_inputs(
    turnover: pd.Series,
    *,
    base_cost_bps: float,
    cost_bps_grid: Iterable[float],
    periods_per_year: int,
) -> list[float]:
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if base_cost_bps < 0.0 or not np.isfinite(base_cost_bps):
        raise ValueError("base_cost_bps must be finite and nonnegative")
    turnover_series = pd.Series(turnover, dtype="float64")
    if (turnover_series < 0.0).any():
        raise ValueError("turnover values must be nonnegative")
    costs = [float(cost) for cost in cost_bps_grid]
    if not costs:
        raise ValueError("cost_bps_grid must contain at least one value")
    if any(cost < 0.0 or not np.isfinite(cost) for cost in costs):
        raise ValueError("cost_bps_grid values must be finite and nonnegative")
    return costs


def cost_sensitivity_table(
    net_returns: pd.Series,
    turnover: pd.Series,
    *,
    base_cost_bps: float,
    cost_bps_grid: Iterable[float],
    periods_per_year: int,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """Summarize portfolio performance under a grid of transaction-cost assumptions."""
    rows: list[dict[str, float]] = []
    costs = _validate_cost_inputs(
        turnover,
        base_cost_bps=base_cost_bps,
        cost_bps_grid=cost_bps_grid,
        periods_per_year=periods_per_year,
    )
    for cost_bps in costs:
        repriced = reprice_returns_for_cost(
            net_returns,
            turnover,
            base_cost_bps=base_cost_bps,
            target_cost_bps=float(cost_bps),
        )
        metrics = performance_summary(repriced, risk_free_rate, periods_per_year)
        metrics.update(
            {
                "cost_bps": float(cost_bps),
                "total_return": float((1.0 + repriced.dropna()).prod() - 1.0),
                "mean_rebalance_turnover": float(pd.Series(turnover, dtype="float64").mean()),
                "mean_rebalance_cost": float(_cost_impact(pd.Series(turnover, dtype="float64"), float(cost_bps)).mean()),
            }
        )
        rows.append(metrics)
    columns = [
        "cost_bps",
        "total_return",
        "cagr",
        "volatility",
        "sharpe",
        "sortino",
        "max_drawdown",
        "calmar",
        "mean_rebalance_turnover",
        "mean_rebalance_cost",
    ]
    return pd.DataFrame(rows)[columns]


def _bootstrap_indices(length: int, rng: np.random.Generator, *, block_length: int | None) -> np.ndarray:
    if block_length is None or block_length <= 1:
        return rng.integers(0, length, size=length)
    starts = rng.integers(0, length, size=int(np.ceil(length / block_length)))
    sampled: list[int] = []
    for start in starts:
        sampled.extend((int(start) + offset) % length for offset in range(block_length))
        if len(sampled) >= length:
            break
    return np.asarray(sampled[:length], dtype=int)


def bootstrap_metric_intervals(
    returns: pd.Series,
    *,
    n_bootstrap: int = 1_000,
    random_state: int | None = None,
    periods_per_year: int,
    risk_free_rate: float = 0.0,
    ci: float = 0.95,
    block_length: int | None = None,
) -> pd.DataFrame:
    """Estimate non-parametric bootstrap confidence intervals for performance metrics.

    Set ``block_length`` for moving-block bootstrap on monthly returns. This preserves
    short-run dependence better than iid resampling while remaining deterministic for
    a fixed random seed.
    """
    clean = pd.Series(returns, dtype="float64").dropna()
    if clean.empty:
        raise ValueError("returns must contain at least one non-null observation")
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if block_length is not None and block_length <= 0:
        raise ValueError("block_length must be positive when provided")
    if not 0.0 < ci < 1.0:
        raise ValueError("ci must be between 0 and 1")

    rng = np.random.default_rng(random_state)
    estimates = performance_summary(clean, risk_free_rate, periods_per_year)
    metric_names = list(estimates)
    draws = {metric: [] for metric in metric_names}
    values = clean.to_numpy()
    for _ in range(n_bootstrap):
        sample_idx = _bootstrap_indices(len(values), rng, block_length=block_length)
        sample = pd.Series(values[sample_idx])
        metrics = performance_summary(sample, risk_free_rate, periods_per_year)
        for metric in metric_names:
            draws[metric].append(metrics[metric])

    lower_q = (1.0 - ci) / 2.0
    upper_q = 1.0 - lower_q
    rows: list[dict[str, float | str | int]] = []
    for metric in metric_names:
        arr = np.asarray(draws[metric], dtype="float64")
        arr = arr[~np.isnan(arr)]
        ci_lower = float(np.quantile(arr, lower_q)) if len(arr) else np.nan
        ci_upper = float(np.quantile(arr, upper_q)) if len(arr) else np.nan
        rows.append(
            {
                "metric": metric,
                "estimate": estimates[metric],
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "confidence_interval": f"[{ci_lower:.6f}, {ci_upper:.6f}]" if np.isfinite(ci_lower) and np.isfinite(ci_upper) else "",
                "confidence_level": ci,
                "n_bootstrap": n_bootstrap,
                "block_length": int(block_length or 1),
            }
        )
    return pd.DataFrame(rows)


def _scaled_criteria(criteria: list[Criterion], multipliers: Mapping[str, float]) -> list[Criterion]:
    scaled_weights = {criterion.name: criterion.weight * float(multipliers.get(criterion.name, 1.0)) for criterion in criteria}
    total = sum(scaled_weights.values())
    if total <= 0.0:
        raise ValueError("scaled ELECTRE criteria weights must sum to a positive value")
    return [
        Criterion(
            criterion.name,
            weight=scaled_weights[criterion.name] / total,
            preference_direction=criterion.preference_direction,
            q=criterion.q,
            p=criterion.p,
            v=criterion.v,
        )
        for criterion in criteria
    ]


def electre_sensitivity_table(
    features: pd.DataFrame,
    criteria: list[Criterion],
    profiles: list[Profile],
    *,
    lambda_values: Iterable[float],
    weight_multipliers: Iterable[Mapping[str, float]],
) -> pd.DataFrame:
    """Run ELECTRE Tri across lambda/weight cases and record selection stability."""
    rows: list[pd.DataFrame] = []
    feature_columns = [criterion.name for criterion in criteria]
    clean_features = features.dropna(subset=feature_columns)
    case_number = 0
    for lambda_cut in lambda_values:
        for multipliers in weight_multipliers:
            case_number += 1
            case_id = f"lambda={float(lambda_cut):.3f};weights={case_number}"
            case_criteria = _scaled_criteria(criteria, multipliers)
            selection = ElectreTri(case_criteria, profiles, lambda_cut=float(lambda_cut)).assign(clean_features[feature_columns])
            selected = selection["category"].astype(str).str.startswith("above_")
            case = selection[["category"]].copy()
            case["ticker"] = case.index
            case["selected"] = selected
            case["lambda_cut"] = float(lambda_cut)
            case["case_id"] = case_id
            case["weight_multipliers"] = ",".join(f"{k}={v}" for k, v in sorted(multipliers.items())) or "baseline"
            rows.append(case.reset_index(drop=True))
    if not rows:
        return pd.DataFrame(columns=["case_id", "lambda_cut", "weight_multipliers", "ticker", "selected", "category"])
    return pd.concat(rows, ignore_index=True)[
        ["case_id", "lambda_cut", "weight_multipliers", "ticker", "selected", "category"]
    ]
