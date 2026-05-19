# ETF Optimizer

Research-backed Python toolkit for the thesis project **Modelo Integrado de Optimización Multicriterio para Portafolios de ETFs: Selección y Rebalanceo**.

The system implements:

1. public ETF universe and historical data ingestion;
2. financial feature engineering;
3. ELECTRE Tri multicriteria ETF classification;
4. portfolio optimization strategies;
5. transaction-cost-aware rebalancing;
6. walk-forward backtesting and benchmark comparison;
7. an end-to-end research pipeline that wires the stages together.

See `docs/research_sources.md` for formulas, papers, and methodological sources.

## Quick start

```bash
uv sync --extra dev
uv run pytest -q

# Optional: download public Yahoo Finance data for the curated ETF universe
uv run python scripts/download_data.py --start 2021-01-01 --end 2025-12-31 --out data/raw/yfinance

# Run the MVP pipeline after data download
uv run python scripts/run_pipeline.py \
  --prices data/raw/yfinance/close.parquet \
  --volume data/raw/yfinance/volume.parquet \
  --out results
```

Current verified test status: **12 tests passing**.
