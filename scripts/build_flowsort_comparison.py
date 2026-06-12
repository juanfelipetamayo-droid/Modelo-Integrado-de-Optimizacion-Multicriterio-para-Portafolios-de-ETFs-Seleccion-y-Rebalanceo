from __future__ import annotations

import argparse
from pathlib import Path

from etf_optimizer.reporting.flowsort_comparison import write_flowsort_comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ELECTRE Tri vs FlowSort sorting comparison artifacts.")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results/pit_integration_baseline/new_public_approximate_pit_universe"),
    )
    parser.add_argument("--prices", type=Path, default=Path("data/raw/yfinance_pilot_2015_2025/close.parquet"))
    parser.add_argument("--out", type=Path, default=Path("results/electre_vs_flowsort"))
    parser.add_argument("--report", type=Path, default=Path("docs/results/electre_vs_flowsort.md"))
    args = parser.parse_args()

    paths = write_flowsort_comparison(args.results_dir, args.prices, args.out, args.report)
    for path in paths:
        print(path)
    print(args.report)


if __name__ == "__main__":
    main()
