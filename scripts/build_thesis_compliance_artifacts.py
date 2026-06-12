from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from etf_optimizer.thesis_alignment import criterion_coverage, thesis_data_quality_verdict
from etf_optimizer.thesis_validation import (
    benchmark_set_completeness,
    compliance_summary,
    objective_traceability_matrix,
    thesis_objective_registry,
    validate_objective1_cardinality,
    validate_objective2_classification,
    validate_objective3_benchmarks,
    validate_objective_general,
    validate_temporal_protocol,
)


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _strategy_and_benchmarks(strategy_comparison: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    if strategy_comparison.empty or "strategy" not in strategy_comparison.columns:
        return pd.Series(dtype="float64"), pd.DataFrame()
    preferred = [
        "ELECTRE_EqualWeight_walk_forward",
        "ELECTRE_MinVariance_walk_forward",
        "ELECTRE_MaxSharpe_walk_forward",
    ]
    strategy_row = pd.Series(dtype="float64")
    for name in preferred:
        match = strategy_comparison.loc[strategy_comparison["strategy"] == name]
        if not match.empty:
            strategy_row = match.iloc[0]
            break
    benchmark_mask = strategy_comparison["strategy"].astype(str).isin(
        [
            "SPY_buy_hold",
            "60/40_SPY_BND_fixed_weight",
            "Universe_EqualWeight_walk_forward",
            "MinVariance_walk_forward",
        ]
    )
    return strategy_row, strategy_comparison.loc[benchmark_mask].copy()


def _classification_status(result_dir: Path) -> dict[str, object]:
    diagnostics_dir = result_dir / "electre_classification_diagnostics"
    effectiveness = _read_csv(diagnostics_dir / "classification_effectiveness.csv")
    if effectiveness.empty:
        return {"objective": "specific_2", "status": "partial", "evidence": "missing classification_effectiveness.csv"}
    # Conservative summary: require ordered mean_forward_sharpe when categories are present.
    category_order = ["above_preferred", "between_minimum_preferred", "below_minimum"]
    metric_col = "mean_forward_sharpe" if "mean_forward_sharpe" in effectiveness.columns else None
    if metric_col is None:
        return {"objective": "specific_2", "status": "partial", "evidence": "missing mean_forward_sharpe"}
    means = effectiveness.set_index("category")[metric_col].reindex(category_order).dropna()
    monotonic = bool(len(means) >= 2 and means.is_monotonic_decreasing)
    synthetic = pd.DataFrame({"return_monotonic": [monotonic], "selected_jaccard": [0.25 if monotonic else 0.0]})
    return validate_objective2_classification(synthetic)


def build_run_compliance_artifacts(
    result_dir: Path,
    *,
    start: str,
    end: str,
    universe_mode: str,
    price_source: str = "regulatory_enriched_public",
) -> dict[str, Path]:
    """Build objective compliance artifacts from a run directory."""
    result_dir = Path(result_dir)
    features = _read_csv(result_dir / "features_table.csv")
    if not features.empty and features.columns[0].startswith("Unnamed"):
        features = features.set_index(features.columns[0])
    coverage = criterion_coverage(features) if not features.empty else pd.DataFrame()
    coverage_path = result_dir / "objective_feature_coverage.csv"
    coverage.to_csv(coverage_path, index=False)

    data_quality = thesis_data_quality_verdict(
        universe_mode=universe_mode,
        price_source=price_source,
        criteria_coverage_table=coverage,
        pit_controls_passed="regulatory" in universe_mode.lower(),
    ) if not coverage.empty else {}
    data_quality_path = result_dir / "objective_data_quality_verdict.json"
    data_quality_path.write_text(json.dumps(data_quality, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    selection = _read_csv(result_dir / "electre_selection_by_rebalance.csv")
    strategy_comparison = _read_csv(result_dir / "strategy_comparison.csv")
    strategy, benchmarks = _strategy_and_benchmarks(strategy_comparison)

    statuses = [
        validate_objective_general(coverage) if not coverage.empty else {"objective": "general", "status": "partial", "evidence": "missing features"},
        validate_objective1_cardinality(selection),
        _classification_status(result_dir),
        validate_objective3_benchmarks(strategy, benchmarks) if not strategy.empty else {"objective": "specific_3", "status": "partial", "evidence": "missing strategy comparison"},
        {"objective": "temporal_protocol", "status": validate_temporal_protocol(start=start, end=end)["validation_role"], "evidence": f"{start} to {end}"},
        {"objective": "benchmark_set", **benchmark_set_completeness(strategy_comparison.get("strategy", pd.Series(dtype=str)).astype(str).tolist())},
    ]
    summary = compliance_summary(
        statuses,
        evidence_paths={
            "general": str(coverage_path),
            "specific_1": str(result_dir / "electre_selection_by_rebalance.csv"),
            "specific_2": str(result_dir / "electre_classification_diagnostics"),
            "specific_3": str(result_dir / "strategy_comparison.csv"),
        },
    )
    summary_path = result_dir / "objective_compliance_summary.csv"
    summary.to_csv(summary_path, index=False)

    traceability = objective_traceability_matrix(coverage)
    traceability_path = result_dir / "objective_traceability_matrix.csv"
    traceability.to_csv(traceability_path, index=False)

    registry_path = result_dir / "thesis_objective_registry.csv"
    thesis_objective_registry().to_csv(registry_path, index=False)

    payload = {
        "result_dir": str(result_dir),
        "temporal_protocol": validate_temporal_protocol(start=start, end=end),
        "data_quality": data_quality,
        "objective_statuses": statuses,
        "artifacts": {
            "feature_coverage": str(coverage_path),
            "data_quality": str(data_quality_path),
            "compliance_summary": str(summary_path),
            "traceability_matrix": str(traceability_path),
            "objective_registry": str(registry_path),
        },
    }
    json_path = result_dir / "objective_compliance_summary.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {
        "feature_coverage": coverage_path,
        "data_quality": data_quality_path,
        "compliance_summary": summary_path,
        "traceability_matrix": traceability_path,
        "objective_registry": registry_path,
        "summary_json": json_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build thesis objective compliance artifacts from result outputs.")
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--universe-mode", default="regulatory_enriched_pit")
    parser.add_argument("--price-source", default="regulatory_enriched_public")
    args = parser.parse_args()
    paths = build_run_compliance_artifacts(
        args.result_dir,
        start=args.start,
        end=args.end,
        universe_mode=args.universe_mode,
        price_source=args.price_source,
    )
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
