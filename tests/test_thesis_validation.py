from __future__ import annotations

import pandas as pd

from etf_optimizer.thesis_validation import (
    OPERATIONAL_OBJECTIVE_3,
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


def test_objective_registry_renders_realistic_objective_3():
    registry = thesis_objective_registry()
    objective3 = registry.set_index("objective").loc["specific_3"]

    assert objective3["operational_wording"] == OPERATIONAL_OBJECTIVE_3
    assert objective3["operational_wording"].startswith("Desarrollar e implementar")
    assert "evaluar empíricamente" in objective3["operational_wording"]


def test_traceability_matrix_marks_complete_and_proxy_criteria():
    coverage = pd.DataFrame(
        [
            {"criterion": "cagr", "status": "complete"},
            {"criterion": "tracking_error", "status": "proxy"},
            {"criterion": "expense_ratio", "status": "missing"},
        ]
    )

    matrix = objective_traceability_matrix(coverage)

    assert {"objective", "criterion", "primary_source", "fallback", "coverage_status"}.issubset(matrix.columns)
    assert matrix.loc[matrix["criterion"] == "tracking error", "coverage_status"].item() == "proxy"
    assert matrix.loc[matrix["criterion"] == "expense ratio", "coverage_status"].item() == "missing"


def test_validate_objective_general_requires_all_six_criteria():
    coverage = pd.DataFrame(
        [
            {"criterion": "cagr", "status": "complete"},
            {"criterion": "volatility", "status": "complete"},
            {"criterion": "sharpe", "status": "complete"},
            {"criterion": "liquidity", "status": "complete"},
            {"criterion": "tracking_error", "status": "proxy"},
            {"criterion": "expense_ratio", "status": "complete"},
        ]
    )

    status = validate_objective_general(coverage)

    assert status["status"] == "near-fulfilled"
    assert status["missing_or_partial_criteria"] == []


def test_validate_objective1_cardinality_reports_violating_rebalances():
    selection = pd.DataFrame(
        {
            "rebalance_date": ["2025-01-31"] * 9 + ["2025-04-30"] * 10,
            "ticker": [f"ETF{i}" for i in range(19)],
            "selected": [True] * 19,
        }
    )

    status = validate_objective1_cardinality(selection, min_assets=10, max_assets=25)

    assert status["status"] == "not fulfilled operationally"
    assert status["violating_dates"] == ["2025-01-31"]
    assert status["aggregate_unique_selected"] == 19


def test_validate_temporal_protocol_separates_principal_and_extended():
    assert validate_temporal_protocol(start="2021-01-01", end="2025-12-31")["validation_role"] == "thesis_aligned_principal"
    assert validate_temporal_protocol(start="2015-01-01", end="2025-12-31")["validation_role"] == "extended_robustness_not_replacement"


def test_validate_objective2_classification_marks_partial_when_unstable():
    diagnostics = pd.DataFrame({"return_monotonic": [True], "selected_jaccard": [0.0]})

    status = validate_objective2_classification(diagnostics)

    assert status["status"] == "partial"
    assert status["monotonic_ok"] is True
    assert status["stable_ok"] is False


def test_validate_objective3_preserves_negative_result_reporting():
    strategy = {"cagr": 0.05, "sharpe": 0.5, "sortino": 0.7, "max_drawdown": -0.20, "volatility": 0.18}
    benchmarks = pd.DataFrame(
        [
            {"strategy": "SPY", "cagr": 0.12, "sharpe": 1.0, "sortino": 1.2, "max_drawdown": -0.10, "volatility": 0.15},
            {"strategy": "60/40", "cagr": 0.08, "sharpe": 0.9, "sortino": 1.0, "max_drawdown": -0.08, "volatility": 0.10},
        ]
    )

    status = validate_objective3_benchmarks(strategy, benchmarks)

    assert status["status"] == "not empirically validated"
    assert status["metric_comparisons"]["sharpe"] is False


def test_benchmark_set_completeness_requires_spy_6040_and_universe_baseline():
    partial = benchmark_set_completeness(["SPY_buy_hold"])
    complete = benchmark_set_completeness(
        ["SPY_buy_hold", "60/40_SPY_BND_fixed_weight", "Universe_EqualWeight_walk_forward"]
    )

    assert partial["status"] == "partial"
    assert "60/40_SPY_BND_fixed_weight" in partial["missing_benchmarks"]
    assert complete["status"] == "complete"


def test_compliance_summary_lists_evidence_and_blocking_gaps():
    summary = compliance_summary(
        [
            {"objective": "general", "status": "near-fulfilled", "missing_or_partial_criteria": []},
            {"objective": "specific_3", "status": "not empirically validated", "evidence": "SPY dominated"},
        ],
        evidence_paths={"general": "feature_coverage.csv"},
    )

    assert summary.loc[summary["objective"] == "general", "evidence"].item() == "feature_coverage.csv"
    assert summary.loc[summary["objective"] == "specific_3", "blocking_gaps"].item() == "SPY dominated"
