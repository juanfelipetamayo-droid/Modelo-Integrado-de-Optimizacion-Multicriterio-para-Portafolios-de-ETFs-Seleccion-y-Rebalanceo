from __future__ import annotations

import numpy as np
import pandas as pd

from etf_optimizer.selection.electre_tri import ElectreTri, Criterion, Profile


def test_electre_tri_classifies_asset_above_reference_profile():
    criteria = [
        Criterion("return", weight=0.6, preference_direction="max", q=0.00, p=0.02, v=0.05),
        Criterion("risk", weight=0.4, preference_direction="min", q=0.00, p=0.03, v=0.08),
    ]
    profiles = [Profile("acceptable", {"return": 0.05, "risk": 0.20})]
    model = ElectreTri(criteria=criteria, profiles=profiles, lambda_cut=0.65)
    alternatives = pd.DataFrame({"return": [0.08, 0.02], "risk": [0.15, 0.35]}, index=["GOOD", "BAD"])

    result = model.assign(alternatives)

    assert result.loc["GOOD", "category"] == "above_acceptable"
    assert result.loc["BAD", "category"] == "below_acceptable"
    assert result.loc["GOOD", "credibility_acceptable"] > result.loc["BAD", "credibility_acceptable"]


def test_electre_tri_veto_reduces_credibility():
    criteria = [
        Criterion("return", weight=0.5, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("expense", weight=0.5, preference_direction="min", q=0.0, p=0.002, v=0.01),
    ]
    model = ElectreTri(criteria, [Profile("good", {"return": 0.07, "expense": 0.004})], lambda_cut=0.7)
    high_return_high_fee = pd.Series({"return": 0.15, "expense": 0.03})
    credibility = model.credibility(high_return_high_fee, model.profiles[0])
    assert credibility < 0.7
    assert np.isfinite(credibility)
