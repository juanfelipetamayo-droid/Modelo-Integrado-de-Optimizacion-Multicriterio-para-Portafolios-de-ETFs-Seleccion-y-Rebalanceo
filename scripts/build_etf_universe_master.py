from __future__ import annotations

import argparse
import logging
from pathlib import Path

from etf_optimizer.data.universe_master import build_universe_master_from_sec, month_start_dates

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build public approximate PIT ETF Universe Master from SEC Series/Class snapshots.")
    parser.add_argument("--out", type=Path, default=Path("data/universe_master"), help="Output directory")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--price-dir", type=Path, default=Path("data/raw/yfinance_pilot_2015_2025"))
    args = parser.parse_args()

    years = range(args.start_year, args.end_year + 1)
    rebalance_dates = month_start_dates(f"{args.start_year}-01-01", f"{args.end_year}-12-01")
    logger.info("Building ETF Universe Master: years=%s-%s out=%s", args.start_year, args.end_year, args.out)
    result = build_universe_master_from_sec(
        years=years,
        output_dir=args.out,
        price_dir=args.price_dir,
        rebalance_dates=rebalance_dates,
    )
    logger.info("Wrote %d tables", len(result.table_paths))
    logger.info("Wrote %d rebalance universe snapshots", len(result.snapshot_paths))
    logger.info("Manifest: %s", args.out / "universe_master_manifest.json")


if __name__ == "__main__":
    main()
