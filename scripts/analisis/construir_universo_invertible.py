"""Regenera las instantáneas del universo invertible con la configuración documentada
en data/universe_master/investable_universe/README.md, cambiando solo los paneles de precios.

Uso: uv run python data/rerun/construir_universo_invertible.py <close.parquet> <volume.parquet> <out_dir> [<listings.csv> <ultimo_anio>]
"""
import sys
from pathlib import Path

import pandas as pd

from etf_optimizer.data.investable_universe import InvestableUniverseConfig, build_universe_eligibility_report

close_path, volume_path, out_dir = map(Path, sys.argv[1:4])
listings_path = sys.argv[4] if len(sys.argv) > 4 else "data/universe_master/listings_by_date.csv"
last_year = int(sys.argv[5]) if len(sys.argv) > 5 else 2025
listings = pd.read_csv(listings_path)
prices = pd.read_parquet(close_path).sort_index()
volume = pd.read_parquet(volume_path).sort_index()
config = InvestableUniverseConfig(
    min_avg_dollar_volume=1_000_000,
    tradable_exchange_only=False,
    lookback_periods=252,
)
dates = [f"{year}-01-01" for year in range(2015, last_year + 1)]
build_universe_eligibility_report(listings, rebalance_dates=dates, output_dir=out_dir, config=config, prices=prices, volume=volume)
summary = pd.read_csv(out_dir / "universe_eligibility_by_date.csv")
print(summary[["rebalance_date", "observed_universe_count", "investable_universe_count"]].to_string(index=False))
