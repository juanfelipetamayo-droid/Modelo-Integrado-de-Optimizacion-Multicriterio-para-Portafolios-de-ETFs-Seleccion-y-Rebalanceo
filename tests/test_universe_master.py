from __future__ import annotations

import pandas as pd

from etf_optimizer.data.universe_master import (
    build_fund_master,
    build_rebalance_snapshot,
    build_ticker_history,
    month_start_dates,
    sec_snapshot_to_listings,
)


def _sample_listing_observations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fund_id": ["SPY", "NEW", "OLD"],
            "ticker": ["SPY", "NEW", "OLD"],
            "ticker_start_date": ["2015-01-01", "2016-01-01", "2015-01-01"],
            "ticker_end_date": ["2016-12-31", "2016-12-31", "2015-12-31"],
            "cik": ["0000078462", "0000000002", "0000000003"],
            "series_id": ["S1", "S2", "S3"],
            "class_id": ["C1", "C2", "C3"],
            "fund_name": ["SPDR S&P 500 ETF", "New ETF", "Old ETF"],
            "issuer": ["SPDR", None, None],
            "exchange": ["NYSE Arca", "NYSE Arca", "NYSE Arca"],
            "asset_class_bucket": ["equity_or_multi_asset", "equity_or_multi_asset", "equity_or_multi_asset"],
            "inception_date": [pd.NaT, pd.NaT, pd.NaT],
            "termination_date": [pd.NaT, pd.NaT, pd.NaT],
            "delisted_date": [pd.NaT, pd.NaT, pd.NaT],
            "expense_ratio": [pd.NA, pd.NA, pd.NA],
            "aum": [pd.NA, pd.NA, pd.NA],
            "avg_dollar_volume": [pd.NA, pd.NA, pd.NA],
            "source": ["sec_series_class"] * 3,
            "source_filing_date": [pd.NaT, pd.NaT, pd.NaT],
            "source_acceptance_date": [pd.NaT, pd.NaT, pd.NaT],
            "source_available_date": ["2015-01-01", "2016-01-01", "2015-01-01"],
            "data_quality_flag": ["public_approximate_pit_sec_series_class_annual_snapshot"] * 3,
            "observation_start_date": ["2015-01-01", "2016-01-01", "2015-01-01"],
            "observation_end_date": ["2016-12-31", "2016-12-31", "2015-12-31"],
            "source_year": [2015, 2016, 2015],
            "source_url": ["sec"] * 3,
        }
    )


def test_sec_snapshot_to_listings_adds_goal_2_required_pit_fields():
    snapshot = pd.DataFrame(
        {
            "fund_id": ["SPY"],
            "ticker": ["spy"],
            "name": ["SPDR S&P 500 ETF"],
            "cik": ["0000078462"],
            "series_id": ["S1"],
            "class_id": ["C1"],
            "exchange": ["NYSE Arca"],
            "source_url": ["https://www.sec.gov/example.csv"],
        }
    )

    listings = sec_snapshot_to_listings(snapshot, 2015)
    row = listings.iloc[0]

    assert row["ticker"] == "SPY"
    assert row["source_available_date"] == pd.Timestamp("2015-01-01")
    assert pd.isna(row["source_filing_date"])
    assert row["data_quality_flag"] == "public_approximate_pit_sec_series_class_annual_snapshot"
    assert row["asset_class_bucket"] == "equity_or_multi_asset"


def test_rebalance_snapshot_enforces_source_available_date_before_rebalance_date():
    listings = _sample_listing_observations()

    snap_2015 = build_rebalance_snapshot(listings, "2015-12-01")
    snap_2016 = build_rebalance_snapshot(listings, "2016-01-01")

    assert set(snap_2015["ticker"]) == {"SPY", "OLD"}
    assert "NEW" not in snap_2015["ticker"].tolist()
    assert set(snap_2016["ticker"]) == {"SPY", "NEW"}
    assert (pd.to_datetime(snap_2016["source_available_date"]) <= pd.Timestamp("2016-01-01")).all()
    assert "data_quality_flag" in snap_2016.columns


def test_fund_master_and_ticker_history_have_minimum_fields():
    listings = _sample_listing_observations()
    fund_master = build_fund_master(listings)
    ticker_history = build_ticker_history(listings)

    for col in ["fund_id", "ticker", "cik", "series_id", "class_id", "source_available_date", "data_quality_flag"]:
        assert col in fund_master.columns
    assert set(ticker_history.columns) >= {"fund_id", "ticker", "ticker_start_date", "ticker_end_date"}


def test_month_start_dates_covers_2015_01_through_2025_12():
    dates = month_start_dates("2015-01-01", "2025-12-01")

    assert dates[0] == pd.Timestamp("2015-01-01")
    assert dates[-1] == pd.Timestamp("2025-12-01")
    assert len(dates) == 132
