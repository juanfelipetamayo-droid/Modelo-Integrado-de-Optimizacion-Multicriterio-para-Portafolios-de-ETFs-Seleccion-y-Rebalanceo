from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.data.investable_universe import (
    InvestableUniverseConfig,
    PublicApproximatePITUniverseProvider,
    build_universe_eligibility_report,
    investable_universe_as_of,
    observed_universe_as_of,
)


def _sample_observations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fund_id": ["SPY", "MF", "CEF", "ETN", "LEV", "INV", "LOW", "NEW", "ILLQ", "OTC"],
            "ticker": ["SPY", "MFNDX", "CEFX", "ETNX", "UPRO", "SH", "LOWP", "NEW", "ILLQ", "OTCETF"],
            "fund_name": [
                "SPDR S&P 500 ETF Trust",
                "Sample Mutual Fund",
                "Closed End Income Fund",
                "Sample Exchange Traded Note ETN",
                "ProShares Ultra S&P500 3x Leveraged ETF",
                "ProShares Short S&P500 Inverse ETF",
                "Low Price ETF",
                "New ETF",
                "Illiquid ETF",
                "OTC ETF",
            ],
            "product_type": ["ETF", "Mutual Fund", "Closed-End Fund", "ETN", "ETF", "ETF", "ETF", "ETF", "ETF", "ETF"],
            "is_etf_or_etmf": [True, False, False, False, True, True, True, True, True, True],
            "is_mutual_fund": [False, True, False, False, False, False, False, False, False, False],
            "is_closed_end_fund": [False, False, True, False, False, False, False, False, False, False],
            "is_etn": [False, False, False, True, False, False, False, False, False, False],
            "is_leveraged": [False, False, False, False, True, False, False, False, False, False],
            "is_inverse": [False, False, False, False, False, True, False, False, False, False],
            "exchange": ["NYSE Arca", "NYSE Arca", "NYSE", "NYSE Arca", "NYSE Arca", "NYSE Arca", "NYSE Arca", "NYSE Arca", "NYSE Arca", "OTC"],
            "ticker_start_date": [
                "2018-01-01",
                "2018-01-01",
                "2018-01-01",
                "2018-01-01",
                "2018-01-01",
                "2018-01-01",
                "2018-01-01",
                "2020-06-01",
                "2018-01-01",
                "2018-01-01",
            ],
            "ticker_end_date": ["2021-12-31"] * 10,
            "source_available_date": ["2019-01-01"] * 10,
            "observation_start_date": ["2019-01-01"] * 10,
            "observation_end_date": ["2021-12-31"] * 10,
            "termination_date": [pd.NaT] * 10,
            "delisted_date": [pd.NaT] * 10,
        }
    )


def _prices_and_volume() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2018-01-31", "2021-01-31", freq="ME")
    tickers = ["SPY", "LOWP", "NEW", "ILLQ", "OTCETF", "MFNDX", "CEFX", "ETNX", "UPRO", "SH"]
    prices = pd.DataFrame(25.0, index=dates, columns=tickers)
    prices["LOWP"] = 4.0
    prices.loc[dates[-10:], "NEW"] = 25.0
    prices.loc[dates[:-10], "NEW"] = pd.NA
    prices.loc[dates[-8:], "ILLQ"] = pd.NA
    volume = pd.DataFrame(1_000_000, index=dates, columns=tickers)
    volume["ILLQ"] = 10
    return prices, volume


def test_observed_universe_as_of_only_applies_point_in_time_visibility() -> None:
    observed = observed_universe_as_of(_sample_observations(), "2021-01-31")

    assert set(observed["ticker"]) == {"SPY", "MFNDX", "CEFX", "ETNX", "UPRO", "SH", "LOWP", "NEW", "ILLQ", "OTCETF"}
    assert "universe_layer" in observed.columns
    assert (observed["universe_layer"] == "observed").all()


def test_investable_universe_as_of_separates_hard_filter_exclusions() -> None:
    prices, volume = _prices_and_volume()
    observed = observed_universe_as_of(_sample_observations(), "2021-01-31")

    investable, exclusions = investable_universe_as_of(
        observed,
        "2021-01-31",
        config=InvestableUniverseConfig(min_history_months=24, min_price=5.0, min_avg_dollar_volume=1_000_000, max_missing_returns=0.20),
        prices=prices,
        volume=volume,
    )

    assert investable["ticker"].tolist() == ["SPY"]
    assert (investable["universe_layer"] == "investable").all()
    reasons = exclusions.set_index("ticker")["exclusion_reasons"].to_dict()
    assert "not_etf_or_etmf" in reasons["MFNDX"]
    assert "mutual_fund" in reasons["MFNDX"]
    assert "closed_end_fund" in reasons["CEFX"]
    assert "etn" in reasons["ETNX"]
    assert "leveraged" in reasons["UPRO"]
    assert "inverse" in reasons["SH"]
    assert "price_below_min" in reasons["LOWP"]
    assert "insufficient_history" in reasons["NEW"]
    assert "missing_returns_above_max" in reasons["ILLQ"]
    assert "avg_dollar_volume_below_min" in reasons["ILLQ"]
    assert "non_tradable_exchange" in reasons["OTCETF"]


def test_build_universe_eligibility_report_writes_counts_and_excluded_by_reason(tmp_path: Path) -> None:
    prices, volume = _prices_and_volume()

    result = build_universe_eligibility_report(
        _sample_observations(),
        rebalance_dates=["2021-01-31"],
        output_dir=tmp_path,
        config=InvestableUniverseConfig(min_history_months=24, min_price=5.0, min_avg_dollar_volume=1_000_000, max_missing_returns=0.20),
        prices=prices,
        volume=volume,
    )

    summary = pd.read_csv(result.summary_path)
    exclusions = pd.read_csv(result.exclusions_by_reason_path)
    assert summary.loc[0, "observed_universe_count"] == 10
    assert summary.loc[0, "investable_universe_count"] == 1
    assert "leveraged" in summary.loc[0, "excluded_by_reason"]
    assert set(exclusions.columns) == {"rebalance_date", "exclusion_reason", "excluded_count"}
    assert (tmp_path / "observed_universe_snapshots" / "observed_universe_2021_01_31.csv").exists()
    assert (tmp_path / "investable_universe_snapshots" / "investable_universe_2021_01_31.csv").exists()


def test_public_approximate_pit_provider_uses_latest_snapshot_without_lookahead(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    pd.DataFrame({"ticker": ["AAA", "BBB"], "ticker_start_date": ["2018-01-01", "2018-01-01"]}).to_csv(
        snapshot_dir / "investable_universe_2018_01_01.csv",
        index=False,
    )
    pd.DataFrame({"ticker": ["CCC"], "ticker_start_date": ["2019-01-01"]}).to_csv(
        snapshot_dir / "investable_universe_2019_01_01.csv",
        index=False,
    )
    provider = PublicApproximatePITUniverseProvider(snapshot_dir)

    _, q2_snapshot = provider.snapshot_as_of("2018-04-30")
    early_snapshot = provider.constituents_as_of("2017-12-31")

    assert q2_snapshot["ticker"].tolist() == ["AAA", "BBB"]
    assert q2_snapshot["snapshot_date_used"].unique().tolist() == ["2018-01-01"]
    assert early_snapshot.empty


def test_public_approximate_pit_provider_applies_lookback_market_filters(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    pd.DataFrame({"ticker": ["AAA", "BBB"]}).to_csv(
        snapshot_dir / "investable_universe_2020_01_01.csv",
        index=False,
    )
    provider = PublicApproximatePITUniverseProvider(snapshot_dir)
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")
    prices = pd.DataFrame({"AAA": [10.0, 11.0, 12.0, 13.0], "BBB": [20.0, pd.NA, pd.NA, 23.0]}, index=dates)
    volume = pd.DataFrame({"AAA": [1000, 1000, 1000, 1000], "BBB": [1, 1, 1, 1]}, index=dates)

    eligible = provider.constituents_as_of(
        "2020-04-30",
        min_coverage_pct=0.75,
        min_avg_dollar_volume=10_000.0,
        prices=prices,
        volume=volume,
        lookback_periods=4,
    )

    assert eligible["ticker"].tolist() == ["AAA"]
