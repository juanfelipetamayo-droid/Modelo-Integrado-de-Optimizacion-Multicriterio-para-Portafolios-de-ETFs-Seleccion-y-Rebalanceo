# ETF Optimizer

Research-backed Python toolkit and local dashboard for the thesis project **Modelo Integrado de Optimización Multicriterio para Portafolios de ETFs: Selección y Rebalanceo**.

This repository is the digital deliverable for the thesis. It includes source code, reproducible scripts, tests, methodological documentation, generated figures, and the final thesis deliverables. Raw market databases, local result folders, CRSP data, and other heavy/generated datasets are intentionally excluded; they must be rebuilt or obtained through the documented data workflows and institutional licenses where applicable.

Final thesis files are available under `docs/deliverables/`, including `tesis_final_tamayo_etf_electre_objetivos_revisados.pdf`.

The system implements:

1. public ETF universe and historical data ingestion;
2. financial feature engineering;
3. ELECTRE Tri multicriteria ETF classification;
4. portfolio optimization strategies;
5. transaction-cost-aware rebalancing;
6. walk-forward backtesting and benchmark comparison;
7. reproducible methodology and run-manifest reporting;
8. an Apple-inspired Streamlit dashboard for running workflows and exploring results.

See `docs/research_sources.md` for formulas, papers, and methodological sources.

## Benchmark comparability

The sprint report keeps the primary comparison table to comparable out-of-sample series: ELECTRE and optimized EqualWeight/MinVariance/MaxSharpe benchmarks are labeled with `_walk_forward`. Fixed allocation references use explicit labels such as `SPY_buy_hold` and `60/40_SPY_BND_fixed_weight` and are aligned to the same out-of-sample dates. Any future benchmark estimated on the full sample must be labeled with `_in_sample_do_not_compare_primary` and excluded from primary conclusions.

## Quick start

```bash
uv sync --extra dev
uv run pytest -q

# Optional: build the broad active ETF universe snapshot (Nasdaq + SEC enrichment)
uv run python scripts/build_universe.py --out data/universe

# Optional: download public Yahoo Finance data for the universe
uv run python scripts/download_data.py \
  --universe data/universe/etf_universe_clean.csv \
  --start 2021-01-01 \
  --end 2025-12-31 \
  --out data/raw/yfinance

# Optional pilot download: normalize/deduplicate the universe, then use only the first 300 tickers
uv run python scripts/download_data.py \
  --universe data/universe/etf_universe_clean.csv \
  --start 2021-01-01 \
  --end 2025-12-31 \
  --out data/raw/yfinance-pilot \
  --limit 300

# Run the MVP pipeline after data download
uv run python scripts/run_pipeline.py \
  --prices data/raw/yfinance/close.parquet \
  --volume data/raw/yfinance/volume.parquet \
  --out results

# Run the local dashboard
uv run etf-optimizer-dashboard
# or
uv run python scripts/run_dashboard.py
```

## Dashboard

The dashboard is a local Streamlit app with Light and Dark themes. It connects to the same backend outputs used by the CLI workflow.

Dashboard capabilities:

- inspect `strategy_comparison.csv`, equity curves, drawdowns, funnel, ELECTRE outputs, robustness diagnostics, methodology report, run manifest, and provenance/source register;
- run guarded local workflows for universe build, Yahoo Finance download, MVP pipeline, and robust sprint experiment;
- preview the exact command before execution;
- point the UI at any result directory, with `results/sprint_universe_pilot` as the default.

## Professional research controls

The sprint runner now writes audit-grade artifacts for quantitative-finance review:

- `strategy_comparison.csv` keeps walk-forward optimized strategies separate from fixed references (`SPY_buy_hold`, `60/40_SPY_BND_fixed_weight`). Fixed references are sourced from the full downloaded return panel or fetched directly as benchmark references when they are not ELECTRE-eligible.
- `cost_sensitivity.csv` reprices the ELECTRE strategy across transaction-cost assumptions (`0`, `5`, `10`, `25`, `50` bps) from recorded rebalance turnover.
- `bootstrap_metric_intervals.csv` records non-parametric bootstrap confidence intervals for core performance metrics.
- `paired_benchmark_tests.csv` records paired bootstrap confidence intervals for metric differences between the ELECTRE strategy and each benchmark, with directional conclusions (`strategy_positive`, `strategy_negative`, or `not_conclusive`).
- `fold_performance.csv` breaks OOS returns into fold-level metrics so weak regimes and worst folds can be diagnosed instead of relying only on full-period averages.
- `fold_holdings_attribution.csv` ranks weighted ETF contributions inside each OOS fold, making it possible to trace losses back to holdings and external ETF categories.
- `category_exposure_report.csv` tracks transparent ETF risk-bucket exposure (`commodities`, `greater_china`, `natural_resources`, `thematic`, `fixed_income`, etc.) for each OOS date.
- `--category-exposure-cap` applies an optional portfolio hygiene cap by risk bucket and broadens the ELECTRE-selected set when needed to keep the cap feasible.
- `fold_diagnostics.json` / `fold_diagnostics.csv` record walk-forward observation arithmetic after monthly resampling and `pct_change()`, including number of OOS folds, OOS periods, and whether a run is thesis-grade or pilot-only evidence.
- `data_quality_verdict.json` records the allowed academic claim boundary (`structural_test_only`, `public_data_pilot`, or `institutional_thesis_grade`) and prevents public active-current runs from being described as survivorship-bias-free.
- `provenance.json` records code files, raw input hashes, data sources, methodology sources, generated artifacts, run metadata, hashes where available, and explicit limitations.

Current verified test status: **142 tests passing; Ruff clean**.

## Presentation-ready candidate

The current presentation candidate is:

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe data/universe/etf_universe_clean.csv \
  --prices data/raw/yfinance_pilot_2015_2025/close.parquet \
  --volume data/raw/yfinance_pilot_2015_2025/volume.parquet \
  --start 2015-01-05 \
  --end 2025-12-31 \
  --rebalance quarterly \
  --weight-drift buy_and_hold \
  --rebalance-policy threshold \
  --drift-tolerance 0.05 \
  --electre-assignment pessimistic \
  --disable-veto \
  --recategorization-policy every_period \
  --category-confirmation-periods 2 \
  --category-change-min-score-improvement 0.30 \
  --category-exposure-cap 0.25 \
  --cost-bps 10 \
  --min-coverage-pct 0.80 \
  --min-avg-dollar-volume 0 \
  --out results/sprint_universe_paper_quarterly_2015_2025_every_confirm2_m030_cap025
```

This candidate is designed for defensible presentation, not as a final live-trading claim: it mitigates the long OOS failure with explicit concentration and recategorization controls while preserving public-data claim boundaries.

## Current thesis-status boundary

The current public-data runs are **pilot evidence**, not final thesis-grade evidence. The main candidate configuration currently exceeds the project's 10% annualized CAGR target in the public pilot sample, but it must not be described as statistically conclusive or survivorship-bias-free until the validation uses sufficient out-of-sample history and an institutional or otherwise point-in-time ETF universe with delisted/merged funds.
