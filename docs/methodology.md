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

Every experiment should report CAGR, volatility, Sharpe, Sortino, max drawdown, Calmar, turnover and cost-adjusted return versus SPY, 60/40, equal-weight and minimum-variance benchmarks.

> **Current implementation:** `performance_summary()` computes CAGR, volatility, Sharpe, Sortino, max drawdown and Calmar for a single return series. Turnover and cost-adjusted return are tracked in `BacktestResult.turnover` and `BacktestResult.portfolio_returns`. Benchmark comparison helpers (`vs SPY`, `vs 60/40`, etc.) are not yet implemented — this is a future extension.
