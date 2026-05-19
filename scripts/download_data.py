from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from etf_optimizer.data.fetcher import download_ohlcv, save_ohlcv
from etf_optimizer.data.universe import load_curated_core_etfs


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ETF OHLCV data from Yahoo Finance.")
    parser.add_argument("--universe", type=Path, default=None, help="CSV with a ticker column")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--out", type=Path, default=Path("data/raw/yfinance"))
    args = parser.parse_args()

    if args.universe:
        universe = pd.read_csv(args.universe)
    else:
        universe = load_curated_core_etfs()
    tickers = universe["ticker"].dropna().astype(str).str.upper().unique().tolist()
    frames = download_ohlcv(tickers, args.start, args.end)
    save_ohlcv(frames, args.out)
    print(f"Downloaded {len(tickers)} tickers into {args.out}")


if __name__ == "__main__":
    main()
