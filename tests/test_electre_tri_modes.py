from __future__ import annotations

import pandas as pd

from etf_optimizer.selection.electre_tri import Criterion, ElectreTri, Profile


def _criteria() -> list[Criterion]:
    return [
        Criterion("return", weight=0.6, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("risk", weight=0.4, preference_direction="min", q=0.0, p=0.02, v=0.08),
    ]


def test_paper_style_three_group_assignment_uses_two_limiting_profiles():
    alternatives = pd.DataFrame(
        {
            "return": [0.14, 0.075, 0.01],
            "risk": [0.10, 0.18, 0.35],
        },
        index=["BEST", "MID", "BAD"],
    )
    profiles = [
        Profile("minimum", {"return": 0.04, "risk": 0.25}),
        Profile("preferred", {"return": 0.10, "risk": 0.14}),
    ]

    result = ElectreTri(_criteria(), profiles, lambda_cut=0.65).assign(alternatives)

    assert result.loc["BEST", "category"] == "above_preferred"
    assert result.loc["MID", "category"] == "between_minimum_preferred"
    assert result.loc["BAD", "category"] == "below_minimum"


def test_pydecision_tri_b_backend_can_be_used_as_general_library_comparator():
    alternatives = pd.DataFrame(
        {
            "return": [0.14, 0.075, 0.01],
            "risk": [0.10, 0.18, 0.35],
        },
        index=["BEST", "MID", "BAD"],
    )
    profiles = [
        Profile("minimum", {"return": 0.04, "risk": 0.25}),
        Profile("preferred", {"return": 0.10, "risk": 0.14}),
    ]

    result = ElectreTri(_criteria(), profiles, lambda_cut=0.65, backend="pydecision_tri_b").assign(alternatives)

    assert result.loc["BEST", "backend"] == "pydecision_tri_b"
    assert result.loc["BEST", "category"] == "above_preferred"
    assert result.loc["MID", "category"] == "between_minimum_preferred"
    assert result.loc["BAD", "category"] == "below_minimum"


def test_optimistic_assignment_can_promote_incomparable_assets_like_paper_variant():
    criteria = [
        Criterion("return", weight=0.5, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("risk", weight=0.5, preference_direction="min", q=0.0, p=0.02, v=0.08),
    ]
    profiles = [
        Profile("minimum", {"return": 0.04, "risk": 0.25}),
        Profile("preferred", {"return": 0.10, "risk": 0.14}),
    ]
    alternatives = pd.DataFrame({"return": [0.16], "risk": [0.22]}, index=["HIGH_RETURN_HIGH_RISK"])

    pessimistic = ElectreTri(criteria, profiles, lambda_cut=0.65, assignment="pessimistic").assign(alternatives)
    optimistic = ElectreTri(criteria, profiles, lambda_cut=0.65, assignment="optimistic").assign(alternatives)

    assert pessimistic.loc["HIGH_RETURN_HIGH_RISK", "category"] == "between_minimum_preferred"
    assert optimistic.loc["HIGH_RETURN_HIGH_RISK", "category"] == "above_preferred"
    assert optimistic.loc["HIGH_RETURN_HIGH_RISK", "assignment"] == "optimistic"


def test_veto_can_be_disabled_for_paper_variant_comparison():
    criteria = [
        Criterion("return", weight=0.8, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("expense", weight=0.2, preference_direction="min", q=0.0, p=0.002, v=0.01),
    ]
    profile = Profile("good", {"return": 0.07, "expense": 0.004})
    alternatives = pd.DataFrame({"return": [0.15], "expense": [0.03]}, index=["EXPENSIVE_WINNER"])

    with_veto = ElectreTri(criteria, [profile], lambda_cut=0.7, use_veto=True).assign(alternatives)
    without_veto = ElectreTri(criteria, [profile], lambda_cut=0.7, use_veto=False).assign(alternatives)

    assert with_veto.loc["EXPENSIVE_WINNER", "category"] == "below_good"
    assert without_veto.loc["EXPENSIVE_WINNER", "category"] == "above_good"
