from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from etf_optimizer.backtesting.metrics import performance_summary

HIGHER_IS_BETTER = {"cagr", "sharpe", "sortino", "max_drawdown", "calmar"}
LOWER_IS_BETTER = {"volatility"}


def _clean_paired_returns(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    benchmark_name: str,
    min_observations: int,
) -> pd.DataFrame:
    paired = pd.concat(
        [
            pd.Series(strategy_returns, dtype="float64", name="strategy"),
            pd.Series(benchmark_returns, dtype="float64", name="benchmark"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    if len(paired) < min_observations:
        raise ValueError(
            f"benchmark {benchmark_name!r} must have at least {min_observations} overlapping observations; "
            f"found {len(paired)}"
        )
    return paired


def _metric_conclusion(metric: str, lower: float, upper: float) -> str:
    if metric in HIGHER_IS_BETTER:
        if lower > 0.0:
            return "strategy_positive"
        if upper < 0.0:
            return "strategy_negative"
        return "not_conclusive"
    if metric in LOWER_IS_BETTER:
        if upper < 0.0:
            return "strategy_positive"
        if lower > 0.0:
            return "strategy_negative"
        return "not_conclusive"
    return "not_conclusive"


def paired_benchmark_tests_table(
    strategy_returns: pd.Series,
    benchmark_returns: Mapping[str, pd.Series],
    *,
    n_bootstrap: int = 1_000,
    random_state: int | None = None,
    periods_per_year: int,
    risk_free_rate: float = 0.0,
    ci: float = 0.95,
    min_observations: int = 6,
) -> pd.DataFrame:
    """Bootstrap paired metric differences between a strategy and benchmarks.

    The bootstrap samples aligned return dates, preserving the paired structure of
    strategy and benchmark returns. Rows report strategy minus benchmark metric
    differences and a directional conclusion only when the confidence interval is
    entirely on the favorable side of zero.
    """
    if not benchmark_returns:
        raise ValueError("benchmark_returns must contain at least one benchmark")
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if min_observations <= 1:
        raise ValueError("min_observations must be greater than 1")
    if not 0.0 < ci < 1.0:
        raise ValueError("ci must be between 0 and 1")

    rng = np.random.default_rng(random_state)
    rows: list[dict[str, float | int | str]] = []
    lower_q = (1.0 - ci) / 2.0
    upper_q = 1.0 - lower_q

    for benchmark_name, returns in benchmark_returns.items():
        paired = _clean_paired_returns(
            strategy_returns,
            returns,
            benchmark_name=benchmark_name,
            min_observations=min_observations,
        )
        strategy_metrics = performance_summary(paired["strategy"], risk_free_rate, periods_per_year)
        benchmark_metrics = performance_summary(paired["benchmark"], risk_free_rate, periods_per_year)
        metric_names = list(strategy_metrics)
        boot_diffs = {metric: [] for metric in metric_names}
        values = paired[["strategy", "benchmark"]].to_numpy(dtype="float64")

        for _ in range(n_bootstrap):
            sample_idx = rng.integers(0, len(values), size=len(values))
            sample = pd.DataFrame(values[sample_idx], columns=["strategy", "benchmark"])
            sampled_strategy = performance_summary(sample["strategy"], risk_free_rate, periods_per_year)
            sampled_benchmark = performance_summary(sample["benchmark"], risk_free_rate, periods_per_year)
            for metric in metric_names:
                boot_diffs[metric].append(sampled_strategy[metric] - sampled_benchmark[metric])

        for metric in metric_names:
            diff = strategy_metrics[metric] - benchmark_metrics[metric]
            draws = np.asarray(boot_diffs[metric], dtype="float64")
            draws = draws[~np.isnan(draws)]
            ci_lower = float(np.quantile(draws, lower_q)) if len(draws) else np.nan
            ci_upper = float(np.quantile(draws, upper_q)) if len(draws) else np.nan
            rows.append(
                {
                    "benchmark": benchmark_name,
                    "metric": metric,
                    "strategy_value": float(strategy_metrics[metric]),
                    "benchmark_value": float(benchmark_metrics[metric]),
                    "difference": float(diff),
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "confidence_level": float(ci),
                    "n_observations": int(len(paired)),
                    "n_bootstrap": int(n_bootstrap),
                    "conclusion": _metric_conclusion(metric, ci_lower, ci_upper),
                }
            )

    return pd.DataFrame(rows)[
        [
            "benchmark",
            "metric",
            "strategy_value",
            "benchmark_value",
            "difference",
            "ci_lower",
            "ci_upper",
            "confidence_level",
            "n_observations",
            "n_bootstrap",
            "conclusion",
        ]
    ]
