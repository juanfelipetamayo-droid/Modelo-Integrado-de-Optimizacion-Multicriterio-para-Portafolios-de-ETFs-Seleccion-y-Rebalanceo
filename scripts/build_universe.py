from __future__ import annotations

import argparse
import logging
from pathlib import Path

from etf_optimizer.data.universe_builder import build_universe, write_universe_snapshot

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ETF universe snapshot from configured sources.")
    parser.add_argument("--out", type=Path, default=Path("data/universe"), help="Output directory")
    parser.add_argument("--no-sec", action="store_true", help="Skip SEC EDGAR source")
    parser.add_argument("--no-public", action="store_true", help="Skip public snapshot source")
    args = parser.parse_args()

    logger.info("Building universe (sec=%s, public=%s)...", not args.no_sec, not args.no_public)

    universe = build_universe(
        include_sec=not args.no_sec,
        include_public=not args.no_public,
    )
    logger.info("Universe built: %d funds", len(universe))

    paths = write_universe_snapshot(universe, args.out)
    logger.info("Raw: %s", paths["raw"])
    logger.info("Clean: %s", paths["clean"])
    logger.info("Coverage report: %s", paths["coverage"])


if __name__ == "__main__":
    main()
