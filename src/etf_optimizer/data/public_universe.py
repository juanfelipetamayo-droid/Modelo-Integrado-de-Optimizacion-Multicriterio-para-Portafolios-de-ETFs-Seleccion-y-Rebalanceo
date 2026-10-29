from __future__ import annotations

from io import StringIO

import pandas as pd
import requests

from etf_optimizer.data.schema import CANONICAL_COLUMNS, make_fund_id, normalize_tickers

NASDAQ_ETF_API_URL = "https://api.nasdaq.com/api/screener/etf?download=true"
LEGACY_ETF_CSV_URL = "https://raw.githubusercontent.com/iancaling/etf-list/master/etfs.csv"
NASDAQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; portfolio-etf-optimizer/0.1 research)",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/market-activity/etf/screener",
}

FALLBACK_ETF_TICKERS: list[str] = [
    "SPY", "IVV", "VOO", "QQQ", "IWM", "VTI", "VEA", "VWO", "BND", "AGG",
    "TLT", "IEF", "LQD", "HYG", "GLD", "SLV", "VNQ", "XLK", "XLF", "XLV",
    "XLY", "XLP", "XLE", "XLI", "XLB", "XLU", "XLRE", "XLC",
    "DIA", "MDY", "EFA", "EEM", "BIL", "SHV", "MUB", "TIP",
    "IGSB", "VCIT", "VCSH", "VWOB", "EMB", "PCY", "BWX",
    "SCHD", "VIG", "VYM", "DVY", "HDV",
    "MTUM", "QUAL", "USMV", "VLUE", "SIZE", "FNDX", "FNDF",
    "ARKK", "ARKQ", "ARKW", "ARKG", "ARKF",
    "ICLN", "TAN", "PBW", "QCLN",
    "IBB", "XBI", "BIB",
    "XLE", "XOP", "OIH",
    "XLF", "KRE", "KBE",
    "XRT", "RTH",
    "SMH", "SOXX",
    "GDX", "GDXJ", "SIL",
    "UNG", "USO", "DBC",
    "TLH", "MBB", "VMBS",
    "HYG", "JNK", "ANGL",
]


def parse_nasdaq_etf_api(payload: dict) -> pd.DataFrame:
    """Parse Nasdaq ETF screener JSON download payload into ticker/name rows."""
    rows = payload.get("data", {}).get("data", {}).get("rows", [])
    records = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("symbol", "")).strip().upper()
        if not ticker:
            continue
        records.append(
            {
                "ticker": ticker,
                "name": row.get("companyName"),
                "source": "nasdaq",
                "source_url": NASDAQ_ETF_API_URL,
                "active_flag": True,
            }
        )
    return pd.DataFrame(records)


def _canonicalize_public(df: pd.DataFrame, source: str, source_url: str) -> pd.DataFrame:
    if "ticker" not in df.columns and "Symbol" in df.columns:
        df = df.rename(columns={"Symbol": "ticker"})
    if "ticker" not in df.columns and "symbol" in df.columns:
        df = df.rename(columns={"symbol": "ticker"})
    if "name" not in df.columns and "Name" in df.columns:
        df = df.rename(columns={"Name": "name"})
    if "name" not in df.columns and "companyName" in df.columns:
        df = df.rename(columns={"companyName": "name"})
    if "ticker" not in df.columns:
        df = pd.DataFrame({"ticker": FALLBACK_ETF_TICKERS})
    df = normalize_tickers(df)
    df["source"] = source
    df["source_url"] = source_url
    df["active_flag"] = True
    df["fund_id"] = df.apply(make_fund_id, axis=1)
    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[CANONICAL_COLUMNS].drop_duplicates("fund_id").reset_index(drop=True)


def load_public_current_etf_snapshot(
    url: str = NASDAQ_ETF_API_URL,
    timeout: int = 30,
) -> pd.DataFrame:
    """Download the broad current ETF snapshot from Nasdaq's public screener API.

    This is a broad active/current universe source, not a survivorship-bias-free history.
    The SEC crosswalk should be used for legal corroboration and CRSP/Morningstar/Lipper
    for full historical/delisted coverage when available.
    """
    try:
        response = requests.get(url, headers=NASDAQ_HEADERS, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "json" in content_type or response.text.lstrip().startswith("{"):
            df = parse_nasdaq_etf_api(response.json())
            if not df.empty:
                return _canonicalize_public(df, "nasdaq", url)
        df = pd.read_csv(StringIO(response.text))
        return _canonicalize_public(df, "nasdaq", url)
    except (requests.RequestException, ValueError, pd.errors.ParserError, KeyError):
        try:
            response = requests.get(LEGACY_ETF_CSV_URL, timeout=timeout)
            response.raise_for_status()
            return _canonicalize_public(pd.read_csv(StringIO(response.text)), "nasdaq", LEGACY_ETF_CSV_URL)
        except (requests.RequestException, ValueError, pd.errors.ParserError, KeyError):
            return _canonicalize_public(pd.DataFrame({"ticker": FALLBACK_ETF_TICKERS}), "manual", "embedded_fallback")


def load_fallback_tickers() -> pd.DataFrame:
    return _canonicalize_public(pd.DataFrame({"ticker": FALLBACK_ETF_TICKERS}), "manual", "embedded_fallback")
