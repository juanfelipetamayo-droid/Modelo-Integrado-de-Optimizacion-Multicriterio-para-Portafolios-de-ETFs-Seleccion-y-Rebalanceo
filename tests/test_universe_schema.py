from __future__ import annotations

import pandas as pd

from etf_optimizer.data.schema import (
    CANONICAL_COLUMNS,
    REQUIRED_COLUMNS,
    KNOWN_SOURCES,
    validate_universe_schema,
    normalize_ticker,
    normalize_tickers,
    make_fund_id,
    convert_dates,
)


def test_canonical_columns_defined():
    assert len(CANONICAL_COLUMNS) >= 15
    assert "fund_id" in CANONICAL_COLUMNS
    assert "ticker" in CANONICAL_COLUMNS
    assert "source" in CANONICAL_COLUMNS
    assert "active_flag" in CANONICAL_COLUMNS


def test_required_columns_subset_of_canonical():
    for col in REQUIRED_COLUMNS:
        assert col in CANONICAL_COLUMNS


def test_known_sources():
    assert "sec" in KNOWN_SOURCES
    assert "nasdaq" in KNOWN_SOURCES
    assert "manual" in KNOWN_SOURCES


def test_validate_universe_schema_valid():
    df = pd.DataFrame({
        "fund_id": ["SPY", "IVV"],
        "ticker": ["SPY", "IVV"],
        "source": ["nasdaq", "sec"],
        "active_flag": [True, True],
    })
    issues = validate_universe_schema(df)
    assert len(issues["missing_required"]) == 0
    assert len(issues["invalid_sources"]) == 0


def test_validate_universe_schema_missing_required():
    df = pd.DataFrame({"ticker": ["SPY"]})
    issues = validate_universe_schema(df)
    assert "fund_id" in issues["missing_required"]
    assert "source" in issues["missing_required"]


def test_validate_universe_schema_duplicates():
    df = pd.DataFrame({
        "fund_id": ["SPY", "SPY"],
        "ticker": ["SPY", "SPY"],
        "source": ["nasdaq", "nasdaq"],
        "active_flag": [True, True],
    })
    issues = validate_universe_schema(df)
    assert "SPY" in issues["duplicate_fund_ids"]


def test_normalize_ticker():
    assert normalize_ticker(" spy ") == "SPY"
    assert normalize_ticker("QQQ") == "QQQ"


def test_normalize_tickers_dataframe():
    df = pd.DataFrame({"ticker": [" spy ", "  IVV  ", "QQQ"]})
    result = normalize_tickers(df)
    assert result["ticker"].tolist() == ["SPY", "IVV", "QQQ"]


def test_make_fund_id_from_ticker():
    row = pd.Series({"ticker": "SPY", "cik": ""})
    assert make_fund_id(row) == "SPY"


def test_make_fund_id_from_cik():
    row = pd.Series({"ticker": None, "cik": "1234567890"})
    assert make_fund_id(row) == "CIK_1234567890"


def test_make_fund_id_unknown():
    row = pd.Series({"ticker": "", "cik": ""})
    fid = make_fund_id(row)
    assert fid.startswith("unknown_")


def test_convert_dates():
    df = pd.DataFrame({
        "inception_date": ["2020-01-01", "invalid"],
        "ticker": ["A", "B"],
    })
    result = convert_dates(df)
    assert result["inception_date"].iloc[0] is not None
    assert pd.isna(result["inception_date"].iloc[1])


def test_validate_schema_invalid_source():
    df = pd.DataFrame({
        "fund_id": ["X"],
        "ticker": ["X"],
        "source": ["unknown_source"],
        "active_flag": [True],
    })
    issues = validate_universe_schema(df)
    assert len(issues["invalid_sources"]) > 0
