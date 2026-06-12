## ADDED Requirements

### Requirement: Accepted Period Protocol
The validation protocol SHALL preserve the accepted thesis period structure: 2021-2024 for development/calibration and 2025 for out-of-sample validation.

#### Scenario: Primary thesis run is executed
- **WHEN** the primary thesis-aligned experiment is run
- **THEN** training, calibration, or profile selection MUST use data available through 2021-2024 and MUST evaluate 2025 as out-of-sample evidence

### Requirement: Extended Robustness Validation
The project SHALL use 2015-2025 as extended robustness validation and SHALL NOT treat it as a replacement for the accepted 2021-2024/2025 protocol.

#### Scenario: Extended validation is reported
- **WHEN** 2015-2025 results are generated
- **THEN** the report MUST label them as robustness or sensitivity evidence and compare them to the primary thesis-period results

### Requirement: Selection Allocation Rebalancing Evaluation Separation
The validation pipeline SHALL separately report selection quality, allocation method, rebalancing behavior, and portfolio performance.

#### Scenario: Portfolio performance is reported
- **WHEN** a strategy row is included in a performance table
- **THEN** the row MUST identify selection method, allocation method, rebalance frequency, cost assumption, and universe mode

#### Scenario: ELECTRE is used with an optimizer
- **WHEN** ELECTRE-selected ETFs are passed to MaxSharpe, MinVariance, EqualWeight, InverseVol, or another allocator
- **THEN** the report MUST NOT attribute allocation effects solely to ELECTRE

### Requirement: Benchmark Comparison
Thesis-aligned validation SHALL compare the portfolio against SPY, 60/40, EqualWeight, MinVariance, and a same-universe baseline.

#### Scenario: Benchmarks are generated
- **WHEN** validation results are produced
- **THEN** benchmark rows MUST be aligned to the same out-of-sample dates and labeled to distinguish walk-forward strategies from buy-and-hold references

#### Scenario: Same-universe baseline is available
- **WHEN** the universe contains multiple eligible ETFs
- **THEN** a same-universe EqualWeight baseline MUST be included to isolate whether ELECTRE selection adds value over the eligible universe

### Requirement: Objective 3 Evidence Is Explicit
The project SHALL explicitly state whether the optimized portfolio validates better risk-adjusted performance versus traditional strategies for the accepted validation period.

#### Scenario: Portfolio beats benchmarks
- **WHEN** the thesis-aligned portfolio outperforms benchmarks on risk-adjusted metrics
- **THEN** the report MUST state the metric, benchmark, period, confidence evidence, and data-quality verdict supporting that result

#### Scenario: Portfolio does not beat benchmarks
- **WHEN** the thesis-aligned portfolio does not outperform benchmarks
- **THEN** the report MUST state that objective 3 is not empirically validated by that run and MUST provide diagnostic evidence rather than suppressing the result

### Requirement: Transaction Costs and Turnover Are Reported
Validation SHALL include turnover and transaction-cost-adjusted results.

#### Scenario: Rebalance occurs
- **WHEN** weights change at a rebalance date
- **THEN** the system MUST record turnover and apply the configured transaction cost assumption in cost-adjusted returns
