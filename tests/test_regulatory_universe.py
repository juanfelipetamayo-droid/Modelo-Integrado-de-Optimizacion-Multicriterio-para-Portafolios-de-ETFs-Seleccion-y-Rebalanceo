from __future__ import annotations

import numpy as np
import pandas as pd

from etf_optimizer.data.regulatory_universe import (
    BENCHMARK_TYPES,
    SOURCE_ALLOWED_USES,
    build_benchmark_map,
    build_electre_features_pit,
    build_filing_index,
    build_fund_snapshots,
    build_holdings_snapshots,
    build_identifier_mappings,
    build_security_master,
    compute_tracking_error_with_mapping,
    criteria_coverage_from_pit_features,
    default_source_registry,
    detect_identifier_ambiguities,
    is_pit_eligible,
    liquidity_metrics,
    normalize_price_history,
    regulatory_data_quality_verdict,
    stable_security_id,
    validate_snapshot_dates,
    validate_source_registry,
)


def test_default_source_registry_contains_tier1_sources_and_policy_values():
    registry = default_source_registry()

    assert validate_source_registry(registry) == []
    assert {"sec_nport", "sec_ncen", "sec_edgar_submissions", "openfigi"}.issubset(set(registry["source_id"]))
    assert set(registry["allowed_use"]).issubset(set(SOURCE_ALLOWED_USES))
    assert registry.loc[registry["source_id"] == "sec_nport", "source_type"].item() == "regulatory"
    assert "User-Agent" in registry.loc[registry["source_id"] == "sec_edgar_submissions", "rate_limit_policy"].item()


def test_stable_security_id_prefers_regulatory_identifiers_over_ticker():
    with_reg = stable_security_id({"ticker": "SPY", "cik": "884394", "series_id": "S1", "class_id": "C1"})
    with_different_ticker = stable_security_id({"ticker": "OLD", "cik": "884394", "series_id": "S1", "class_id": "C1"})
    ticker_fallback = stable_security_id({"ticker": "SPY", "issuer": "SPDR"})

    assert with_reg == with_different_ticker
    assert not with_reg.startswith("ETF-UNVERIFIED")
    assert ticker_fallback.startswith("ETF-UNVERIFIED")


def test_security_master_mappings_and_ambiguity_flags():
    records = pd.DataFrame(
        [
            {"ticker": "AAA", "cik": "1", "series_id": "S1", "class_id": "C1", "fund_name": "A ETF"},
            {"ticker": "AAA", "cik": "2", "series_id": "S2", "class_id": "C2", "fund_name": "B ETF"},
            {"ticker": "BBB", "issuer": "Issuer Only"},
        ]
    )

    master = build_security_master(records)
    mappings = build_identifier_mappings(master)
    ambiguities = detect_identifier_ambiguities(mappings)

    assert "security_id" in master.columns
    assert master.loc[master["ticker"] == "BBB", "identity_qc_flags"].str.contains("ticker_not_durable_identity").any()
    assert "AAA" in set(ambiguities["identifier_value"])
    assert "identifier_maps_to_multiple_security_ids" in set(ambiguities["ambiguity_flag"])


def test_filing_index_preserves_amendments_and_public_dates():
    raw = pd.DataFrame(
        [
            {"cik": 123, "accessionNumber": "0001", "form": "NPORT-P", "reportDate": "2021-03-31", "filingDate": "2021-05-30"},
            {"cik": 123, "accessionNumber": "0002", "form": "NPORT-P/A", "reportDate": "2021-03-31", "filingDate": "2021-06-15", "amends_accession": "0001"},
        ]
    )

    index = build_filing_index(raw)

    assert index["public_available_date"].notna().all()
    assert index.loc[index["accession_number"] == "0002", "is_amendment"].item() is True
    assert set(index["accession_number"]) == {"0001", "0002"}


def test_fund_and_holdings_snapshots_preserve_availability_dates_and_flags():
    fund = build_fund_snapshots(
        pd.DataFrame(
            [
                {
                    "security_id": "ETF1",
                    "filing_id": "F1",
                    "as_of_date": "2021-03-31",
                    "filed_date": "2021-05-30",
                    "aum_or_net_assets": 100_000_000,
                    "benchmark_name": "S&P 500",
                }
            ]
        )
    )
    holdings = build_holdings_snapshots(
        pd.DataFrame(
            [
                {
                    "security_id": "ETF1",
                    "filing_id": "F1",
                    "as_of_date": "2021-03-31",
                    "public_available_date": "2021-05-30",
                    "holding_name": "AAPL",
                    "weight": 0.07,
                }
            ]
        )
    )

    assert validate_snapshot_dates(fund) == []
    assert "missing_expense_ratio" in fund.loc[0, "snapshot_qc_flags"]
    assert holdings.loc[0, "holding_id"]
    assert holdings.loc[0, "holding_qc_flags"] == ""


def test_price_history_and_liquidity_metrics_flag_missing_volume_and_extreme_moves():
    prices = pd.DataFrame({"AAA": [10.0, 11.0, 30.0]}, index=pd.date_range("2021-01-01", periods=3))
    volume = pd.DataFrame({"AAA": [100, np.nan, 100]}, index=prices.index)
    master = build_security_master(pd.DataFrame([{"ticker": "AAA", "cik": "1", "series_id": "S", "class_id": "C"}]))

    history = normalize_price_history(prices, volume=volume, security_master=master, retrieved_at="2021-01-04")
    liquidity = liquidity_metrics(history)

    assert set(["adjusted_close", "volume", "source_id"]).issubset(history.columns)
    assert history["price_qc_flags"].str.contains("missing_volume").any()
    assert liquidity.loc[0, "valid_trading_days"] == 3
    assert "extreme_price_move_check_adjustments" in liquidity.loc[0, "price_qc_flags"]


def test_benchmark_map_and_tracking_error_label_proxy_vs_official():
    mapping = build_benchmark_map(
        pd.DataFrame(
            [
                {"security_id": "ETF1", "benchmark_name": "S&P 500", "benchmark_type": "official"},
                {"security_id": "ETF2", "benchmark_name": "Category Proxy", "benchmark_type": "inferred"},
            ]
        )
    )

    result = compute_tracking_error_with_mapping(
        pd.Series([0.01, 0.02, -0.01]),
        pd.Series([0.00, 0.01, -0.02]),
        mapping.iloc[1],
        periods_per_year=12,
    )

    assert set(mapping["benchmark_type"]).issubset(set(BENCHMARK_TYPES))
    assert result["fallback_level"] == "proxy"
    assert result["tracking_error_label"] == "inferred"


def test_pit_feature_eligibility_excludes_post_date_data():
    assert is_pit_eligible(
        measurement_date="2021-03-31",
        public_available_date="2021-05-01",
        decision_date="2021-06-01",
    )
    assert not is_pit_eligible(
        measurement_date="2021-03-31",
        public_available_date="2021-07-01",
        decision_date="2021-06-01",
    )


def test_electre_features_pit_records_source_fallback_and_coverage_status():
    values = pd.DataFrame({"cagr": [0.1], "tracking_error": [0.03]}, index=["ETF1"])
    features = build_electre_features_pit(
        values,
        decision_date="2021-06-01",
        source_date="2021-03-31",
        public_available_date="2021-05-01",
        fallback_level="proxy",
    )
    coverage = criteria_coverage_from_pit_features(features, ["cagr", "tracking_error", "expense_ratio"])

    assert features["qc_flags"].eq("").all()
    assert set(features["fallback_level"]) == {"proxy"}
    assert coverage.set_index("criterion").loc["tracking_error", "status"] == "proxy"
    assert coverage.set_index("criterion").loc["expense_ratio", "status"] == "missing"


def test_regulatory_data_quality_verdict_allows_only_public_regulatory_claims():
    coverage = pd.DataFrame(
        [
            {"criterion": "cagr", "status": "complete"},
            {"criterion": "tracking_error", "status": "proxy"},
            {"criterion": "expense_ratio", "status": "complete"},
        ]
    )

    verdict = regulatory_data_quality_verdict(
        universe_mode="regulatory_enriched_pit",
        criteria_coverage_table=coverage,
        pit_controls_passed=True,
        identifier_ambiguities=0,
    )

    assert verdict["verdict"] == "thesis_aligned_public_regulatory_pit"
    assert verdict["survivorship_bias_free"] is False
    assert "institutional survivorship-bias-free" in verdict["prohibited_claims"]
