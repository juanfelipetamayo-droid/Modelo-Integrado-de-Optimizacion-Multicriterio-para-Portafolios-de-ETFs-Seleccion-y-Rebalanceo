## ADDED Requirements

### Requirement: Universe Source Is Separate From Price Source
The project SHALL distinguish the authority used to define ETF universe membership from the source used to obtain prices and volumes.

#### Scenario: yfinance prices are used
- **WHEN** yfinance or another public price API supplies OHLCV data
- **THEN** the report MUST NOT describe that source as the universe authority unless it also provides auditable ETF universe membership

### Requirement: Dynamic Universe by Decision Date
The ETF universe SHALL be constructed dynamically by decision or rebalance date for thesis-aligned backtests.

#### Scenario: Rebalance universe is built
- **WHEN** the system prepares a rebalance date
- **THEN** it MUST include only ETFs that are observable and eligible as of that date according to the selected universe provider

#### Scenario: Static current universe is used
- **WHEN** a static current universe is used for smoke tests or pilot diagnostics
- **THEN** the run MUST be labeled as non-thesis-grade and MUST NOT be used as primary evidence of objective fulfillment

### Requirement: Data Quality Verdict
Each thesis-aligned run SHALL emit or reference a data-quality verdict that describes universe quality, price coverage, criterion coverage, and survivorship-bias limitations.

#### Scenario: Public approximate PIT data is used
- **WHEN** public approximate point-in-time data is used
- **THEN** the verdict MUST state that survivorship bias is reduced or made explicit but not fully eliminated

#### Scenario: Criterion coverage is incomplete
- **WHEN** any accepted criterion is missing for part of the universe
- **THEN** the verdict MUST include coverage counts and whether the run remains valid for thesis-aligned evidence

### Requirement: ETF Lifecycle Changes Are Accounted For
The universe layer SHALL account for ETF entries, exits, delistings, mergers, ticker changes, and insufficient-history cases when such information is available.

#### Scenario: ETF starts after rebalance date
- **WHEN** an ETF first becomes observable after a rebalance date
- **THEN** the ETF MUST NOT be eligible for that rebalance

#### Scenario: ETF disappears before or during a holding period
- **WHEN** an ETF termination, delisting, merger, or last-observed date affects a selected ETF
- **THEN** the backtest MUST apply a documented handling rule and report the event

### Requirement: Coverage Reports Are Generated
The project SHALL produce coverage evidence for universe construction and filtering.

#### Scenario: Universe funnel is reported
- **WHEN** a thesis-aligned run completes
- **THEN** the report MUST include requested, observed, priced, sufficient-history, liquid, and final-selected counts
