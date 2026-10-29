from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from etf_optimizer.data.fetcher import (
    download_ohlcv_batch,
    compute_price_coverage,
    compute_ticker_coverage,
    save_ohlcv,
)
from etf_optimizer.data.universe import load_curated_core_etfs

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def _batch_failures_frame(batch_result: dict[str, pd.DataFrame]) -> pd.DataFrame:
    failed_tickers = getattr(batch_result, "failed_tickers", [])
    errors = getattr(batch_result, "errors", {})
    return pd.DataFrame(
        [{"ticker": ticker, "error": errors.get(ticker, "unknown_error")} for ticker in failed_tickers],
        columns=["ticker", "error"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ETF OHLCV data from Yahoo Finance.")
    parser.add_argument("--universe", type=Path, default=None, help="CSV with a ticker column")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--out", type=Path, default=Path("data/raw/yfinance"))
    parser.add_argument("--batch-size", type=int, default=50, help="Tickers per batch")
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--coverage-report", type=Path, default=None, help="Output path for coverage CSV")
    parser.add_argument("--limit", type=int, default=None, help="Limit tickers after normalization/deduplication for pilot downloads")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be a non-negative integer")

    if args.universe:
        universe = pd.read_csv(args.universe)
    else:
        universe = load_curated_core_etfs()
        logger.info("Using curated core ETF universe (%d tickers)", len(universe))

    raw_tickers = universe["ticker"].dropna().astype(str)
    requested_tickers = len(raw_tickers)
    normalized_tickers = raw_tickers.str.strip().str.upper()
    normalized_tickers = normalized_tickers[normalized_tickers != ""]
    unique_tickers = normalized_tickers.unique().tolist()
    tickers = unique_tickers[: args.limit] if args.limit is not None else unique_tickers
    logger.info(
        "Ticker universe: requested=%d normalized_unique=%d used=%d limit=%s",
        requested_tickers,
        len(unique_tickers),
        len(tickers),
        args.limit if args.limit is not None else "none",
    )
    logger.info("Downloading %d tickers from %s to %s (batch size=%d)", len(tickers), args.start, args.end, args.batch_size)

    frames = download_ohlcv_batch(tickers, args.start, args.end, batch_size=args.batch_size, max_retries=args.max_retries)

    failures = _batch_failures_frame(frames)
    if not failures.empty:
        args.out.mkdir(parents=True, exist_ok=True)
        failures_path = args.out / "download_failures.csv"
        failures.to_csv(failures_path, index=False)
        logger.warning("Download failures written to %s", failures_path)

    if frames:
        save_ohlcv(frames, args.out)

    coverage_path = args.coverage_report or (args.out / "coverage_report.csv")
    coverage_by_ticker_path = args.out / "coverage_by_ticker.csv"
    if "close" in frames:
        coverage = compute_price_coverage(tickers, frames["close"], args.start, args.end)
        coverage.to_csv(coverage_path, index=False)
        coverage_by_ticker = compute_ticker_coverage(tickers, frames["close"], args.start, args.end)
        coverage_by_ticker.to_csv(coverage_by_ticker_path, index=False)
        logger.info("Coverage report written to %s", coverage_path)
        logger.info("Coverage by ticker written to %s", coverage_by_ticker_path)
        logger.info("Tickers with data: %s / %s",
                    coverage.loc[coverage["metric"] == "tickers_with_data", "count"].values[0],
                    len(tickers))

    fields = list(frames.keys())
    logger.info("Downloaded fields: %s", fields)
    logger.info("Output directory: %s", args.out)


if __name__ == "__main__":
    main()
