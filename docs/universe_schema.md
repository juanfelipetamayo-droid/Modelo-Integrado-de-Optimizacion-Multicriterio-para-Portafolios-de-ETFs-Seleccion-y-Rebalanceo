# ETF Universe Schema

**Date:** 2026-05-18  
**Purpose:** Define the canonical schema for the ETF universe dataset to ensure source compatibility.

## Columns

| Column | Type | Required | Description |
|---|---|---|---|
| `fund_id` | str | Yes | Unique identifier (ticker if available, else SEC identifier) |
| `ticker` | str | Yes | Ticker symbol (uppercase, normalized) |
| `name` | str | No | Full legal name of the fund |
| `cik` | str | No | SEC Central Index Key (10-digit padded) |
| `series_id` | str | No | SEC series identifier (if available) |
| `class_id` | str | No | SEC class identifier (if available) |
| `exchange` | str | No | Primary exchange (NYSE, NASDAQ, etc.) |
| `sponsor` | str | No | Fund sponsor / fund family |
| `asset_class` | str | No | Asset class (Equity, Fixed Income, Commodity, etc.) |
| `category` | str | No | Morningstar-style category if available |
| `inception_date` | date | No | Fund inception date |
| `termination_date` | date | No | Fund termination/liquidation date (if applicable) |
| `source` | str | Yes | Origin source identifier ('sec', 'nasdaq', 'vettafi', 'manual') |
| `source_url` | str | No | URL or reference for the source record |
| `active_flag` | bool | Yes | True if fund is currently active |
| `expense_ratio` | float | No | Annual expense ratio (decimal) |
| `aum` | float | No | Assets under management (USD) |
| `benchmark` | str | No | Benchmark index ticker |

## Constraints

- `fund_id` must be non-null and unique across the merged dataset.
- `ticker` must be uppercase, stripped, and non-null.
- `source` must be one of the known source identifiers.
- `active_flag` must be a boolean (True for active, False for terminated/merged).

## Source column mappings

| Source | Maps to |
|---|---|
| SEC EDGAR | fund_id=ticker or CIK, cik, series_id, class_id, name |
| Nasdaq screener | fund_id=ticker, ticker, name, exchange, category |
| VettaFi | fund_id=ticker, ticker, name, sponsor, expense_ratio, aum |
| yfinance (prices only) | No universe columns; prices are merged by ticker separately |
