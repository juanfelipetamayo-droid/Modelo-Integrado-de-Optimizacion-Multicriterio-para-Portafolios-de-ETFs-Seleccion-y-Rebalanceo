from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


def download_ohlcv(tickers: list[str], start: str, end: str, auto_adjust: bool = True) -> dict[str, pd.DataFrame]:
    """Download public historical ETF data from Yahoo Finance via yfinance."""
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=auto_adjust,
        group_by="column",
        progress=False,
        threads=True,
    )
    if isinstance(data.columns, pd.MultiIndex):
        return {field.lower().replace(" ", "_"): data[field].dropna(how="all") for field in data.columns.levels[0] if field in data}
    return {field.lower().replace(" ", "_"): data[[field]].rename(columns={field: tickers[0]}) for field in data.columns}


def save_ohlcv(frames: dict[str, pd.DataFrame], out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_parquet(out / f"{name}.parquet")
