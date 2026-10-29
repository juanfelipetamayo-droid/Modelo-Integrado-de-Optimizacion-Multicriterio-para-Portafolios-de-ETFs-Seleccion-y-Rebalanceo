from __future__ import annotations

import pandas as pd
import pytest

from etf_optimizer.optimization.exposure import (
    apply_group_exposure_cap,
    category_exposure_table,
    classify_etf_risk_bucket,
)


def test_classify_etf_risk_bucket_flags_commodity_and_theme_names():
    assert classify_etf_risk_bucket("CORN", "Teucrium Corn Fund") == "commodities"
    assert classify_etf_risk_bucket("CNXT", "VanEck ChiNext Innovators ETF") == "greater_china"
    assert classify_etf_risk_bucket("CARZ", "First Trust Future Vehicles & Technology ETF") == "thematic"
    assert classify_etf_risk_bucket("SPY", "SPDR S&P 500 ETF Trust") == "broad_equity"


def test_apply_group_exposure_cap_reduces_dominant_category_and_preserves_full_investment():
    weights = pd.Series({"CORN": 0.50, "CANE": 0.20, "SPY": 0.20, "BND": 0.10})
    metadata = pd.DataFrame(
        {
            "ticker": ["CORN", "CANE", "SPY", "BND"],
            "name": ["Teucrium Corn Fund", "Teucrium Sugar Fund", "SPDR S&P 500 ETF", "Vanguard Total Bond Market ETF"],
        }
    )

    capped = apply_group_exposure_cap(weights, metadata, cap=0.35)
    exposure = category_exposure_table(capped, metadata)

    commodity_weight = exposure.loc[exposure["risk_bucket"] == "commodities", "weight"].iloc[0]

    assert capped.sum() == pytest.approx(1.0)
    assert commodity_weight <= 0.35 + 1e-12
    assert capped.loc["SPY"] > weights.loc["SPY"]
    assert capped.loc["BND"] > weights.loc["BND"]


def test_apply_group_exposure_cap_rejects_infeasible_caps():
    weights = pd.Series({"CORN": 0.6, "SPY": 0.4})
    metadata = pd.DataFrame({"ticker": ["CORN", "SPY"], "name": ["Corn Fund", "S&P 500 ETF"]})

    with pytest.raises(ValueError, match="infeasible"):
        apply_group_exposure_cap(weights, metadata, cap=0.40)
