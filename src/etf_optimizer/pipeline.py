from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Literal

import pandas as pd

from etf_optimizer.backtesting.engine import BacktestConfig, BacktestResult, WalkForwardBacktester
from etf_optimizer.backtesting.metrics import performance_summary
from etf_optimizer.data.sec_universe import PointInTimeETFUniverseProvider
from etf_optimizer.features import compute_feature_table
from etf_optimizer.optimization.exposure import (
    apply_group_exposure_cap,
    classify_etf_risk_bucket,
)
from etf_optimizer.optimization.portfolio import (
    equal_weight,
    ledoit_wolf_covariance,
    max_sharpe_weights,
    min_variance_weights,
    sample_covariance,
)
from etf_optimizer.optimization.rebalancing import apply_transaction_cost, compute_turnover
from etf_optimizer.selection.electre_tri import Criterion, ElectreTri, Profile
from etf_optimizer.selection.flowsort import FlowSort, FlowSortPreference
from etf_optimizer.thesis_alignment import (
    assign_electre_by_peer_group,
    finalize_thesis_selection,
    peer_group_lookup,
    thesis_category,
)

StrategyName = Literal["equal_weight", "min_variance", "max_sharpe"]
AssignmentName = Literal["pessimistic", "optimistic"]
WeightDriftName = Literal["constant_mix", "buy_and_hold"]
RebalancePolicyName = Literal["calendar", "threshold"]
RecategorizationPolicyName = Literal["rebalance_only", "every_period"]


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
    electre_assignment: AssignmentName = "pessimistic"
    electre_use_veto: bool = True
    electre_backend: Literal["internal", "pydecision_tri_b"] = "internal"
    weight_drift: WeightDriftName = "buy_and_hold"
    rebalance_policy: RebalancePolicyName = "calendar"
    drift_tolerance: float = 0.05
    optimizer_fallback: bool = True
    recategorization_policy: RecategorizationPolicyName = "rebalance_only"
    turnover_penalty: float = 0.0
    category_confirmation_periods: int = 1
    category_change_min_score_improvement: float = 0.0
    asset_metadata: pd.DataFrame | None = None
    category_exposure_cap: float | None = None
    universe_provider: PointInTimeETFUniverseProvider | None = None
    universe_min_age_months: int = 0
    universe_min_coverage_pct: float | None = None
    universe_min_avg_dollar_volume: float | None = None
    flowsort_preference_function: FlowSortPreference = "v_shape"
    flowsort_use_net_flow: bool = True
    fold_artifacts_dir: Path | None = None
    benchmark_returns: pd.Series | pd.DataFrame | None = None
    benchmark_map: dict[str, str] | None = None
    expense_ratios: pd.Series | dict[str, float] | pd.DataFrame | None = None
    use_peer_group_profiles: bool = False
    peer_group_min_size: int = 5
    thesis_selection_min_assets: int | None = None
    thesis_selection_max_assets: int | None = None


@dataclass
class FoldStageArtifacts:
    fold_id: int
    rebalance_date: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp | None
    universe_snapshot: pd.DataFrame
    criteria_matrix: pd.DataFrame
    electre_assignments: pd.DataFrame
    flowsort_assignments: pd.DataFrame
    selected_etfs: pd.DataFrame
    portfolio_weights: pd.DataFrame
    fold_performance: pd.DataFrame
    classification_diagnostics: pd.DataFrame


@dataclass(frozen=True)
class PipelineResult:
    features: pd.DataFrame
    selection: pd.DataFrame
    selection_by_rebalance: pd.DataFrame
    selected_assets: list[str]
    backtest: BacktestResult
    summary: pd.DataFrame
    fold_artifacts: list[FoldStageArtifacts] | None = None


def _select_assets(selection: pd.DataFrame) -> list[str]:
    selected = [idx for idx, row in selection.iterrows() if str(row["category"]).startswith("above_")]
    if not selected:
        # Fallback: keep the highest-credibility assets so the research pipeline remains runnable.
        credibility_cols = [col for col in selection.columns if col.startswith("credibility_")]
        if not credibility_cols:
            raise ValueError("selection output has no credibility columns")
        selected = selection[credibility_cols].max(axis=1).sort_values(ascending=False).head(5).index.tolist()
    return selected


def _risk_bucket_lookup(metadata: pd.DataFrame | None, tickers: list[str]) -> dict[str, str]:
    if metadata is None or "ticker" not in metadata.columns:
        return {ticker: classify_etf_risk_bucket(ticker) for ticker in tickers}
    meta = metadata.drop_duplicates("ticker").set_index("ticker")
    buckets: dict[str, str] = {}
    for ticker in tickers:
        if ticker in meta.index:
            row = meta.loc[ticker]
            name = str(row.get("name", "")) if "name" in meta.columns else ""
            category = str(row.get("category", "")) if "category" in meta.columns else ""
        else:
            name = ""
            category = ""
        buckets[ticker] = classify_etf_risk_bucket(ticker, name, category)
    return buckets


def _diversify_for_category_cap(
    selected_assets: list[str],
    selection: pd.DataFrame,
    config: PipelineConfig,
) -> list[str]:
    if config.category_exposure_cap is None or config.asset_metadata is None:
        return selected_assets
    required_buckets = math.ceil(1.0 / config.category_exposure_cap)
    if required_buckets <= 1:
        return selected_assets
    all_assets = selection.index.astype(str).tolist()
    buckets = _risk_bucket_lookup(config.asset_metadata, all_assets)
    selected = list(dict.fromkeys(str(asset) for asset in selected_assets))
    selected_buckets = {buckets.get(asset, classify_etf_risk_bucket(asset)) for asset in selected}
    if len(selected_buckets) >= required_buckets:
        return selected
    credibility_cols = [col for col in selection.columns if col.startswith("credibility_")]
    if credibility_cols:
        ranked = selection[credibility_cols].max(axis=1).sort_values(ascending=False).index.astype(str).tolist()
    else:
        ranked = all_assets
    for asset in ranked:
        bucket = buckets.get(asset, classify_etf_risk_bucket(asset))
        if asset not in selected and bucket not in selected_buckets:
            selected.append(asset)
            selected_buckets.add(bucket)
        if len(selected_buckets) >= required_buckets:
            break
    return selected


def _finalize_selected_assets(selection: pd.DataFrame, config: PipelineConfig) -> list[str]:
    selected_assets = _diversify_for_category_cap(_select_assets(selection), selection, config)
    if config.thesis_selection_min_assets is None and config.thesis_selection_max_assets is None:
        return selected_assets
    return finalize_thesis_selection(
        selection,
        min_assets=config.thesis_selection_min_assets or 1,
        max_assets=config.thesis_selection_max_assets or len(selection),
    )


def _apply_exposure_controls(weights: pd.Series, config: PipelineConfig) -> pd.Series:
    if config.category_exposure_cap is None:
        return weights
    if config.asset_metadata is None:
        raise ValueError("asset_metadata is required when category_exposure_cap is set")
    controlled = apply_group_exposure_cap(weights, config.asset_metadata, cap=config.category_exposure_cap)
    return controlled.reindex(weights.index, fill_value=0.0)


def _optimize_weights(
    train: pd.DataFrame,
    config: PipelineConfig,
) -> tuple[pd.Series, list[dict[str, str]]]:
    cov = (
        ledoit_wolf_covariance(train, config.periods_per_year)
        if config.covariance == "ledoit_wolf" and len(train) > train.shape[1]
        else sample_covariance(train, config.periods_per_year)
    )
    diagnostics: list[dict[str, str]] = []

    def record_success(strategy_name: str, weights: pd.Series) -> tuple[pd.Series, list[dict[str, str]]]:
        weights = _apply_exposure_controls(weights, config)
        diagnostics.append({"strategy": strategy_name, "status": "success", "error": ""})
        return weights, diagnostics

    if config.strategy == "equal_weight":
        return record_success("equal_weight", equal_weight(train.columns))
    if config.strategy == "min_variance":
        return record_success("min_variance", min_variance_weights(cov, max_weight=config.max_weight))

    expected_returns = train.mean() * config.periods_per_year
    try:
        return record_success(
            "max_sharpe",
            max_sharpe_weights(
                expected_returns,
                cov,
                risk_free_rate=config.risk_free_rate,
                max_weight=config.max_weight,
            ),
        )
    except Exception as exc:
        diagnostics.append({"strategy": "max_sharpe", "status": "failed", "error": str(exc)})
        if not config.optimizer_fallback:
            raise

    try:
        return record_success("min_variance", min_variance_weights(cov, max_weight=config.max_weight))
    except Exception as exc:
        diagnostics.append({"strategy": "min_variance", "status": "failed", "error": str(exc)})
        return record_success("equal_weight", equal_weight(train.columns))


def _make_strategy(config: PipelineConfig, selected_assets: list[str]):
    def strategy(train_returns: pd.DataFrame) -> pd.Series:
        train = train_returns[selected_assets].dropna(axis=1, how="all")
        if train.isna().any().any():
            missing_counts = train.isna().sum()
            missing_assets = missing_counts[missing_counts > 0].index.tolist()
            raise ValueError(f"missing returns in training window for selected assets: {missing_assets}")
        if train.shape[1] == 0:
            raise ValueError("no selected assets available in training window")
        weights, _diagnostics = _optimize_weights(train, config)
        return weights

    return strategy


def _compute_mcdm_selection(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    config: PipelineConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    criteria_cols = features_columns(config.criteria)
    features = compute_feature_table(
        prices,
        volume=volume,
        benchmark_returns=config.benchmark_returns,
        benchmark_map=config.benchmark_map,
        expense_ratios=config.expense_ratios,
        risk_free_rate=config.risk_free_rate,
        periods_per_year=config.periods_per_year,
    ).dropna(subset=criteria_cols)
    criteria_matrix = features[criteria_cols]
    if config.use_peer_group_profiles:
        electre_assignments = assign_electre_by_peer_group(
            criteria_matrix,
            config.criteria,
            config.profiles,
            metadata=config.asset_metadata,
            lambda_cut=config.lambda_cut,
            assignment=config.electre_assignment,
            use_veto=config.electre_use_veto,
            backend=config.electre_backend,
            min_group_size=config.peer_group_min_size,
        )
    else:
        electre_model = ElectreTri(
            config.criteria,
            config.profiles,
            config.lambda_cut,
            assignment=config.electre_assignment,
            use_veto=config.electre_use_veto,
            backend=config.electre_backend,
        )
        electre_assignments = electre_model.assign(criteria_matrix)
        if config.asset_metadata is not None:
            electre_assignments["peer_group"] = peer_group_lookup(config.asset_metadata, electre_assignments.index)
            electre_assignments["profile_scope"] = "global"
    flowsort_model = FlowSort(
        config.criteria,
        config.profiles,
        preference_function=config.flowsort_preference_function,
        use_net_flow=config.flowsort_use_net_flow,
    )
    flowsort_assignments = flowsort_model.assign(criteria_matrix)
    selected_assets = _finalize_selected_assets(electre_assignments, config)
    return features, electre_assignments, flowsort_assignments, selected_assets


def _compute_electre_selection(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    config: PipelineConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    features, electre_assignments, _flowsort_assignments, selected_assets = _compute_mcdm_selection(
        prices,
        volume,
        config,
    )
    return features, electre_assignments, selected_assets


def _classification_diagnostics(
    rebalance_date: pd.Timestamp,
    electre_assignments: pd.DataFrame,
    flowsort_assignments: pd.DataFrame,
    selected_assets: list[str],
) -> pd.DataFrame:
    joined = electre_assignments[["category"]].rename(columns={"category": "electre_category"}).join(
        flowsort_assignments[["category"]].rename(columns={"category": "flowsort_category"}),
        how="outer",
    )
    agreement = joined["electre_category"].astype(str) == joined["flowsort_category"].astype(str)
    return pd.DataFrame(
        [
            {
                "rebalance_date": rebalance_date,
                "n_candidates": int(len(joined)),
                "n_selected": int(len(selected_assets)),
                "electre_flowsort_agreement_rate": float(agreement.mean()) if len(agreement) else 0.0,
                "electre_top_category_count": int(joined["electre_category"].astype(str).str.startswith("above_").sum()),
                "flowsort_top_category_count": int(joined["flowsort_category"].astype(str).str.startswith("above_").sum()),
            }
        ]
    )


def _eligible_universe_as_of(
    as_of: pd.Timestamp,
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    columns: pd.Index,
    config: PipelineConfig,
) -> pd.DataFrame:
    if config.universe_provider is None:
        return pd.DataFrame(
            {
                "ticker": [str(column) for column in columns],
                "fund_id": [str(column) for column in columns],
                "source": "input_price_columns",
                "data_quality_flag": "static_input_columns_no_pit_provider",
            }
        )
    eligible = config.universe_provider.constituents_as_of(
        as_of,
        min_age_months=config.universe_min_age_months,
        min_coverage_pct=config.universe_min_coverage_pct,
        min_avg_dollar_volume=config.universe_min_avg_dollar_volume,
        prices=prices,
        volume=volume,
        lookback_periods=config.train_size + 1,
    )
    ticker_series = eligible["ticker"] if "ticker" in eligible.columns else pd.Series(dtype=str)
    column_set = {str(column).upper() for column in columns}
    eligible_tickers = ticker_series.dropna().astype(str).str.upper().isin(column_set)
    return eligible.loc[eligible_tickers].copy().reset_index(drop=True)


def _eligible_columns_as_of(
    as_of: pd.Timestamp,
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    columns: pd.Index,
    config: PipelineConfig,
) -> list[str]:
    """Return rebalance-date eligible columns under a point-in-time universe provider."""
    if config.universe_provider is None:
        return [str(column) for column in columns]
    eligible = _eligible_universe_as_of(as_of, prices, volume, columns, config)
    ticker_series = eligible["ticker"] if "ticker" in eligible.columns else pd.Series(dtype=str)
    eligible_tickers = set(ticker_series.dropna().astype(str).str.upper())
    return [ticker for ticker in [str(column) for column in columns] if ticker.upper() in eligible_tickers]


def _with_ticker_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "ticker" not in out.columns:
        out.insert(0, "ticker", out.index.astype(str))
    return out.reset_index(drop=True)


def _build_selected_etfs(selected_assets: list[str], electre_assignments: pd.DataFrame, flowsort_assignments: pd.DataFrame) -> pd.DataFrame:
    selected = pd.DataFrame({"ticker": selected_assets})
    if selected.empty:
        return selected
    selected = selected.join(
        electre_assignments[["category"]].rename(columns={"category": "electre_category"}),
        on="ticker",
    )
    selected = selected.join(
        flowsort_assignments[["category"]].rename(columns={"category": "flowsort_category"}),
        on="ticker",
    )
    if "peer_group" in electre_assignments.columns:
        selected = selected.join(electre_assignments[["peer_group"]], on="ticker")
    if "profile_scope" in electre_assignments.columns:
        selected = selected.join(electre_assignments[["profile_scope"]], on="ticker")
    selected["thesis_category"] = selected["electre_category"].map(thesis_category)
    selected["selection_rule"] = "electre_top_category_or_credibility_fallback_or_thesis_cardinality"
    return selected


def _write_fold_artifacts(artifacts: list[FoldStageArtifacts], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        fold_dir = output_dir / f"fold_{artifact.fold_id:03d}_{artifact.rebalance_date:%Y_%m_%d}"
        fold_dir.mkdir(parents=True, exist_ok=True)
        artifact.universe_snapshot.to_csv(fold_dir / "universe_snapshot.csv", index=False)
        artifact.criteria_matrix.to_csv(fold_dir / "criteria_matrix.csv", index=False)
        artifact.electre_assignments.to_csv(fold_dir / "electre_assignments.csv", index=False)
        artifact.flowsort_assignments.to_csv(fold_dir / "flowsort_assignments.csv", index=False)
        artifact.selected_etfs.to_csv(fold_dir / "selected_etfs.csv", index=False)
        artifact.portfolio_weights.to_csv(fold_dir / "portfolio_weights.csv", index=False)
        artifact.fold_performance.to_csv(fold_dir / "fold_performance.csv", index=False)
        artifact.classification_diagnostics.to_csv(fold_dir / "classification_diagnostics.csv", index=False)


def _attach_fold_performance(
    artifacts: list[FoldStageArtifacts],
    portfolio_returns: pd.Series,
    config: PipelineConfig,
) -> None:
    for artifact in artifacts:
        fold_returns = portfolio_returns.loc[portfolio_returns.index >= artifact.test_start]
        if artifact.test_end is not None:
            fold_returns = fold_returns.loc[fold_returns.index <= artifact.test_end]
        metrics = performance_summary(
            fold_returns,
            risk_free_rate=config.risk_free_rate,
            periods_per_year=config.periods_per_year,
        )
        artifact.fold_performance = pd.DataFrame(
            [
                {
                    "fold_id": artifact.fold_id,
                    "rebalance_date": artifact.rebalance_date,
                    "test_start": artifact.test_start,
                    "test_end": artifact.test_end,
                    "n_periods": int(len(fold_returns)),
                    **metrics,
                }
            ]
        )


def _selection_trace_rows(
    rebalance_date: pd.Timestamp,
    features: pd.DataFrame,
    selection: pd.DataFrame,
    selected_assets: list[str],
) -> pd.DataFrame:
    trace = features.join(selection[["category"]], how="inner")
    if "peer_group" in selection.columns:
        trace = trace.join(selection[["peer_group"]], how="left")
    if "profile_scope" in selection.columns:
        trace = trace.join(selection[["profile_scope"]], how="left")
    trace = trace.assign(
        rebalance_date=rebalance_date,
        ticker=trace.index,
        selected=trace.index.isin(selected_assets),
        thesis_category=trace["category"].map(thesis_category),
    )
    columns = [
        "rebalance_date",
        "ticker",
        "selected",
        "category",
        "thesis_category",
        "cagr",
        "volatility",
        "sharpe",
        "sortino",
    ]
    for optional in ["peer_group", "profile_scope", "liquidity", "tracking_error", "expense_ratio"]:
        if optional in trace.columns:
            columns.append(optional)
    if "avg_dollar_volume" in trace.columns:
        columns.append("avg_dollar_volume")
    return trace[columns].reset_index(drop=True)


def _selected_set_score(selection: pd.DataFrame, selected_assets: set[str], config: PipelineConfig) -> float:
    """Score a candidate selected set using current-window ELECTRE credibility."""
    if not selected_assets:
        return float("-inf")
    selected_index = [asset for asset in selected_assets if asset in selection.index]
    if not selected_index:
        return float("-inf")
    if config.profiles:
        credibility_col = f"credibility_{config.profiles[-1].name}"
        if credibility_col in selection.columns:
            scores = pd.Series(pd.to_numeric(selection.loc[selected_index, credibility_col], errors="coerce"))
            return float(scores.mean())
    category_score = selection.loc[selected_index, "category"].astype(str).str.startswith("above_").astype(float)
    return float(category_score.mean())


def _make_walk_forward_electre_strategy(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    returns_index: pd.Index,
    config: PipelineConfig,
    first_selection: dict[str, pd.DataFrame] | None = None,
    selection_trace_rows: list[pd.DataFrame] | None = None,
    fold_artifacts: list[FoldStageArtifacts] | None = None,
):
    def strategy(train_returns: pd.DataFrame) -> pd.Series:
        future_return_dates = returns_index[returns_index > train_returns.index[-1]]
        if future_return_dates.empty:
            raise ValueError("cannot infer rebalance date after training window")
        rebalance_date = pd.Timestamp(future_return_dates[0])
        universe_snapshot = _eligible_universe_as_of(
            rebalance_date,
            prices.loc[: train_returns.index[-1]],
            volume.loc[: train_returns.index[-1]] if volume is not None else None,
            train_returns.columns,
            config,
        )
        ticker_series = universe_snapshot["ticker"] if "ticker" in universe_snapshot.columns else pd.Series(dtype=str)
        eligible_tickers = set(ticker_series.dropna().astype(str).str.upper())
        eligible_columns = [ticker for ticker in [str(column) for column in train_returns.columns] if ticker.upper() in eligible_tickers]
        if not eligible_columns:
            raise ValueError(f"no point-in-time eligible assets as of {rebalance_date.date()}")
        train_returns = train_returns[eligible_columns]
        train_prices = prices.loc[: train_returns.index[-1], train_returns.columns].tail(len(train_returns) + 1)
        train_volume = None
        if volume is not None:
            train_volume = volume.reindex(train_prices.index).loc[:, list(train_prices.columns)]
        features, selection, flowsort_assignments, selected_assets = _compute_mcdm_selection(train_prices, train_volume, config)
        if first_selection is not None and not first_selection:
            first_selection["features"] = features
            first_selection["selection"] = selection
        if selection_trace_rows is not None:
            selection_trace_rows.append(
                _selection_trace_rows(rebalance_date, features, selection, selected_assets)
            )
        selected_train = train_returns[selected_assets].dropna(axis=0, how="any")
        if selected_train.shape[1] == 0:
            raise ValueError("no selected assets available in training window")
        weights, optimizer_diagnostics = _optimize_weights(selected_train, config)
        if fold_artifacts is not None:
            fold_id = len(fold_artifacts) + 1
            test_window = returns_index[returns_index >= rebalance_date][: config.test_size]
            test_end = pd.Timestamp(test_window[-1]) if len(test_window) else None
            portfolio_weights = weights.rename("weight").reset_index()
            portfolio_weights = portfolio_weights.rename(columns={portfolio_weights.columns[0]: "ticker"})
            portfolio_weights.insert(0, "rebalance_date", rebalance_date)
            portfolio_weights["allocation_method"] = config.strategy
            portfolio_weights["optimizer_diagnostics"] = str(optimizer_diagnostics)
            criteria_matrix = _with_ticker_column(features[features_columns(config.criteria)])
            fold_artifacts.append(
                FoldStageArtifacts(
                    fold_id=fold_id,
                    rebalance_date=rebalance_date,
                    test_start=rebalance_date,
                    test_end=test_end,
                    universe_snapshot=universe_snapshot,
                    criteria_matrix=criteria_matrix,
                    electre_assignments=_with_ticker_column(selection),
                    flowsort_assignments=_with_ticker_column(flowsort_assignments),
                    selected_etfs=_build_selected_etfs(selected_assets, selection, flowsort_assignments),
                    portfolio_weights=portfolio_weights,
                    fold_performance=pd.DataFrame(),
                    classification_diagnostics=_classification_diagnostics(
                        rebalance_date,
                        selection,
                        flowsort_assignments,
                        selected_assets,
                    ),
                )
            )
        return weights

    return strategy


def _run_every_period_recategorization(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    returns: pd.DataFrame,
    config: PipelineConfig,
) -> tuple[BacktestResult, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    portfolio_returns: list[float] = []
    portfolio_index: list[pd.Timestamp] = []
    weight_rows: list[pd.Series] = []
    effective_rows: list[pd.Series] = []
    event_rows: list[dict[str, float | str | pd.Timestamp]] = []
    selection_trace_rows: list[pd.DataFrame] = []
    first_features: pd.DataFrame | None = None
    first_selection: pd.DataFrame | None = None
    current_weights = pd.Series(0.0, index=returns.columns, dtype=float)
    target_weights = pd.Series(0.0, index=returns.columns, dtype=float)
    previous_selected: set[str] | None = None
    pending_selected: set[str] | None = None
    pending_target: pd.Series | None = None
    pending_count = 0
    if config.category_confirmation_periods <= 0:
        raise ValueError("category_confirmation_periods must be positive")
    if config.category_change_min_score_improvement < 0.0:
        raise ValueError("category_change_min_score_improvement must be nonnegative")

    for pos in range(config.train_size, len(returns)):
        train_returns = returns.iloc[pos - config.train_size : pos]
        test_date = pd.Timestamp(returns.index[pos])
        eligible_columns = _eligible_columns_as_of(
            test_date,
            prices.loc[: train_returns.index[-1]],
            volume.loc[: train_returns.index[-1]] if volume is not None else None,
            train_returns.columns,
            config,
        )
        if not eligible_columns:
            raise ValueError(f"no point-in-time eligible assets as of {test_date.date()}")
        train_returns = train_returns[eligible_columns]
        train_prices = prices.loc[: train_returns.index[-1], train_returns.columns].tail(len(train_returns) + 1)
        train_volume = None
        if volume is not None:
            train_volume = volume.reindex(train_prices.index).loc[:, list(train_prices.columns)]
        features, selection, selected_assets = _compute_electre_selection(train_prices, train_volume, config)
        if first_features is None:
            first_features = features
            first_selection = selection
        selection_trace_rows.append(_selection_trace_rows(test_date, features, selection, selected_assets))

        selected_set = set(selected_assets)
        selected_train = train_returns[selected_assets].dropna(axis=0, how="any")
        if selected_train.shape[1] == 0:
            raise ValueError("no selected assets available in training window")
        optimized_weights, _diagnostics = _optimize_weights(selected_train, config)
        proposed_target = optimized_weights.reindex(returns.columns, fill_value=0.0).astype(float)
        proposed_target = proposed_target / proposed_target.sum()
        if previous_selected is not None and config.turnover_penalty:
            if not 0.0 <= config.turnover_penalty <= 1.0:
                raise ValueError("turnover_penalty must be between 0 and 1")
            proposed_target = (
                (1.0 - config.turnover_penalty) * proposed_target
                + config.turnover_penalty * current_weights.reindex(returns.columns, fill_value=0.0)
            )
            proposed_target = proposed_target / proposed_target.sum()

        event_type = ""
        max_abs_drift = 0.0
        if previous_selected is None:
            event_type = "calendar"
            pending_selected = None
            pending_target = None
            pending_count = 0
        elif selected_set != previous_selected:
            if selected_set == pending_selected:
                pending_count += 1
            else:
                pending_selected = selected_set
                pending_target = proposed_target.copy()
                pending_count = 1
            if pending_count >= config.category_confirmation_periods:
                current_score = _selected_set_score(selection, previous_selected, config)
                proposed_score = _selected_set_score(selection, selected_set, config)
                score_improvement = proposed_score - current_score
                if score_improvement >= config.category_change_min_score_improvement:
                    event_type = "category_change"
                    if pending_target is not None:
                        proposed_target = pending_target.copy()
                    pending_selected = None
                    pending_target = None
                    pending_count = 0
        elif config.rebalance_policy == "threshold":
            drift = (current_weights - target_weights).abs()
            max_abs_drift = float(drift.max()) if not drift.empty else 0.0
            if max_abs_drift > config.drift_tolerance:
                event_type = "threshold"

        event_turnover = 0.0
        if event_type:
            if event_type != "threshold":
                max_abs_drift = float((current_weights - proposed_target).abs().max())
            event_turnover = compute_turnover(current_weights, proposed_target)
            current_weights = proposed_target.copy()
            target_weights = proposed_target.copy()
            previous_selected = selected_set
            weight_rows.append(pd.Series(target_weights, name=test_date))
            event_rows.append(
                {
                    "date": test_date,
                    "event_type": event_type,
                    "turnover": event_turnover,
                    "max_abs_drift": max_abs_drift,
                }
            )

        effective_rows.append(pd.Series(current_weights, name=test_date))
        period_returns = returns.loc[test_date, current_weights.index]
        period_return = float((period_returns * current_weights).sum())
        if event_turnover:
            period_return = apply_transaction_cost(period_return, event_turnover, config.cost_bps)
        portfolio_returns.append(period_return)
        portfolio_index.append(test_date)
        if config.weight_drift == "buy_and_hold":
            growth = 1.0 + period_return
            if growth != 0:
                current_weights = current_weights * (1.0 + period_returns) / growth
                current_weights = current_weights / current_weights.sum()
        else:
            current_weights = target_weights.copy()

    if not portfolio_returns or first_features is None or first_selection is None:
        raise ValueError("not enough observations for every-period recategorization")
    rebalance_events = pd.DataFrame(event_rows).set_index("date").sort_index()
    backtest = BacktestResult(
        portfolio_returns=pd.Series(portfolio_returns, index=portfolio_index).sort_index(),
        weights=pd.DataFrame(weight_rows),
        turnover=rebalance_events["turnover"],
        effective_weights=pd.DataFrame(effective_rows),
        rebalance_events=rebalance_events,
    )
    selection_by_rebalance = pd.concat(selection_trace_rows, ignore_index=True)
    selected_assets_all = backtest.weights.columns[(backtest.weights.abs() > 0.0).any(axis=0)].tolist()
    return backtest, first_features, first_selection, selection_by_rebalance, selected_assets_all


def run_research_pipeline(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    config: PipelineConfig,
) -> PipelineResult:
    """Run the thesis MVP: features → ELECTRE Tri → optimization → walk-forward test.

    This is intentionally transparent rather than overly automated. Researchers can
    inspect each intermediate output and report the methodology in a thesis appendix.
    """
    prices = prices.sort_index()
    sorted_volume = volume.sort_index() if volume is not None else None
    returns = prices.pct_change().dropna(how="all")
    if config.recategorization_policy == "every_period":
        backtest, features, selection, selection_by_rebalance, selected_assets = _run_every_period_recategorization(
            prices,
            sorted_volume,
            returns,
            config,
        )
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
        return PipelineResult(features, selection, selection_by_rebalance, selected_assets, backtest, summary)

    backtester = WalkForwardBacktester(
        BacktestConfig(
            train_size=config.train_size,
            test_size=config.test_size,
            step_size=config.step_size,
            cost_bps=config.cost_bps,
            weight_drift=config.weight_drift,
            rebalance_policy=config.rebalance_policy,
            drift_tolerance=config.drift_tolerance,
        )
    )
    first_selection: dict[str, pd.DataFrame] = {}
    selection_trace_rows: list[pd.DataFrame] = []
    fold_artifacts: list[FoldStageArtifacts] = []
    backtest = backtester.run(
        returns,
        _make_walk_forward_electre_strategy(
            prices,
            sorted_volume,
            returns.index,
            config,
            first_selection,
            selection_trace_rows,
            fold_artifacts,
        ),
    )
    features = first_selection["features"]
    selection = first_selection["selection"]
    selection_by_rebalance = pd.concat(selection_trace_rows, ignore_index=True)
    selected_assets = backtest.weights.columns[(backtest.weights.abs() > 0.0).any(axis=0)].tolist()
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
    _attach_fold_performance(fold_artifacts, backtest.portfolio_returns, config)
    if config.fold_artifacts_dir is not None:
        _write_fold_artifacts(fold_artifacts, config.fold_artifacts_dir)
    return PipelineResult(features, selection, selection_by_rebalance, selected_assets, backtest, summary, fold_artifacts)


def features_columns(criteria: list[Criterion]) -> list[str]:
    return [criterion.name for criterion in criteria]
