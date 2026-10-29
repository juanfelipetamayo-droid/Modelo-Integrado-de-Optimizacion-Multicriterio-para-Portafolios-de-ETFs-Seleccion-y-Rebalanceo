from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import requests

DEFAULT_ETF_UNIVERSE_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
CURATED_CORE_ETFS = [
    "SPY", "IVV", "VOO", "QQQ", "IWM", "VTI", "VEA", "VWO", "BND", "AGG",
    "TLT", "IEF", "LQD", "HYG", "GLD", "SLV", "VNQ", "XLK", "XLF", "XLV",
    "XLY", "XLP", "XLE", "XLI", "XLB", "XLU", "XLRE", "XLC", "MTUM", "QUAL",
    "USMV", "VLUE", "SCHD", "VIG", "ARKK", "DIA", "MDY", "EFA", "EEM", "BIL",
]


def load_curated_core_etfs() -> pd.DataFrame:
    """Small reproducible ETF universe useful for demos and tests.

    For thesis experiments, extend or replace this with ETF lists from ETF.com,
    Nasdaq fund lists, Kaggle ETF datasets, or a licensed data provider.
    """
    return pd.DataFrame({"ticker": CURATED_CORE_ETFS})


def download_csv_universe(url: str, ticker_column: str = "Symbol") -> pd.DataFrame:
    """Download a public CSV universe and normalize it to a `ticker` column."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))
    if ticker_column not in df.columns:
        raise ValueError(f"ticker_column {ticker_column!r} not found in columns {list(df.columns)}")
    df = df.rename(columns={ticker_column: "ticker"})
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    return df.drop_duplicates("ticker")


def save_universe(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
