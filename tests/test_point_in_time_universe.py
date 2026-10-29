from __future__ import annotations

import pandas as pd

from etf_optimizer.data.sec_universe import (
    PointInTimeETFUniverseProvider,
    build_point_in_time_master,
    load_sec_series_class_snapshot,
)


def test_load_sec_series_class_snapshot_filters_etf_candidates_and_preserves_ids(tmp_path):
    csv_path = tmp_path / "investment_company_series_class_2018.csv"
    csv_path.write_text(
        "rep_file_num,CIK,entity_name,entity_org_type,series_id,series_name,class_id,class_name,class_ticker_symbol\n"
        "811-00001,78462,SPDR TRUST,UIT,S000001,SPDR S&P 500 ETF TRUST,C000001,SPDR S&P 500 ETF,spy\n"
        "811-00002,99999,ABC MUTUAL FUND,MF,S000002,ABC INCOME FUND,C000002,ABC Class A,abcax\n",
        encoding="utf-8",
    )

    df = load_sec_series_class_snapshot(csv_path, year=2018)

    assert df["ticker"].tolist() == ["SPY"]
    row = df.iloc[0]
    assert row["cik"] == "0000078462"
    assert row["series_id"] == "S000001"
    assert row["class_id"] == "C000001"
    assert row["source"] == "sec"
    assert row["source_year"] == 2018
    assert row["first_seen_date"] == pd.Timestamp("2018-01-01")
    assert row["last_seen_date"] == pd.Timestamp("2018-12-31")
    assert bool(row["is_etf_candidate"])


def test_load_sec_series_class_snapshot_supports_newer_title_case_headers(tmp_path):
    csv_path = tmp_path / "investment_company_series_class_2022.csv"
    csv_path.write_text(
        "Reporting File Number,CIK Number,Entity Name,Entity Org Type,Series ID,Series Name,Class ID,Class Name,Class Ticker\n"
        "811-00003,0001100663,iShares Trust,30,S000010,ISHARES CORE ETF,C000010,iShares Core ETF,core\n",
        encoding="utf-8",
    )

    df = load_sec_series_class_snapshot(csv_path, year=2022)

    assert df["ticker"].tolist() == ["CORE"]
    row = df.iloc[0]
    assert row["cik"] == "0001100663"
    assert row["series_id"] == "S000010"
    assert row["class_id"] == "C000010"
    assert row["source_year"] == 2022


def test_point_in_time_provider_adds_new_etfs_only_after_observable_date():
    master = build_point_in_time_master(
        [
            pd.DataFrame(
                {
                    "ticker": ["SPY", "OLD"],
                    "fund_id": ["SPY", "OLD"],
                    "first_seen_date": ["2018-01-01", "2018-01-01"],
                    "last_seen_date": ["2018-12-31", "2018-12-31"],
                    "inception_date": ["1993-01-22", "2017-06-01"],
                    "termination_date": [None, None],
                    "source": ["sec", "sec"],
                    "active_flag": [True, True],
                    "is_etf_candidate": [True, True],
                }
            ),
            pd.DataFrame(
                {
                    "ticker": ["SPY", "NEW"],
                    "fund_id": ["SPY", "NEW"],
                    "first_seen_date": ["2019-01-01", "2019-01-01"],
                    "last_seen_date": ["2019-12-31", "2019-12-31"],
                    "inception_date": ["1993-01-22", "2019-06-15"],
                    "termination_date": [None, None],
                    "source": ["sec", "sec"],
                    "active_flag": [True, True],
                    "is_etf_candidate": [True, True],
                }
            ),
        ]
    )
    provider = PointInTimeETFUniverseProvider(master)

    in_2018 = provider.constituents_as_of("2018-09-30", min_age_months=0)
    in_2019_before_age = provider.constituents_as_of("2019-09-30", min_age_months=6)
    end_2019 = provider.constituents_as_of("2019-12-31", min_age_months=6)

    assert in_2018["ticker"].tolist() == ["OLD", "SPY"]
    assert "NEW" not in in_2019_before_age["ticker"].tolist()
    assert set(end_2019["ticker"]) == {"NEW", "SPY"}
    assert "OLD" not in end_2019["ticker"].tolist()


def test_point_in_time_provider_applies_price_coverage_and_liquidity_filters():
    master = pd.DataFrame(
        {
            "ticker": ["GOOD", "ILLQ", "MISS"],
            "fund_id": ["GOOD", "ILLQ", "MISS"],
            "first_seen_date": ["2020-01-01"] * 3,
            "last_seen_date": ["2020-12-31"] * 3,
            "inception_date": ["2019-01-01"] * 3,
            "termination_date": [None] * 3,
            "source": ["sec"] * 3,
            "active_flag": [True] * 3,
            "is_etf_candidate": [True] * 3,
        }
    )
    prices = pd.DataFrame(
        {
            "GOOD": [10.0, 11.0, 12.0, 13.0],
            "ILLQ": [20.0, 21.0, 22.0, 23.0],
            "MISS": [30.0, None, None, 33.0],
        },
        index=pd.date_range("2020-01-31", periods=4, freq="ME"),
    )
    volume = pd.DataFrame(
        {
            "GOOD": [200_000, 200_000, 200_000, 200_000],
            "ILLQ": [100, 100, 100, 100],
            "MISS": [200_000, 200_000, 200_000, 200_000],
        },
        index=prices.index,
    )

    provider = PointInTimeETFUniverseProvider(master)
    eligible = provider.constituents_as_of(
        "2020-04-30",
        min_age_months=0,
        min_coverage_pct=0.8,
        min_avg_dollar_volume=1_000_000,
        prices=prices,
        volume=volume,
        lookback_periods=4,
    )

    assert eligible["ticker"].tolist() == ["GOOD"]
    assert eligible.loc[eligible["ticker"] == "GOOD", "price_coverage_pct"].iloc[0] == 1.0
