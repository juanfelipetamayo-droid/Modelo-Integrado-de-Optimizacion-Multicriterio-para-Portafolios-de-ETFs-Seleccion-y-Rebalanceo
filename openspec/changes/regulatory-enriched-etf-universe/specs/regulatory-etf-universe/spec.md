## ADDED Requirements

### Requirement: Source Registry
The system SHALL maintain a registry of every external data source used to build the ETF universe, including source type, URL, license or terms summary, retrieval method, allowed use, quality rank, and rate-limit policy.

#### Scenario: Register regulatory source
- **WHEN** SEC N-PORT, SEC N-CEN, or EDGAR is used as an input
- **THEN** the source registry records it as a `regulatory` source with primary allowed use and a traceable URL

#### Scenario: Restrict commercial web source
- **WHEN** a commercial web page or unofficial scraper is used only for enrichment
- **THEN** the source registry marks it as `fallback`, `manual_reference`, or `disallowed` according to known terms and quality limits

### Requirement: Stable ETF Identity
The system SHALL assign each ETF a stable internal `security_id` and SHALL NOT use ticker alone as the durable identity key.

#### Scenario: Map multiple identifiers
- **WHEN** an ETF has ticker, CIK, series ID, class ID, CUSIP, ISIN, or FIGI data available
- **THEN** the system stores those identifiers under the same `security_id` with validity dates and mapping confidence

#### Scenario: Ambiguous identifier mapping
- **WHEN** two or more candidate mappings conflict for the same ticker and date
- **THEN** the system flags the ETF with an identifier ambiguity quality flag and excludes or degrades affected features until resolved

### Requirement: Filing Index Audit Trail
The system SHALL index regulatory filings with `accession_number`, `form_type`, `period_end_date`, `filed_date`, `accepted_datetime`, `public_available_date`, source URL, amendment status, and CIK.

#### Scenario: N-PORT filing is indexed
- **WHEN** an N-PORT filing is ingested for an ETF
- **THEN** the filing index stores both the economic period end date and the date when the filing became publicly available

#### Scenario: Amendment is detected
- **WHEN** a filing amends a previous accession
- **THEN** the filing index links the amendment to the amended accession and preserves both records for point-in-time reconstruction

### Requirement: Point-in-Time Feature Eligibility
The system SHALL include a feature in ELECTRE input for a decision date only when its `public_available_date` is less than or equal to the decision date and its measurement date is not after the decision date.

#### Scenario: Feature was public before rebalance
- **WHEN** a feature has `public_available_date <= decision_date` and no invalid quality flags
- **THEN** the feature is eligible for the ELECTRE feature table for that decision date

#### Scenario: Feature was published after rebalance
- **WHEN** a feature has `public_available_date > decision_date`
- **THEN** the feature is excluded from the ELECTRE feature table for that decision date and reported as unavailable to avoid lookahead bias

#### Scenario: Publication date is unknown
- **WHEN** a source lacks an explicit public availability date
- **THEN** the system applies a conservative lag policy and marks the feature with a fallback quality flag

### Requirement: Fund Snapshot Data
The system SHALL produce fund-level snapshots keyed by ETF and date that include available AUM or net assets, NAV, shares outstanding, expense ratio, issuer, category, asset class, benchmark name, ETF flag, source, confidence, and quality flags.

#### Scenario: Complete fund snapshot
- **WHEN** regulatory or issuer data provides fund metadata for an ETF at a date
- **THEN** the snapshot stores those fields with source references and public availability dates

#### Scenario: Expense ratio missing
- **WHEN** expense ratio is unavailable for an ETF at a decision date
- **THEN** the snapshot records the missing value and the downstream data-quality verdict identifies `expense_ratio` as missing or partial

### Requirement: Holdings Snapshot Data
The system SHALL store holdings snapshots when available, including holding identifiers, market value, weight, shares, asset type, sector, country, source filing, and public availability date.

#### Scenario: Holdings available from N-PORT
- **WHEN** N-PORT holdings are available for an ETF
- **THEN** the system stores holdings with the source filing ID and permits concentration metrics only after the filing is publicly available

#### Scenario: Holdings unavailable
- **WHEN** holdings are unavailable or below quality thresholds
- **THEN** concentration or exposure criteria are marked as missing, optional, or fallback rather than silently imputed as complete

### Requirement: Benchmark Mapping
The system SHALL maintain benchmark mappings with type `official`, `issuer_stated`, `proxy`, `inferred`, or `missing`, including valid dates, confidence, and rationale.

#### Scenario: Official benchmark has public price series
- **WHEN** an ETF has an official benchmark and a public benchmark proxy or tradable benchmark series exists
- **THEN** tracking error may be calculated and labeled with the benchmark mapping type and confidence

#### Scenario: Benchmark is inferred
- **WHEN** no official benchmark is available but category information supports a proxy
- **THEN** the mapping is labeled `inferred` or `proxy` and reports MUST NOT call the resulting tracking error official

### Requirement: ELECTRE Feature Coverage
The system SHALL produce a point-in-time ELECTRE feature table containing the accepted thesis criteria: return, volatility, Sharpe Ratio, liquidity, tracking error, and expense ratio, with source, fallback level, confidence, and quality flags for each value.

#### Scenario: All accepted criteria complete
- **WHEN** every accepted thesis criterion is available from primary or approved fallback sources for the selected universe
- **THEN** the feature coverage report marks the criteria set as complete for the run

#### Scenario: Criterion uses proxy
- **WHEN** a criterion is calculated using a proxy source or benchmark
- **THEN** the feature coverage report records the proxy fallback level and limits the allowed claim for that criterion

### Requirement: Universe Quality Verdict
The system SHALL classify every run with a data-quality verdict that reflects universe mode, source coverage, PIT controls, survivorship limitations, criterion completeness, identifier quality, and benchmark mapping quality.

#### Scenario: Regulatory enriched public PIT run
- **WHEN** a 2021-2024/2025 run uses regulatory and issuer sources, passes PIT eligibility checks, and covers all accepted criteria with documented sources or approved fallbacks
- **THEN** the verdict may be `thesis_aligned_public_regulatory_pit` with explicit public-data limitations

#### Scenario: Static current universe run
- **WHEN** a run uses a static current universe as the primary universe
- **THEN** the verdict MUST remain pilot-only and reports MUST NOT treat it as primary thesis evidence

#### Scenario: Extended historical run lacks complete PIT coverage
- **WHEN** a 2015-2025 run lacks complete regulatory PIT coverage before 2019
- **THEN** the verdict MUST identify the run as extended robustness evidence with degraded claims

### Requirement: Claims Guardrails
The system SHALL enforce report wording that distinguishes permitted public-regulatory claims from prohibited institutional-grade claims.

#### Scenario: Public regulatory universe report
- **WHEN** a report summarizes a regulatory enriched run
- **THEN** it may state that the universe is public/regulatory enriched with approximate PIT controls and MUST disclose remaining public-data limitations

#### Scenario: Unsupported survivor-bias-free claim
- **WHEN** closure/delisting coverage is incomplete or not systematically verified
- **THEN** the report MUST NOT claim the universe is fully survivor-bias-free
