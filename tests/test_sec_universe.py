from __future__ import annotations

import pandas as pd

from etf_optimizer.data.sec_universe import (
    SEC_USER_AGENT,
    _parse_sec_exchange_json,
    filter_likely_etf_entities,
    load_sec_company_tickers,
    load_sec_company_tickers_exchange,
)


class FakeResponse:
    def __init__(self, payload: object, status_error: Exception | None = None):
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self) -> None:
        if self.status_error:
            raise self.status_error

    def json(self) -> object:
        return self.payload


def test_sec_user_agent_defined():
    assert "portfolio-etf-optimizer" in SEC_USER_AGENT


def test_load_sec_company_tickers_parses_sec_mapping(monkeypatch):
    payload = {"0": {"cik_str": 78462, "ticker": "spy", "title": "SPDR S&P 500 ETF TRUST"}}
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse(payload))
    df = load_sec_company_tickers()
    assert isinstance(df, pd.DataFrame)
    assert df.loc[0, "cik"] == "0000078462"
    assert df.loc[0, "ticker"] == "SPY"
    assert df.loc[0, "source"] == "sec"


def test_load_sec_company_tickers_handles_failure():
    df = load_sec_company_tickers(url="https://invalid.url/nonexistent.json", timeout=1)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_parse_sec_exchange_json_documented_shape():
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [[78462, "SPDR S&P 500 ETF TRUST", "SPY", "NYSE Arca"]],
    }
    rows = _parse_sec_exchange_json(payload)
    assert rows == [{"cik": 78462, "name": "SPDR S&P 500 ETF TRUST", "ticker": "SPY", "exchange": "NYSE Arca"}]


def test_load_sec_company_tickers_exchange_parses_documented_shape(monkeypatch):
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [[78462, "SPDR S&P 500 ETF TRUST", "SPY", "NYSE Arca"]],
    }
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse(payload))
    df = load_sec_company_tickers_exchange()
    assert df.loc[0, "ticker"] == "SPY"
    assert df.loc[0, "exchange"] == "NYSE Arca"


def test_filter_likely_etf_entities_is_conservative():
    df = pd.DataFrame({"ticker": ["SPY", "AAPL"], "name": ["SPDR S&P 500 ETF TRUST", "APPLE INC"]})
    result = filter_likely_etf_entities(df)
    assert result["ticker"].tolist() == ["SPY"]
