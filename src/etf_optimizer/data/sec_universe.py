from __future__ import annotations

import pandas as pd
import requests

from etf_optimizer.data.schema import CANONICAL_COLUMNS, make_fund_id, normalize_tickers

SEC_USER_AGENT = "portfolio-etf-optimizer/0.1.0 (research project; contact: juan.tamayo@email.com)"
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
ETF_NAME_KEYWORDS = (" ETF", "EXCHANGE TRADED", " ETF ", "TRUST")


def _canonicalize(df: pd.DataFrame, source_url: str) -> pd.DataFrame:
    df = normalize_tickers(df)
    df["source"] = "sec"
    df["source_url"] = source_url
    df["active_flag"] = True
    df["fund_id"] = df.apply(make_fund_id, axis=1)
    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
    mask = df["ticker"].notna() & (df["ticker"] != "")
    return df.loc[mask, CANONICAL_COLUMNS].reset_index(drop=True)


def load_sec_company_tickers(
    url: str = SEC_COMPANY_TICKERS_URL,
    user_agent: str = SEC_USER_AGENT,
    timeout: int = 30,
) -> pd.DataFrame:
    """Load SEC company tickers from EDGAR's official JSON endpoint.

    This endpoint is a legal/citable crosswalk for CIK, ticker and registrant name.
    It is **not** an ETF universe by itself; use it to enrich or corroborate a universe
    assembled from ETF-specific sources.
    """
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        records = [
            {
                "cik": str(entry.get("cik_str", "")).zfill(10),
                "ticker": str(entry.get("ticker", "")).strip().upper(),
                "name": entry.get("title", ""),
            }
            for entry in data.values()
            if isinstance(entry, dict)
        ]
        return _canonicalize(pd.DataFrame(records), url)
    except (requests.RequestException, ValueError, KeyError, AttributeError):
        return pd.DataFrame(columns=CANONICAL_COLUMNS)


def _parse_sec_exchange_json(data: object) -> list[dict[str, object]]:
    """Parse SEC company_tickers_exchange JSON in either documented or row-dict shape."""
    if isinstance(data, dict) and "fields" in data and "data" in data:
        fields = [str(field) for field in data["fields"]]
        return [dict(zip(fields, row, strict=False)) for row in data["data"] if isinstance(row, (list, tuple))]
    if isinstance(data, list):
        return [entry for entry in data if isinstance(entry, dict)]
    if isinstance(data, dict):
        return [entry for entry in data.values() if isinstance(entry, dict)]
    return []


def load_sec_company_tickers_exchange(
    url: str = SEC_COMPANY_TICKERS_EXCHANGE_URL,
    user_agent: str = SEC_USER_AGENT,
    timeout: int = 30,
) -> pd.DataFrame:
    """Load SEC company tickers with exchange info from EDGAR."""
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        records = []
        for entry in _parse_sec_exchange_json(data):
            records.append(
                {
                    "cik": str(entry.get("cik", entry.get("cik_str", ""))).zfill(10),
                    "ticker": str(entry.get("ticker", "")).strip().upper(),
                    "name": entry.get("name", entry.get("title", "")),
                    "exchange": entry.get("exchange", ""),
                }
            )
        return _canonicalize(pd.DataFrame(records), url)
    except (requests.RequestException, ValueError, KeyError, AttributeError):
        return pd.DataFrame(columns=CANONICAL_COLUMNS)


def filter_likely_etf_entities(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort SEC-name filter for ETF-like registrants.

    This is deliberately conservative and should not be treated as a survivor-bias-free
    ETF universe. Its role is legal corroboration/enrichment, not primary universe selection.
    """
    if df.empty or "name" not in df.columns:
        return df.copy()
    names = df["name"].fillna("").str.upper()
    mask = names.str.contains("ETF|EXCHANGE TRADED|ISHARES|SPDR|VANGUARD.*INDEX|INVESCO.*TRUST", regex=True)
    return df.loc[mask].reset_index(drop=True)
