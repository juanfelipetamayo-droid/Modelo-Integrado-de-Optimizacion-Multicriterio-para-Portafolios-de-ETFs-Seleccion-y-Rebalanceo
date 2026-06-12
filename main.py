from __future__ import annotations

import argparse
from pathlib import Path

from etf_optimizer.thesis_final import run_thesis_final


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen thesis-final backtest package.")
    parser.add_argument("--config", type=Path, required=True, help="Path to thesis final YAML config")
    args = parser.parse_args()
    manifest_path = run_thesis_final(args.config)
    print(manifest_path)


if __name__ == "__main__":
    main()
