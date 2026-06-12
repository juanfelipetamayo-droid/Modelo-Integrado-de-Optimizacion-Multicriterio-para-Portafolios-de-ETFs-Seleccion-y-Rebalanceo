# Methodology

## Hypothesis

A two-stage pipeline can improve ETF portfolio construction by first filtering the ETF universe through multicriteria decision analysis and then applying constrained quantitative optimization only to the selected candidates.

## Stage 1: ETF universe

The default implementation ships with a curated core ETF universe for reproducibility. The data layer can be replaced with public ETF lists from Nasdaq, ETF.com exports, Kaggle ETF datasets, or licensed institutional databases.

## Stage 2: Feature engineering

Features are calculated from adjusted historical prices and volume. Cost-like criteria such as volatility and max drawdown are marked as `min`; benefit-like criteria such as CAGR, Sharpe, Sortino and liquidity (avg. dollar volume) are marked as `max`.

> **Note:** Tracking error and expense ratio are recognized cost criteria in the methodology but are not computed from OHLCV data alone. Tracking error requires a benchmark return series; expense ratio requires fund-level data (e.g. Morningstar, EDGAR filings). These can be added when the data source expands.

## Stage 3: ELECTRE Tri selection

ELECTRE Tri is used as a sorting model rather than a simple weighted sum. This matters because a veto threshold can prevent a fund with excellent return from passing if one criterion is unacceptable, such as excessive fees, drawdown or tracking error.

## Stage 4: Optimization

The optimizer begins with transparent baselines:

- equal weight;
- minimum variance;
- maximum Sharpe;
- Ledoit-Wolf covariance shrinkage.

These are intentionally simple and defensible. More advanced strategies can be added later after the baseline is stable.

## Stage 5: Walk-forward validation

The backtester passes only the training window to the strategy function and applies the resulting weights to the subsequent test window. This design prevents look-ahead bias by construction.

## Stage 6: Reporting

Every experiment should report CAGR, volatility, Sharpe, Sortino, max drawdown, Calmar, turnover and cost-adjusted return versus SPY, 60/40, equal-weight and minimum-variance benchmarks. Professional sprint runs also emit transaction-cost sensitivity, bootstrap metric intervals, paired bootstrap benchmark-difference tests, fold-level OOS performance diagnostics, holding-level fold attribution, ELECTRE selection sensitivity, out-of-sample fold diagnostics, data-quality claim boundaries, and a machine-readable provenance record for code/data/methodology auditability.

Primary reports must not mix in-sample optimized benchmarks with walk-forward strategies. The current sprint report labels ELECTRE and optimized EqualWeight/MinVariance/MaxSharpe rows with `_walk_forward`; fixed-weight references are labeled as `SPY_buy_hold` and `60/40_SPY_BND_fixed_weight` and aligned to the walk-forward out-of-sample index. If a full-sample optimized benchmark is ever retained for diagnostics, its row name must include `_in_sample_do_not_compare_primary` and it must not be used as a primary comparator.

The run-level data-quality verdict constrains thesis language. Synthetic runs are structural tests only. Public Nasdaq/yfinance runs are public-data pilots and must not be described as survivorship-bias-free or statistically conclusive. Only institutional historical ETF data with delisted/merged funds and sufficient out-of-sample folds may be labeled thesis-grade survivorship-bias-free evidence.

## Claim boundaries for thesis writing

Allowed claims:

- A public approximate point-in-time ETF universe was constructed.
- Explicit look-ahead violations are controlled through `source_available_date`.
- Observation quality is labeled and reported.
- Selection, allocation, and rebalancing are separate stages.
- ELECTRE Tri is compared against FlowSort as a multicriteria classification/sorting method.
- Classification quality is evaluated before portfolio performance.
- Ablations isolate sources of performance.

Forbidden claims:

- The public database is completely survivor-bias-free.
- The model beats the market.
- Do not describe ELECTRE as the portfolio-weight optimizer.
- Do not describe FlowSort as the rebalancing engine.
- High-CAGR pilot windows are final evidence.

Recommended thesis wording:

> Dado que no fue posible acceder a una base institucional survivor-bias-free como CRSP, se construyó un universo ETF público aproximado point-in-time a partir de fuentes regulatorias y de mercado, incorporando fechas de disponibilidad de información y etiquetas de calidad. Esta reconstrucción no elimina por completo el riesgo de sesgo de supervivencia, pero permite reducirlo y hacerlo explícito dentro del protocolo de backtesting.

## Current implementation

`performance_summary()` computes CAGR, volatility, Sharpe, Sortino, max drawdown and Calmar for a single return series. Turnover and cost-adjusted return are tracked in `BacktestResult.turnover` and `BacktestResult.portfolio_returns`. Primary benchmark comparison is produced by `scripts/run_sprint_experiment.py` using out-of-sample walk-forward optimized benchmarks plus aligned fixed-weight references.

## Thesis objective alignment

The accepted thesis objectives in `docs/trabajo_de_grado.md` are tracked in `docs/traceability/thesis_objective_alignment.md`. The operational protocol for aligning the implementation with those objectives is documented in `docs/methodology/thesis_aligned_protocol.md`.

The thesis-aligned interpretation separates three result classes:

- **Primary protocol:** 2021-2024 development/calibration and 2025 out-of-sample validation.
- **Extended robustness:** 2015-2025 sensitivity and regime robustness, not a replacement for the accepted protocol.
- **Pilot diagnostics:** static-current or incomplete-criteria runs used only for development and diagnosis.
