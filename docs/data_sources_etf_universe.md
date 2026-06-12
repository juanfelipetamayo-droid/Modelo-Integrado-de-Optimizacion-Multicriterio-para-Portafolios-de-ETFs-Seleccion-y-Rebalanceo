# Data Sources for ETF Universe

**Date:** 2026-05-18  
**Updated:** 2026-05-20  
**Project:** portfolio-etf-optimizer  
**Purpose:** Document source selection for building a broad historical ETF universe with survivorship-bias awareness.

> Detailed point-in-time source matrix and implementation roadmap: `docs/research/etf_point_in_time_data_sources.md`.

## Source comparison table

| Source | Type | License / Access | Active ETFs | Delisted ETFs | Survivorship-bias-free? | Citable? | Cost |
|---|---|---|---|---|---|---|---|
| CRSP Survivor-Bias-Free Mutual Fund DB | Academic/commercial | Institutional license (WRDS) | Yes | Yes | Yes | Yes | Institutional license required |
| Morningstar Direct | Commercial institutional | Institutional subscription | Yes | Yes | Partial | Yes | Institutional license required |
| SEC EDGAR (filings) | Public / Legal | Public / Free | Yes (via filings) | Yes (via historical filings) | Partial — depends on filing coverage | Yes (legal source) | Free |
| Nasdaq ETF screener / VettaFi | Public / Current snapshot | Public / Free | Yes | No | No | Limited | Free |
| Yahoo Finance / yfinance | Public | Free for research | Yes | Incomplete | No | No | Free |
| Kaggle ETF datasets | Public | Various (check per dataset) | Yes | Varies | Varies | Limited | Free |

## Selected sources and rationale

### Implemented public v0: Nasdaq ETF screener + SEC EDGAR crosswalk

The implemented `build_universe.py` uses the Nasdaq public ETF screener API as the broad active ETF membership source and then enriches matching tickers with SEC EDGAR CIK/exchange metadata. The 2026-05-18 snapshot produced **4,554 active ETF candidates**, exceeding the ~2k target for a first public universe.

**Important limitation:** this Nasdaq snapshot is current-active, so it is not survivor-bias-free. SEC EDGAR is used here for legal identifier enrichment and corroboration, not as a complete ETF-only historical universe.

### Academic ideal: CRSP / Morningstar / Lipper

For final thesis claims about survivorship-bias-free performance, the preferred source remains CRSP Survivor-Bias-Free Mutual Fund Database, Morningstar Direct, Lipper, Bloomberg, or Refinitiv if institutional access is available.

### Secondary: Nasdaq ETF screener / VettaFi snapshot

Provides current ETF list with tickers, names, and basic metadata. Used as complement to SEC data for active ETFs.

### Price data: Yahoo Finance via yfinance

Practical source for historical daily prices after the universe is established. Coverage of delisted ETFs is incomplete, which is documented as a residual survivorship-bias limitation.

## Survivorship bias mitigation strategy

1. Nasdaq public screener is used for a broad active universe v0.
2. SEC EDGAR is used to enrich/corroborate tickers with CIK/exchange legal identifiers.
3. A coverage report is generated showing how many tickers have SEC metadata and, later, price data.
4. Historical/delisted coverage remains an explicit limitation unless CRSP/Morningstar/Lipper access is obtained.
5. The paper explicitly documents that full survivorship-bias elimination requires CRSP or comparable institutional data.

## Decision

**Two-level strategy:**

- **Level 1 (ideal):** CRSP Survivor-Bias-Free Database or Morningstar Direct if institutional access is available.
- **Level 2 (fallback, implemented here):** SEC EDGAR + Nasdaq/VettaFi snapshot + yfinance prices, with documented coverage limitations.

> If no institutional survivorship-bias-free database is obtained, the paper must not claim full elimination of survivorship bias. It must instead claim documented mitigation with transparent coverage reporting.
