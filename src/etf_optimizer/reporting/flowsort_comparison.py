from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from etf_optimizer.reporting.classification_diagnostics import (
    _fold_dirs,
    _fold_id,
    _fold_periods,
    _jaccard,
    annualized_cumulative_return,
    default_electre_criteria,
    default_electre_profiles,
    is_selected,
)
from etf_optimizer.selection.electre_tri import Criterion, Profile
from etf_optimizer.selection.flowsort import FlowSort

FLOW_SORT_VARIANTS: tuple[tuple[str, str, bool], ...] = (
    ("usual_net_flow", "usual", True),
    ("v_shape_net_flow", "v_shape", True),
    ("level_net_flow", "level", True),
    ("v_shape_leaving_flow", "v_shape", False),
)


def cohen_kappa(left: pd.Series, right: pd.Series) -> float:
    joined = pd.DataFrame({"left": left.astype(str), "right": right.astype(str)}).dropna()
    if joined.empty:
        return float("nan")
    observed = float((joined["left"] == joined["right"]).mean())
    labels = sorted(set(joined["left"]) | set(joined["right"]))
    expected = 0.0
    for label in labels:
        expected += float((joined["left"] == label).mean()) * float((joined["right"] == label).mean())
    if np.isclose(1.0 - expected, 0.0):
        return 1.0 if np.isclose(observed, 1.0) else 0.0
    return float((observed - expected) / (1.0 - expected))


def _forward_equal_weight_returns(
    tickers: list[str],
    returns: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.Series:
    window = returns.loc[(returns.index >= start) & (returns.index <= end)]
    available = [ticker for ticker in tickers if ticker in window.columns]
    if not available:
        return pd.Series(dtype=float)
    return window[available].dropna(axis=1, how="all").mean(axis=1, skipna=True)


def _pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.2%}"


def _num(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.3f}"


def _markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sin datos._"
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df[columns].iterrows():
        rows.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(rows)


def build_flowsort_comparison(
    results_dir: Path,
    prices_path: Path,
    *,
    criteria: list[Criterion] | None = None,
    profiles: list[Profile] | None = None,
    periods_per_year: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    criteria = criteria or default_electre_criteria()
    profiles = profiles or default_electre_profiles()
    stage_dir = results_dir / "fold_stage_artifacts"
    periods = _fold_periods(results_dir).set_index("fold")
    prices = pd.read_parquet(prices_path).sort_index()
    prices.index = pd.to_datetime(prices.index)
    returns = prices.pct_change(fill_method=None)

    assignment_rows: list[dict[str, object]] = []
    flow_rows: list[dict[str, object]] = []
    agreement_rows: list[dict[str, object]] = []
    previous_by_variant: dict[str, dict[str, str]] = {}
    previous_selected_by_variant: dict[str, set[str]] = {}
    previous_fold_by_variant: dict[str, int] = {}
    previous_date_by_variant: dict[str, str] = {}

    for fold_dir in _fold_dirs(stage_dir):
        fold = _fold_id(fold_dir)
        if fold not in periods.index:
            continue
        assignment_path = fold_dir / "electre_assignments.csv"
        criteria_path = fold_dir / "criteria_matrix.csv"
        if not assignment_path.exists() or not criteria_path.exists():
            continue

        start = periods.loc[fold, "start_date"]
        end = periods.loc[fold, "end_date"]
        rebalance_date = start.strftime("%Y-%m-%d")
        matrix = pd.read_csv(criteria_path).set_index("ticker")
        electre = pd.read_csv(assignment_path)[["ticker", "category"]].copy()
        electre["ticker"] = electre["ticker"].astype(str)
        electre["category"] = electre["category"].astype(str)
        electre_categories = dict(zip(electre["ticker"], electre["category"], strict=False))
        electre_selected = {ticker for ticker, category in electre_categories.items() if is_selected(category)}

        for variant, preference_function, use_net_flow in FLOW_SORT_VARIANTS:
            model = FlowSort(criteria, profiles, preference_function=preference_function, use_net_flow=use_net_flow)  # type: ignore[arg-type]
            assigned = model.assign(matrix)
            assigned.index = assigned.index.astype(str)
            joined = assigned.join(electre.set_index("ticker").rename(columns={"category": "electre_category"}), how="inner")
            joined["flowsort_category"] = joined["category"].astype(str)
            selected = set(joined.index[joined["flowsort_category"].map(is_selected)])

            for ticker, row in joined.iterrows():
                base = {
                    "fold": fold,
                    "rebalance_date": rebalance_date,
                    "ticker": ticker,
                    "variant": variant,
                    "preference_function": preference_function,
                    "flow_assignment_rule": "net_flow" if use_net_flow else "leaving_flow",
                    "electre_category": row["electre_category"],
                    "flowsort_category": row["flowsort_category"],
                }
                assignment_rows.append(base)
                flow_rows.append(
                    {
                        **base,
                        "flowsort_leaving_flow": row["flowsort_leaving_flow"],
                        "flowsort_entering_flow": row["flowsort_entering_flow"],
                        "flowsort_net_flow": row["flowsort_net_flow"],
                        "ranking_flow": row["ranking_flow"],
                    }
                )

            agreement_rows.append(
                {
                    "comparison_scope": "electre_vs_flowsort_agreement",
                    "fold": fold,
                    "rebalance_date": rebalance_date,
                    "variant": variant,
                    "category": "all",
                    "n_assets": len(joined),
                    "category_agreement_rate": float((joined["electre_category"] == joined["flowsort_category"]).mean()) if len(joined) else np.nan,
                    "selected_jaccard": _jaccard(electre_selected, selected),
                    "cohen_kappa": cohen_kappa(joined["electre_category"], joined["flowsort_category"]),
                    "temporal_selected_jaccard": np.nan,
                    "temporal_category_agreement_rate": np.nan,
                    "mean_equal_weight_forward_cumulative_return": np.nan,
                    "mean_equal_weight_forward_cagr": np.nan,
                }
            )

            if variant in previous_by_variant:
                previous = previous_by_variant[variant]
                common = sorted(set(previous) & set(joined.index))
                current_categories = joined["flowsort_category"].to_dict()
                agreement_rows.append(
                    {
                        "comparison_scope": "temporal_stability",
                        "fold": fold,
                        "from_fold": previous_fold_by_variant[variant],
                        "to_fold": fold,
                        "from_rebalance_date": previous_date_by_variant[variant],
                        "rebalance_date": rebalance_date,
                        "variant": variant,
                        "category": "all",
                        "n_assets": len(common),
                        "category_agreement_rate": np.nan,
                        "selected_jaccard": np.nan,
                        "cohen_kappa": np.nan,
                        "temporal_selected_jaccard": _jaccard(previous_selected_by_variant[variant], selected),
                        "temporal_category_agreement_rate": float(np.mean([previous[ticker] == current_categories[ticker] for ticker in common])) if common else np.nan,
                        "mean_equal_weight_forward_cumulative_return": np.nan,
                        "mean_equal_weight_forward_cagr": np.nan,
                    }
                )
            previous_by_variant[variant] = joined["flowsort_category"].to_dict()
            previous_selected_by_variant[variant] = selected
            previous_fold_by_variant[variant] = fold
            previous_date_by_variant[variant] = rebalance_date

            for category, group in joined.groupby("flowsort_category", sort=False):
                tickers = list(group.index.astype(str))
                ew_returns = _forward_equal_weight_returns(tickers, returns, start, end)
                clean = ew_returns.dropna()
                agreement_rows.append(
                    {
                        "comparison_scope": "flowsort_forward_returns_by_category",
                        "fold": fold,
                        "rebalance_date": rebalance_date,
                        "variant": variant,
                        "category": category,
                        "n_assets": len(tickers),
                        "category_agreement_rate": np.nan,
                        "selected_jaccard": np.nan,
                        "cohen_kappa": np.nan,
                        "temporal_selected_jaccard": np.nan,
                        "temporal_category_agreement_rate": np.nan,
                        "mean_equal_weight_forward_cumulative_return": float((1.0 + clean).prod() - 1.0) if not clean.empty else np.nan,
                        "mean_equal_weight_forward_cagr": annualized_cumulative_return(clean, periods_per_year),
                    }
                )

    return pd.DataFrame(assignment_rows), pd.DataFrame(flow_rows), pd.DataFrame(agreement_rows)


def build_report(agreement: pd.DataFrame, report_path: Path, output_dir: Path) -> None:
    agreement_summary = agreement[agreement["comparison_scope"].eq("electre_vs_flowsort_agreement")].copy()
    if not agreement_summary.empty:
        summary = (
            agreement_summary.groupby("variant")
            .agg(
                folds=("fold", "nunique"),
                mean_category_agreement=("category_agreement_rate", "mean"),
                mean_selected_jaccard=("selected_jaccard", "mean"),
                mean_cohen_kappa=("cohen_kappa", "mean"),
            )
            .reset_index()
        )
    else:
        summary = pd.DataFrame(columns=["variant", "folds", "mean_category_agreement", "mean_selected_jaccard", "mean_cohen_kappa"])

    stability = agreement[agreement["comparison_scope"].eq("temporal_stability")].copy()
    if not stability.empty:
        stability_summary = (
            stability.groupby("variant")
            .agg(
                mean_temporal_selected_jaccard=("temporal_selected_jaccard", "mean"),
                mean_temporal_category_agreement=("temporal_category_agreement_rate", "mean"),
            )
            .reset_index()
        )
    else:
        stability_summary = pd.DataFrame(columns=["variant", "mean_temporal_selected_jaccard", "mean_temporal_category_agreement"])

    forward = agreement[agreement["comparison_scope"].eq("flowsort_forward_returns_by_category")].copy()
    if not forward.empty:
        forward_summary = (
            forward.groupby(["variant", "category"])
            .agg(
                observations=("fold", "size"),
                mean_equal_weight_forward_cumulative_return=("mean_equal_weight_forward_cumulative_return", "mean"),
                mean_equal_weight_forward_cagr=("mean_equal_weight_forward_cagr", "mean"),
            )
            .reset_index()
        )
    else:
        forward_summary = pd.DataFrame(
            columns=["variant", "category", "observations", "mean_equal_weight_forward_cumulative_return", "mean_equal_weight_forward_cagr"]
        )

    for df, cols in [
        (summary, ["mean_category_agreement", "mean_selected_jaccard"]),
        (stability_summary, ["mean_temporal_selected_jaccard", "mean_temporal_category_agreement"]),
        (forward_summary, ["mean_equal_weight_forward_cumulative_return", "mean_equal_weight_forward_cagr"]),
    ]:
        for col in cols:
            if col in df.columns:
                df[col] = df[col].map(_pct)
    if "mean_cohen_kappa" in summary.columns:
        summary["mean_cohen_kappa"] = summary["mean_cohen_kappa"].map(_num)

    report = f"""# ELECTRE Tri vs FlowSort — GOAL 12

**FlowSort es clasificación multicriterio, no rebalanceo.** Este reporte compara la etapa de sorting/clasificación contra ELECTRE Tri antes de cualquier asignación de capital.

## Artefactos generados

- `{output_dir / 'flowsort_assignments.csv'}`
- `{output_dir / 'flowsort_flows.csv'}`
- `{output_dir / 'electre_vs_flowsort_agreement.csv'}`

## Variantes FlowSort evaluadas

- `usual_net_flow`: función usual + net flow.
- `v_shape_net_flow`: V-shape + net flow.
- `level_net_flow`: level + net flow.
- `v_shape_leaving_flow`: V-shape + leaving flow.

## ELECTRE vs FlowSort agreement

{_markdown_table(summary, ['variant', 'folds', 'mean_category_agreement', 'mean_selected_jaccard', 'mean_cohen_kappa'])}

## Estabilidad temporal FlowSort

{_markdown_table(stability_summary, ['variant', 'mean_temporal_selected_jaccard', 'mean_temporal_category_agreement'])}

## Forward returns por categoría FlowSort

{_markdown_table(forward_summary, ['variant', 'category', 'observations', 'mean_equal_weight_forward_cumulative_return', 'mean_equal_weight_forward_cagr'])}

## Interpretación metodológica

1. `category_agreement_rate` mide coincidencia exacta de categorías ELECTRE vs FlowSort.
2. `selected_jaccard` compara la clase superior (`above_*`) entre ambos métodos.
3. `cohen_kappa` corrige el acuerdo por coincidencia esperada al azar.
4. La estabilidad temporal mide persistencia entre folds consecutivos; baja estabilidad indica sorting sensible al tiempo.
5. Los retornos forward por categoría evalúan si las clases superiores realmente concentran mejor desempeño posterior, sin presentar FlowSort como política de rebalanceo.
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def write_flowsort_comparison(
    results_dir: Path,
    prices_path: Path,
    output_dir: Path,
    report_path: Path,
    *,
    criteria: list[Criterion] | None = None,
    profiles: list[Profile] | None = None,
) -> list[Path]:
    assignments, flows, agreement = build_flowsort_comparison(results_dir, prices_path, criteria=criteria, profiles=profiles)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        output_dir / "flowsort_assignments.csv",
        output_dir / "flowsort_flows.csv",
        output_dir / "electre_vs_flowsort_agreement.csv",
    ]
    assignments.to_csv(paths[0], index=False)
    flows.to_csv(paths[1], index=False)
    agreement.to_csv(paths[2], index=False)
    build_report(agreement, report_path, output_dir)
    return paths
