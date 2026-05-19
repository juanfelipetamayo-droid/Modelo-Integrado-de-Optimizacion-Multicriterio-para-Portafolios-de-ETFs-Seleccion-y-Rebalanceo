from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from etf_optimizer.data.fetcher import (
    download_ohlcv_batch,
    compute_price_coverage,
    save_ohlcv,
)
from etf_optimizer.data.universe import load_curated_core_etfs

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ETF OHLCV data from Yahoo Finance.")
    parser.add_argument("--universe", type=Path, default=None, help="CSV with a ticker column")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--out", type=Path, default=Path("data/raw/yfinance"))
    parser.add_argument("--batch-size", type=int, default=50, help="Tickers per batch")
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--coverage-report", type=Path, default=None, help="Output path for coverage CSV")
    args = parser.parse_args()

    if args.universe:
        universe = pd.read_csv(args.universe)
    else:
        universe = load_curated_core_etfs()
        logger.info("Using curated core ETF universe (%d tickers)", len(universe))

    tickers = universe["ticker"].dropna().astype(str).str.upper().unique().tolist()
    logger.info("Downloading %d tickers from %s to %s (batch size=%d)", len(tickers), args.start, args.end, args.batch_size)

    frames = download_ohlcv_batch(tickers, args.start, args.end, batch_size=args.batch_size, max_retries=args.max_retries)

    if frames:
        save_ohlcv(frames, args.out)

    coverage_path = args.coverage_report or (args.out / "coverage_report.csv")
    if "close" in frames:
        coverage = compute_price_coverage(tickers, frames["close"], args.start, args.end)
        coverage.to_csv(coverage_path, index=False)
        logger.info("Coverage report written to %s", coverage_path)
        logger.info("Tickers with data: %s / %s",
                    coverage.loc[coverage["metric"] == "tickers_with_data", "count"].values[0],
                    len(tickers))

    fields = list(frames.keys())
    logger.info("Downloaded fields: %s", fields)
    logger.info("Output directory: %s", args.out)


if __name__ == "__main__":
    main()
