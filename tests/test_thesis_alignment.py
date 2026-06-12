from __future__ import annotations

import pandas as pd

from etf_optimizer.selection.electre_tri import Criterion, Profile
from etf_optimizer.thesis_alignment import (
    THESIS_REQUIRED_CRITERIA,
    assign_electre_by_peer_group,
    criterion_coverage,
    finalize_thesis_selection,
    infer_etf_peer_group,
    thesis_category,
    thesis_data_quality_verdict,
)


def test_thesis_category_maps_internal_electre_labels():
    assert thesis_category("above_preferred") == "excelentes"
    assert thesis_category("between_minimum_preferred") == "aceptables"
    assert thesis_category("below_minimum") == "rechazados"


def test_infer_etf_peer_group_uses_auditable_rules():
    assert infer_etf_peer_group("TLT", name="20 Year Treasury Bond ETF") == "fixed_income"
    assert infer_etf_peer_group("GLD", name="Gold Shares") == "commodities"
    assert infer_etf_peer_group("XLK", name="Technology Select Sector SPDR") == "equity_sector"
    assert infer_etf_peer_group("TQQQ", name="3x leveraged Nasdaq") == "leveraged_inverse_special"


def test_criterion_coverage_reports_missing_and_complete_criteria():
    features = pd.DataFrame(
        {
            "cagr": [0.1, 0.2],
            "volatility": [0.2, 0.3],
            "sharpe": [1.0, 0.5],
            "liquidity": [1_000_000, 2_000_000],
            "tracking_error": [0.05, 0.06],
            "expense_ratio": [0.001, 0.002],
        },
        index=["AAA", "BBB"],
    )
    coverage = criterion_coverage(features)

    assert set(coverage["criterion"]) == set(THESIS_REQUIRED_CRITERIA)
    assert set(coverage["status"]) == {"complete"}


def test_thesis_data_quality_verdict_flags_missing_criteria_and_static_universe():
    coverage = pd.DataFrame(
        [
            {"criterion": "cagr", "status": "complete"},
            {"criterion": "expense_ratio", "status": "missing"},
        ]
    )

    verdict = thesis_data_quality_verdict(
        universe_mode="static_current",
        price_source="yfinance",
        criteria_coverage_table=coverage,
    )

    assert verdict["verdict"] == "pilot_static_current_not_primary"
    assert verdict["missing_or_partial_criteria"] == ["expense_ratio"]


def test_thesis_data_quality_verdict_recognizes_regulatory_public_pit_proxy_coverage():
    coverage = pd.DataFrame(
        [
            {"criterion": "cagr", "status": "complete"},
            {"criterion": "tracking_error", "status": "proxy"},
            {"criterion": "expense_ratio", "status": "complete"},
        ]
    )

    verdict = thesis_data_quality_verdict(
        universe_mode="regulatory_enriched_pit",
        price_source="regulatory_enriched_public",
        criteria_coverage_table=coverage,
        pit_controls_passed=True,
        identifier_ambiguities=0,
    )

    assert verdict["verdict"] == "thesis_aligned_public_regulatory_pit"
    assert verdict["criteria_complete"] is True
    assert "guaranteed benchmark outperformance" in verdict["prohibited_claims"]


def test_finalize_thesis_selection_enforces_max_cardinality_and_fills_from_acceptable():
    tickers = [f"ETF{i:02d}" for i in range(30)]
    selection = pd.DataFrame(
        {
            "category": ["above_preferred"] * 12 + ["between_minimum_preferred"] * 18,
            "credibility_preferred": list(reversed(range(30))),
        },
        index=tickers,
    )

    selected = finalize_thesis_selection(selection, min_assets=10, max_assets=25)

    assert len(selected) == 25
    assert selected[0] == "ETF00"
    assert selected[-1] == "ETF24"


def test_assign_electre_by_peer_group_adds_peer_group_and_profile_scope():
    criteria = [Criterion("cagr", weight=1.0, preference_direction="max", q=0.0, p=0.01, v=0.05)]
    profiles = [Profile("minimum", {"cagr": 0.01}), Profile("preferred", {"cagr": 0.05})]
    matrix = pd.DataFrame({"cagr": [0.10, 0.08, 0.02, 0.01]}, index=["AAA", "BBB", "CCC", "DDD"])
    metadata = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB", "CCC", "DDD"],
            "peer_group": ["equity_broad", "equity_broad", "fixed_income", "fixed_income"],
        }
    )

    assigned = assign_electre_by_peer_group(
        matrix,
        criteria,
        profiles,
        metadata=metadata,
        lambda_cut=0.75,
        assignment="pessimistic",
        use_veto=True,
        backend="internal",
        min_group_size=2,
    )

    assert assigned.loc["AAA", "peer_group"] == "equity_broad"
    assert set(assigned["profile_scope"]) == {"peer_group"}
