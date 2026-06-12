## ADDED Requirements

### Requirement: Thesis Criteria Coverage
The ETF selection pipeline SHALL support the six criteria accepted in the thesis: CAGR, volatility, Sharpe Ratio, liquidity, tracking error, and expense ratio.

#### Scenario: Criteria are available
- **WHEN** a thesis-aligned ELECTRE run is executed
- **THEN** the criteria matrix MUST include CAGR, volatility, Sharpe Ratio, liquidity, tracking error, and expense ratio for each eligible ETF

#### Scenario: A criterion is unavailable
- **WHEN** tracking error, expense ratio, or any accepted criterion cannot be computed from available data
- **THEN** the run MUST be labeled with a data-quality limitation and MUST identify whether a proxy, omission, or external source was used

### Requirement: ELECTRE Categories Match Thesis
The ELECTRE Tri selection SHALL classify ETFs into three thesis-aligned ordered categories: `excelentes`, `aceptables`, and `rechazados`.

#### Scenario: ETF classification is produced
- **WHEN** ELECTRE Tri assigns categories to ETFs
- **THEN** each ETF MUST receive one of `excelentes`, `aceptables`, or `rechazados`, with any internal labels mapped to these thesis terms in reports

### Requirement: Peer Group Adaptation of Xidonas
The project SHALL adapt Xidonas et al. by applying ELECTRE Tri within comparable ETF peer groups rather than relying only on a single global profile across all ETF types.

#### Scenario: Peer groups are configured
- **WHEN** ETF selection is run in thesis-aligned mode
- **THEN** each ETF MUST be assigned to a peer group before ELECTRE profiles are applied

#### Scenario: A peer group has insufficient observations
- **WHEN** a peer group has too few ETFs or insufficient history to estimate stable profiles
- **THEN** the pipeline MUST fall back to a parent peer group or global profile and MUST report that fallback

### Requirement: Final Selection Cardinality
The selection stage SHALL produce a final candidate set of 10 to 25 ETFs for the thesis period unless data-quality constraints make that impossible.

#### Scenario: More than 25 ETFs are excellent
- **WHEN** more than 25 ETFs are classified as `excelentes`
- **THEN** the selector MUST apply a reproducible tie-breaking or ranking rule to retain at most 25 ETFs

#### Scenario: Fewer than 10 ETFs are excellent
- **WHEN** fewer than 10 ETFs are classified as `excelentes`
- **THEN** the selector MUST apply a documented completion rule using the best `aceptables` or MUST mark the run as failing the cardinality objective

### Requirement: Classification Consistency Is Validated Before Portfolio Performance
The project SHALL evaluate ELECTRE classification quality before interpreting portfolio performance.

#### Scenario: Categories are evaluated forward
- **WHEN** category assignments are available for a rebalance date
- **THEN** the system MUST compute forward performance by category to test whether `excelentes` outperform or improve risk-adjusted behavior relative to `aceptables` and `rechazados`

#### Scenario: Classification is unstable
- **WHEN** selected ETF Jaccard similarity or category monotonicity indicates unstable classification
- **THEN** the report MUST identify selection quality as a blocker before optimizing portfolio weights
