from __future__ import annotations

from pathlib import Path

from etf_optimizer.criteria_config import load_criteria_config


REQUIRED_FIELDS = {
    "criterion_name",
    "formula",
    "lookback_window",
    "orientation",
    "is_hard_filter",
    "missing_data_rule",
    "winsorization_rule",
    "normalization_rule",
    "source",
}


EXPECTED_HARD_FILTERS = {
    "exclude_leveraged_etfs",
    "exclude_inverse_etfs",
    "exclude_etns",
    "minimum_history_months",
    "minimum_avg_dollar_volume",
    "minimum_aum_usd",
    "maximum_expense_ratio",
    "minimum_price_usd",
    "minimum_price_coverage_pct",
}


EXPECTED_MCDM_CRITERIA = {
    "momentum_12_1",
    "volatility_annualized",
    "rolling_max_drawdown",
    "rolling_sortino",
    "avg_dollar_volume",
    "expense_ratio",
    "tracking_error_vs_category_benchmark",
    "beta_vs_category_benchmark",
    "marginal_correlation_to_selected_universe",
    "fund_age_months",
    "aum_usd",
}


def test_default_criteria_config_exists_with_required_schema() -> None:
    config_path = Path("configs/criteria_config.yaml")

    specs = load_criteria_config(config_path)

    assert config_path.exists()
    assert specs
    for spec in specs:
        row = spec.to_dict()
        assert REQUIRED_FIELDS <= row.keys()
        assert row["orientation"] in {"maximize", "minimize"}
        assert isinstance(row["is_hard_filter"], bool)
        assert row["criterion_name"]
        assert row["formula"]
        assert row["missing_data_rule"]
        assert row["winsorization_rule"]
        assert row["normalization_rule"]
        assert row["source"]


def test_hard_filters_are_separate_from_mcdm_criteria() -> None:
    specs = load_criteria_config("configs/criteria_config.yaml")
    hard_filters = {spec.criterion_name for spec in specs if spec.is_hard_filter}
    mcdm_criteria = {spec.criterion_name for spec in specs if not spec.is_hard_filter}

    assert EXPECTED_HARD_FILTERS <= hard_filters
    assert EXPECTED_MCDM_CRITERIA <= mcdm_criteria
    assert hard_filters.isdisjoint(mcdm_criteria)


def test_cagr_is_not_a_dominant_mcdm_criterion() -> None:
    specs = load_criteria_config("configs/criteria_config.yaml")
    mcdm_names = [spec.criterion_name for spec in specs if not spec.is_hard_filter]

    assert "cagr" not in mcdm_names
    assert "historical_cagr" not in mcdm_names
