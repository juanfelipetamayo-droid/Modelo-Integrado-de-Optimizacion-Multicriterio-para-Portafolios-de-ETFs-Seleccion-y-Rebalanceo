from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pandas as pd

from etf_optimizer.selection.electre_tri import Criterion, ElectreTri, Profile

CATEGORY_ORDER = {
    "below_minimum": 0,
    "between_minimum_preferred": 1,
    "above_preferred": 2,
}


@dataclass(frozen=True)
class ClassificationDiagnosticArtifacts:
    classification_effectiveness: pd.DataFrame
    category_forward_returns: pd.DataFrame
    category_forward_sharpe: pd.DataFrame
    category_forward_drawdown: pd.DataFrame
    pessimistic_optimistic_divergence: pd.DataFrame
    category_transition_matrix: pd.DataFrame
    selection_jaccard_by_fold: pd.DataFrame


def default_electre_criteria() -> list[Criterion]:
    """Return the ELECTRE criteria used by scripts/run_sprint_experiment.py."""
    return [
        Criterion("cagr", weight=0.35, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("volatility", weight=0.25, preference_direction="min", q=0.0, p=0.02, v=0.10),
        Criterion("sharpe", weight=0.25, preference_direction="max", q=0.0, p=0.10, v=0.30),
        Criterion("sortino", weight=0.15, preference_direction="max", q=0.0, p=0.10, v=0.30),
    ]


def default_electre_profiles() -> list[Profile]:
    """Return the ELECTRE profiles used by scripts/run_sprint_experiment.py."""
    return [
        Profile("minimum", {"cagr": 0.03, "volatility": 0.25, "sharpe": 0.3, "sortino": 0.4}),
        Profile("preferred", {"cagr": 0.10, "volatility": 0.18, "sharpe": 0.8, "sortino": 1.0}),
    ]


def category_rank(category: str) -> int:
    return CATEGORY_ORDER.get(str(category), -1)


def is_selected(category: str) -> bool:
    return str(category).startswith("above_")


def annualized_cumulative_return(returns: pd.Series, periods_per_year: int = 12) -> float:
    clean = returns.dropna()
    if clean.empty:
        return np.nan
    cumulative = float((1.0 + clean).prod() - 1.0)
    return float((1.0 + cumulative) ** (periods_per_year / len(clean)) - 1.0)


def annualized_sharpe(returns: pd.Series, periods_per_year: int = 12) -> float:
    clean = returns.dropna()
    if clean.empty:
        return np.nan
    std = float(clean.std(ddof=1))
    if np.isclose(std, 0.0) or np.isnan(std):
        return np.nan
    return float(clean.mean() / std * np.sqrt(periods_per_year))


def max_drawdown_from_returns(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return np.nan
    equity = (1.0 + clean).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    return float(drawdown.min())


def _fold_id(path: Path) -> int:
    match = re.search(r"fold_(\d+)_", path.name)
    if not match:
        raise ValueError(f"cannot parse fold id from {path}")
    return int(match.group(1))


def _fold_dirs(stage_artifacts_dir: Path) -> list[Path]:
    return sorted(
        [path for path in stage_artifacts_dir.glob("fold_*_*") if path.is_dir()],
        key=_fold_id,
    )


def _fold_periods(results_dir: Path) -> pd.DataFrame:
    perf = pd.read_csv(results_dir / "fold_performance.csv")
    base = perf[perf["strategy"].astype(str).eq("ELECTRE_MaxSharpe_walk_forward")].copy()
    if base.empty:
        base = perf.drop_duplicates("fold").copy()
    base["start_date"] = pd.to_datetime(base["start_date"])
    base["end_date"] = pd.to_datetime(base["end_date"])
    return base[["fold", "start_date", "end_date", "n_observations"]].drop_duplicates("fold")


def _variant_assignments(
    criteria_matrix: pd.DataFrame,
    criteria: list[Criterion],
    profiles: list[Profile],
    lambda_cut: float,
) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for assignment in ["pessimistic", "optimistic"]:
        for use_veto in [False, True]:
            key = f"{assignment}_{'with_veto' if use_veto else 'no_veto'}"
            model = ElectreTri(
                criteria,
                profiles,
                lambda_cut=lambda_cut,
                assignment=assignment,  # type: ignore[arg-type]
                use_veto=use_veto,
                backend="internal",
            )
            out[key] = model.assign(criteria_matrix)
    return out


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / len(union)


def build_classification_diagnostics(
    results_dir: Path,
    prices_path: Path,
    *,
    lambda_cut: float = 0.75,
    periods_per_year: int = 12,
    criteria: list[Criterion] | None = None,
    profiles: list[Profile] | None = None,
) -> ClassificationDiagnosticArtifacts:
    criteria = criteria or default_electre_criteria()
    profiles = profiles or default_electre_profiles()
    stage_dir = results_dir / "fold_stage_artifacts"
    periods = _fold_periods(results_dir).set_index("fold")
    prices = pd.read_parquet(prices_path).sort_index()
    prices.index = pd.to_datetime(prices.index)
    returns = prices.pct_change(fill_method=None)

    asset_rows: list[dict[str, object]] = []
    category_rows: list[dict[str, object]] = []
    divergence_rows: list[dict[str, object]] = []
    transition_rows: list[dict[str, object]] = []
    jaccard_rows: list[dict[str, object]] = []

    previous_categories: dict[str, str] | None = None
    previous_selected: set[str] | None = None
    previous_candidates: set[str] | None = None
    previous_fold: int | None = None
    previous_rebalance_date: str | None = None

    for fold_dir in _fold_dirs(stage_dir):
        fold = _fold_id(fold_dir)
        if fold not in periods.index:
            continue
        start = periods.loc[fold, "start_date"]
        end = periods.loc[fold, "end_date"]
        assignment_path = fold_dir / "electre_assignments.csv"
        criteria_path = fold_dir / "criteria_matrix.csv"
        if not assignment_path.exists() or not criteria_path.exists():
            continue
        assignments = pd.read_csv(assignment_path)
        matrix = pd.read_csv(criteria_path).set_index("ticker")
        variants = _variant_assignments(matrix, criteria, profiles, lambda_cut)

        baseline = assignments[["ticker", "category"]].copy()
        baseline["category"] = baseline["category"].astype(str)
        baseline_categories = dict(zip(baseline["ticker"].astype(str), baseline["category"].astype(str), strict=False))
        selected = {ticker for ticker, category in baseline_categories.items() if is_selected(category)}
        candidates = set(baseline_categories)
        rebalance_date = start.strftime("%Y-%m-%d")

        if previous_categories is not None:
            common = sorted(set(previous_categories) & set(baseline_categories))
            for ticker in common:
                transition_rows.append(
                    {
                        "from_fold": previous_fold,
                        "to_fold": fold,
                        "from_rebalance_date": previous_rebalance_date,
                        "to_rebalance_date": rebalance_date,
                        "ticker": ticker,
                        "from_category": previous_categories[ticker],
                        "to_category": baseline_categories[ticker],
                        "from_category_rank": category_rank(previous_categories[ticker]),
                        "to_category_rank": category_rank(baseline_categories[ticker]),
                    }
                )
            jaccard_rows.append(
                {
                    "from_fold": previous_fold,
                    "to_fold": fold,
                    "from_rebalance_date": previous_rebalance_date,
                    "to_rebalance_date": rebalance_date,
                    "selected_count_from": len(previous_selected or set()),
                    "selected_count_to": len(selected),
                    "selected_jaccard": _jaccard(previous_selected or set(), selected),
                    "candidate_count_from": len(previous_candidates or set()),
                    "candidate_count_to": len(candidates),
                    "candidate_jaccard": _jaccard(previous_candidates or set(), candidates),
                }
            )

        for key_left, key_right, comparison in [
            ("pessimistic_no_veto", "optimistic_no_veto", "pessimistic_vs_optimistic_no_veto"),
            ("pessimistic_with_veto", "optimistic_with_veto", "pessimistic_vs_optimistic_with_veto"),
            ("pessimistic_no_veto", "pessimistic_with_veto", "veto_effect_pessimistic"),
            ("optimistic_no_veto", "optimistic_with_veto", "veto_effect_optimistic"),
        ]:
            left = variants[key_left][["category"]].rename(columns={"category": "left_category"})
            right = variants[key_right][["category"]].rename(columns={"category": "right_category"})
            joined = left.join(right, how="inner")
            left_selected = set(joined.index[joined["left_category"].map(is_selected)])
            right_selected = set(joined.index[joined["right_category"].map(is_selected)])
            rank_diff = joined["right_category"].map(category_rank) - joined["left_category"].map(category_rank)
            divergence_rows.append(
                {
                    "fold": fold,
                    "rebalance_date": rebalance_date,
                    "comparison": comparison,
                    "left_variant": key_left,
                    "right_variant": key_right,
                    "n_assets": len(joined),
                    "category_agreement_rate": float((joined["left_category"] == joined["right_category"]).mean()) if len(joined) else np.nan,
                    "selected_jaccard": _jaccard(left_selected, right_selected),
                    "left_selected_count": len(left_selected),
                    "right_selected_count": len(right_selected),
                    "mean_rank_change_right_minus_left": float(rank_diff.mean()) if len(rank_diff) else np.nan,
                    "downgrade_count": int((rank_diff < 0).sum()),
                    "upgrade_count": int((rank_diff > 0).sum()),
                }
            )

        window_returns = returns.loc[(returns.index >= start) & (returns.index <= end)]
        for category, group in baseline.groupby("category", sort=False):
            tickers = [ticker for ticker in group["ticker"].astype(str) if ticker in window_returns.columns]
            category_returns = window_returns[tickers].dropna(axis=1, how="all") if tickers else pd.DataFrame()
            ew_returns = category_returns.mean(axis=1, skipna=True) if not category_returns.empty else pd.Series(dtype=float)
            category_rows.append(
                {
                    "fold": fold,
                    "rebalance_date": rebalance_date,
                    "forward_start_date": start.strftime("%Y-%m-%d"),
                    "forward_end_date": end.strftime("%Y-%m-%d"),
                    "category": category,
                    "category_rank": category_rank(category),
                    "n_assets": len(tickers),
                    "n_return_observations": int(ew_returns.dropna().shape[0]),
                    "equal_weight_forward_cumulative_return": float((1.0 + ew_returns.dropna()).prod() - 1.0) if not ew_returns.dropna().empty else np.nan,
                    "equal_weight_forward_cagr": annualized_cumulative_return(ew_returns, periods_per_year),
                    "equal_weight_forward_sharpe": annualized_sharpe(ew_returns, periods_per_year),
                    "equal_weight_forward_max_drawdown": max_drawdown_from_returns(ew_returns),
                    "mean_asset_forward_cumulative_return": np.nan,
                    "median_asset_forward_cumulative_return": np.nan,
                    "mean_asset_forward_sharpe": np.nan,
                    "mean_asset_forward_max_drawdown": np.nan,
                }
            )
            asset_metrics = []
            for ticker in tickers:
                series = window_returns[ticker].dropna()
                if series.empty:
                    continue
                cumulative = float((1.0 + series).prod() - 1.0)
                row = {
                    "fold": fold,
                    "rebalance_date": rebalance_date,
                    "forward_start_date": start.strftime("%Y-%m-%d"),
                    "forward_end_date": end.strftime("%Y-%m-%d"),
                    "ticker": ticker,
                    "category": category,
                    "category_rank": category_rank(category),
                    "selected": is_selected(category),
                    "forward_cumulative_return": cumulative,
                    "forward_cagr": annualized_cumulative_return(series, periods_per_year),
                    "forward_sharpe": annualized_sharpe(series, periods_per_year),
                    "forward_max_drawdown": max_drawdown_from_returns(series),
                    "n_return_observations": int(series.shape[0]),
                }
                asset_rows.append(row)
                asset_metrics.append(row)
            if asset_metrics:
                last = category_rows[-1]
                metrics_df = pd.DataFrame(asset_metrics)
                last["mean_asset_forward_cumulative_return"] = float(metrics_df["forward_cumulative_return"].mean())
                last["median_asset_forward_cumulative_return"] = float(metrics_df["forward_cumulative_return"].median())
                last["mean_asset_forward_sharpe"] = float(metrics_df["forward_sharpe"].mean(skipna=True))
                last["mean_asset_forward_max_drawdown"] = float(metrics_df["forward_max_drawdown"].mean(skipna=True))

        previous_categories = baseline_categories
        previous_selected = selected
        previous_candidates = candidates
        previous_fold = fold
        previous_rebalance_date = rebalance_date

    asset_df = pd.DataFrame(asset_rows)
    category_df = pd.DataFrame(category_rows).sort_values(["fold", "category_rank"])

    if asset_df.empty:
        effectiveness = pd.DataFrame()
    else:
        effectiveness = (
            asset_df.groupby(["category", "category_rank"], dropna=False)
            .agg(
                observations=("ticker", "size"),
                folds=("fold", "nunique"),
                unique_etfs=("ticker", "nunique"),
                selected_rate=("selected", "mean"),
                mean_forward_cumulative_return=("forward_cumulative_return", "mean"),
                median_forward_cumulative_return=("forward_cumulative_return", "median"),
                mean_forward_cagr=("forward_cagr", "mean"),
                mean_forward_sharpe=("forward_sharpe", "mean"),
                mean_forward_max_drawdown=("forward_max_drawdown", "mean"),
                pct_positive_forward_return=("forward_cumulative_return", lambda s: float((s > 0).mean())),
            )
            .reset_index()
            .sort_values("category_rank")
        )

    transitions = pd.DataFrame(transition_rows)
    if not transitions.empty:
        transition_matrix = (
            transitions.groupby(["from_category", "from_category_rank", "to_category", "to_category_rank"])
            .size()
            .reset_index(name="transition_count")
            .sort_values(["from_category_rank", "to_category_rank"])
        )
        totals = transition_matrix.groupby("from_category")["transition_count"].transform("sum")
        transition_matrix["transition_probability"] = transition_matrix["transition_count"] / totals
    else:
        transition_matrix = pd.DataFrame(
            columns=[
                "from_category",
                "from_category_rank",
                "to_category",
                "to_category_rank",
                "transition_count",
                "transition_probability",
            ]
        )

    return ClassificationDiagnosticArtifacts(
        classification_effectiveness=effectiveness,
        category_forward_returns=category_df[
            [
                "fold",
                "rebalance_date",
                "forward_start_date",
                "forward_end_date",
                "category",
                "category_rank",
                "n_assets",
                "n_return_observations",
                "equal_weight_forward_cumulative_return",
                "equal_weight_forward_cagr",
                "mean_asset_forward_cumulative_return",
                "median_asset_forward_cumulative_return",
            ]
        ],
        category_forward_sharpe=category_df[
            [
                "fold",
                "rebalance_date",
                "forward_start_date",
                "forward_end_date",
                "category",
                "category_rank",
                "n_assets",
                "n_return_observations",
                "equal_weight_forward_sharpe",
                "mean_asset_forward_sharpe",
            ]
        ],
        category_forward_drawdown=category_df[
            [
                "fold",
                "rebalance_date",
                "forward_start_date",
                "forward_end_date",
                "category",
                "category_rank",
                "n_assets",
                "n_return_observations",
                "equal_weight_forward_max_drawdown",
                "mean_asset_forward_max_drawdown",
            ]
        ],
        pessimistic_optimistic_divergence=pd.DataFrame(divergence_rows).sort_values(["fold", "comparison"]),
        category_transition_matrix=transition_matrix,
        selection_jaccard_by_fold=pd.DataFrame(jaccard_rows),
    )


def write_classification_diagnostics(
    results_dir: Path,
    prices_path: Path,
    output_dir: Path,
    *,
    lambda_cut: float = 0.75,
) -> ClassificationDiagnosticArtifacts:
    artifacts = build_classification_diagnostics(results_dir, prices_path, lambda_cut=lambda_cut)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in {
        "classification_effectiveness.csv": artifacts.classification_effectiveness,
        "category_forward_returns.csv": artifacts.category_forward_returns,
        "category_forward_sharpe.csv": artifacts.category_forward_sharpe,
        "category_forward_drawdown.csv": artifacts.category_forward_drawdown,
        "pessimistic_optimistic_divergence.csv": artifacts.pessimistic_optimistic_divergence,
        "category_transition_matrix.csv": artifacts.category_transition_matrix,
        "selection_jaccard_by_fold.csv": artifacts.selection_jaccard_by_fold,
    }.items():
        table.to_csv(output_dir / name, index=False)
    return artifacts
