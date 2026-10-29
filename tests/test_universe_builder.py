from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.data.universe_builder import (
    merge_universe_sources,
    enrich_universe_with_sec_metadata,
    generate_coverage_report,
    write_universe_snapshot,
)


def test_merge_universe_sources_empty():
    result = merge_universe_sources([])
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_merge_universe_sources_single():
    df1 = pd.DataFrame({
        "fund_id": ["SPY", "IVV"],
        "ticker": ["SPY", "IVV"],
        "source": ["nasdaq", "nasdaq"],
        "active_flag": [True, True],
    })
    result = merge_universe_sources([df1])
    assert len(result) == 2
    assert result["fund_id"].tolist() == ["SPY", "IVV"]


def test_merge_universe_sources_dedup():
    df1 = pd.DataFrame({
        "fund_id": ["SPY", "IVV"],
        "ticker": ["SPY", "IVV"],
        "source": ["nasdaq", "nasdaq"],
        "active_flag": [True, True],
    })
    df2 = pd.DataFrame({
        "fund_id": ["SPY", "QQQ"],
        "ticker": ["SPY", "QQQ"],
        "source": ["manual", "manual"],
        "active_flag": [True, True],
    })
    result = merge_universe_sources([df1, df2])
    assert len(result) == 3
    assert "QQQ" in result["fund_id"].values


def test_enrich_universe_with_sec_metadata_does_not_expand_membership():
    universe = pd.DataFrame({
        "fund_id": ["SPY"],
        "ticker": ["SPY"],
        "source": ["nasdaq"],
        "active_flag": [True],
    })
    sec = pd.DataFrame({
        "fund_id": ["SPY", "AAPL"],
        "ticker": ["SPY", "AAPL"],
        "cik": ["0000078462", "0000320193"],
        "exchange": ["NYSE Arca", "Nasdaq"],
        "source_url": ["sec-url", "sec-url"],
        "source": ["sec", "sec"],
        "active_flag": [True, True],
    })
    result = enrich_universe_with_sec_metadata(universe, sec)
    assert result["ticker"].tolist() == ["SPY"]
    assert result.loc[0, "cik"] == "0000078462"
    assert result.loc[0, "exchange"] == "NYSE Arca"


def test_merge_universe_sources_missing_fund_id():
    df = pd.DataFrame({
        "ticker": ["SPY", "IVV"],
        "source": ["nasdaq", "nasdaq"],
        "active_flag": [True, True],
    })
    result = merge_universe_sources([df])
    assert len(result) == 2
    assert result["fund_id"].notna().all()


def test_generate_coverage_report():
    df = pd.DataFrame({
        "fund_id": ["A", "B", "C"],
        "ticker": ["A", "B", "C"],
        "source": ["nasdaq", "sec", "nasdaq"],
        "active_flag": [True, False, True],
        "name": ["Fund A", None, "Fund C"],
    })
    report = generate_coverage_report(df)
    assert isinstance(report, pd.DataFrame)
    metrics = report["metric"].tolist()
    assert "total_funds" in metrics
    assert "source_nasdaq" in metrics
    assert "source_sec" in metrics
    assert "active" in metrics
    assert "name_present" in metrics


def test_generate_coverage_report_empty():
    report = generate_coverage_report(pd.DataFrame())
    assert isinstance(report, pd.DataFrame)
    assert report.iloc[0]["count"] == 0


def test_write_universe_snapshot(tmp_path: Path):
    df = pd.DataFrame({
        "fund_id": ["SPY"],
        "ticker": ["SPY"],
        "source": ["nasdaq"],
        "active_flag": [True],
    })
    paths = write_universe_snapshot(df, str(tmp_path))
    assert paths["raw"].exists()
    assert paths["clean"].exists()
    assert paths["coverage"].exists()
    raw = pd.read_csv(paths["raw"])
    assert len(raw) == 1
