from __future__ import annotations

import pandas as pd

from etf_optimizer.data.public_universe import (
    FALLBACK_ETF_TICKERS,
    load_fallback_tickers,
    load_public_current_etf_snapshot,
    parse_nasdaq_etf_api,
)


class FakeResponse:
    headers = {"content-type": "application/json"}
    text = "{}"

    def __init__(self, payload: object):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def test_parse_nasdaq_etf_api_rows():
    payload = {"data": {"data": {"rows": [{"symbol": "spy", "companyName": "SPDR S&P 500 ETF Trust"}]}}}
    df = parse_nasdaq_etf_api(payload)
    assert df.loc[0, "ticker"] == "SPY"
    assert df.loc[0, "name"] == "SPDR S&P 500 ETF Trust"


def test_load_public_current_etf_snapshot_returns_dataframe(monkeypatch):
    payload = {"data": {"data": {"rows": [{"symbol": "SPY", "companyName": "SPDR S&P 500 ETF Trust"}]}}}
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse(payload))
    df = load_public_current_etf_snapshot()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "ticker" in df.columns
    assert "fund_id" in df.columns
    assert "source" in df.columns
    assert "active_flag" in df.columns


def test_load_public_current_etf_snapshot_no_duplicates(monkeypatch):
    payload = {"data": {"data": {"rows": [
        {"symbol": "SPY", "companyName": "SPDR S&P 500 ETF Trust"},
        {"symbol": "SPY", "companyName": "SPDR S&P 500 ETF Trust"},
    ]}}}
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse(payload))
    df = load_public_current_etf_snapshot()
    assert df["fund_id"].is_unique


def test_load_fallback_tickers():
    df = load_fallback_tickers()
    assert len(df) == len(set(FALLBACK_ETF_TICKERS))
    assert all(df["source"] == "manual")
    assert all(df["active_flag"])


def test_fallback_tickers_contains_spy():
    df = load_fallback_tickers()
    assert "SPY" in df["ticker"].values
