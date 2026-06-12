## 1. Source Registry and Policy

- [x] 1.1 Define the source registry schema for regulatory, issuer, identifier, price, web reference, and manual curated sources.
- [x] 1.2 Add SEC N-PORT, SEC N-CEN, EDGAR submissions, OpenFIGI, issuer metadata sources, and public price sources to the registry with URLs, allowed use, quality rank, and usage restrictions.
- [x] 1.3 Define source-use policy values for `primary`, `fallback`, `manual_reference`, and `disallowed` sources.
- [x] 1.4 Document rate-limit and User-Agent requirements for SEC and identifier APIs.

## 2. Security Master and Identifier Resolution

- [x] 2.1 Define the stable `security_id` model and identity fields for ticker, CIK, series ID, class ID, CUSIP, ISIN, FIGI, issuer, exchange, and fund name.
- [x] 2.2 Implement identifier mapping records with validity dates and confidence scores.
- [x] 2.3 Add ambiguity detection for ticker reuse, conflicting CUSIP/FIGI mappings, and missing CIK/series/class IDs.
- [x] 2.4 Add tests or checks proving that ticker alone is not used as the durable ETF identity.

## 3. Regulatory Filing Index

- [x] 3.1 Build an EDGAR submissions index for ETF-related CIKs with accession numbers and filing types.
- [x] 3.2 Parse or load SEC N-PORT filing metadata with `period_end_date`, `filed_date`, `accepted_datetime`, and `public_available_date`.
- [x] 3.3 Parse or load SEC N-CEN filing metadata for ETF status and annual fund metadata.
- [x] 3.4 Preserve amendments and amended accessions without overwriting historical point-in-time records.

## 4. Snapshot Tables

- [x] 4.1 Build `fund_snapshot` records containing AUM/net assets, NAV, shares outstanding, expense ratio, issuer, category, asset class, benchmark name, ETF flag, confidence, and quality flags.
- [x] 4.2 Build `holdings_snapshot` records from N-PORT or approved issuer sources with holding identifiers, weights, market values, shares, asset type, sector, and country when available.
- [x] 4.3 Add snapshot quality flags for stale data, missing fields, post-date data exclusion, incomplete holdings, and issuer/category conflicts.
- [x] 4.4 Add checks that snapshots preserve both economic date and public availability date.

## 5. Price History and Liquidity Inputs

- [x] 5.1 Normalize public OHLCV price data into `price_history` keyed by `security_id` and date.
- [x] 5.2 Preserve adjusted close, raw close, volume, dividends, splits, source ID, retrieval date, and price quality flags.
- [x] 5.3 Add liquidity derivations for average dollar volume, valid trading days, missing price coverage, and volume coverage.
- [x] 5.4 Add cross-source or sanity checks for extreme price gaps and missing periods.

## 6. Benchmark Mapping and Tracking Error

- [x] 6.1 Define `benchmark_map` with mapping types `official`, `issuer_stated`, `proxy`, `inferred`, and `missing`.
- [x] 6.2 Add benchmark mapping confidence and rationale fields.
- [x] 6.3 Compute tracking error only when ETF and benchmark return series are available under PIT-safe assumptions.
- [x] 6.4 Label tracking error reports as official, proxy, inferred, or missing according to the benchmark mapping.

## 7. ELECTRE Feature Coverage

- [x] 7.1 Generate `electre_features_pit` with return, volatility, Sharpe Ratio, liquidity, tracking error, and expense ratio for each eligible ETF and decision date.
- [x] 7.2 Record source ID, source date, public availability date, fallback level, confidence, and quality flags for every feature value.
- [x] 7.3 Apply PIT eligibility rules before features can enter ELECTRE input.
- [x] 7.4 Produce a criteria coverage table identifying complete, proxy, partial, missing, and invalid criteria.

## 8. Universe Quality Verdicts and Claims

- [x] 8.1 Extend data-quality verdicts to distinguish `thesis_aligned_public_regulatory_pit`, partial regulatory alignment, pilot static current, and extended robustness evidence.
- [x] 8.2 Add report guardrails preventing unsupported claims such as fully point-in-time, survivor-bias-free institutional, complete US ETF universe, or guaranteed benchmark outperformance.
- [x] 8.3 Add allowed-claims output for each run based on data quality, PIT controls, survivorship limitations, and criterion coverage.
- [x] 8.4 Add report sections listing public-data limitations and fallback usage.

## 9. Objective Validation and Reformulated Objective 3

- [x] 9.1 Add an objective registry containing the accepted objectives and the operational reformulation of objective 3.
- [x] 9.2 Ensure objective 3 is rendered as: "Desarrollar e implementar un modelo de optimización de portafolios que busque mejorar la rentabilidad ajustada por riesgo y controlar la exposición al riesgo, con el propósito de construir portafolios eficientes y evaluar empíricamente si el enfoque multicriterio ofrece ventajas frente a estrategias de inversión tradicionales."
- [x] 9.3 Generate an objective-to-data traceability matrix mapping each objective to criteria, sources, fields, fallbacks, confidence, evidence artifacts, and remaining gaps.
- [x] 9.4 Validate the objective general by checking all six accepted criteria: return, volatility, Sharpe Ratio, liquidity, tracking error, and expense ratio.

## 10. Objective 1 Selection Validation

- [x] 10.1 Enforce final selected ETF cardinality between 10 and 25 assets per rebalance in the principal protocol.
- [x] 10.2 Report every rebalance date that violates the 10-25 cardinality rule.
- [x] 10.3 Distinguish aggregate unique selected assets from per-rebalance selection size.
- [x] 10.4 Validate that 2021-2024 is treated as development/calibration and 2025 as out-of-sample evidence.

## 11. Objective 2 Classification Diagnostics

- [x] 11.1 Report forward performance by ELECTRE category for principal and extended runs.
- [x] 11.2 Report monotonicity, Jaccard stability, turnover, and pessimistic versus optimistic assignment divergence.
- [x] 11.3 Mark objective 2 as fulfilled, partial, or not supported according to diagnostic evidence.
- [x] 11.4 Preserve non-monotonic or unstable classification results rather than smoothing them away.

## 12. Objective 3 Benchmark Evaluation

- [x] 12.1 Compare the thesis strategy against SPY buy-and-hold, 60/40 SPY/BND or documented equivalent, same-universe equal weight, and optimization baselines where applicable.
- [x] 12.2 Evaluate CAGR, Sharpe, Sortino, volatility, max drawdown, and other risk-control metrics over the same OOS window.
- [x] 12.3 Mark objective 3 as empirically supported, partially supported for risk control, or not empirically validated according to benchmark results.
- [x] 12.4 Preserve negative or mixed benchmark results in final reports.

## 13. Principal and Extended Protocol Runs

- [x] 13.1 Add or update configuration for the principal regulatory-enriched 2021-2024/2025 protocol.
- [x] 13.2 Add or update configuration for 2015-2025 extended robustness with degraded claims.
- [x] 13.3 Run and store principal protocol outputs with data-quality verdict, objective compliance summary, feature coverage, selection cardinality, classification diagnostics, and benchmark comparisons.
- [x] 13.4 Run and store extended robustness outputs with explicit pre-2019 public-data limitations.

## 14. Verification

- [x] 14.1 Add tests for PIT feature eligibility using `public_available_date <= decision_date`.
- [x] 14.2 Add tests for identifier ambiguity flags and non-ticker durable identity.
- [x] 14.3 Add tests for criterion coverage and objective status classification.
- [x] 14.4 Add tests for objective 1 cardinality failure and success cases.
- [x] 14.5 Add tests for objective 3 negative-result reporting.
- [x] 14.6 Run the full test suite and record results in the implementation log.
