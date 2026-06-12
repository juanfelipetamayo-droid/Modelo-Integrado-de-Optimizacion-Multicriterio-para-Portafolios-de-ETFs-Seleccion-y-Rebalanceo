## ADDED Requirements

### Requirement: Thesis Objective Registry
The system SHALL maintain the accepted thesis objectives and the operational validation wording used by reports, including a realistic formulation of objective 3 that preserves infinitive verbs and avoids assuming benchmark outperformance ex ante.

#### Scenario: Objective 3 is rendered in reports
- **WHEN** the thesis objective summary is generated
- **THEN** objective 3 is rendered as: "Desarrollar e implementar un modelo de optimización de portafolios que busque mejorar la rentabilidad ajustada por riesgo y controlar la exposición al riesgo, con el propósito de construir portafolios eficientes y evaluar empíricamente si el enfoque multicriterio ofrece ventajas frente a estrategias de inversión tradicionales."

#### Scenario: Original accepted objectives are referenced
- **WHEN** the report discusses alignment with the accepted thesis document
- **THEN** it preserves traceability to the original accepted objectives and clearly labels any reformulation as operational, methodological, or reporting-oriented

### Requirement: Objective-to-Data Traceability Matrix
The system SHALL generate or maintain a matrix mapping each thesis objective to required criteria, primary sources, fields or derivations, fallback sources, confidence levels, quality flags, and evidence artifacts.

#### Scenario: Criterion source is complete
- **WHEN** a criterion such as expense ratio is available from an approved source for the decision date
- **THEN** the traceability matrix marks the criterion as covered and records the source, field, date, and confidence

#### Scenario: Criterion source is partial
- **WHEN** a criterion such as tracking error depends on a proxy benchmark
- **THEN** the traceability matrix marks the criterion as partial/proxy and records the fallback level and allowed claim

### Requirement: Objective General Validation
The system SHALL validate the objective general by checking that the run includes return, volatility, Sharpe Ratio, liquidity, tracking error, and expense ratio as ELECTRE criteria or explicitly labeled proxies.

#### Scenario: All six accepted criteria are available
- **WHEN** a run includes all six accepted criteria with complete or approved fallback coverage
- **THEN** the objective general status may be marked as fulfilled or near-fulfilled according to data-quality verdict

#### Scenario: Accepted criterion is missing
- **WHEN** tracking error or expense ratio is missing without approved fallback
- **THEN** the objective general status MUST be marked partial and the missing criterion MUST be listed in the report

### Requirement: Objective 1 Cardinality Validation
The system SHALL validate objective 1 by requiring the final selected ETF set to contain between 10 and 25 assets at each rebalance in the principal 2021-2024/2025 protocol.

#### Scenario: Selection is within target range
- **WHEN** every principal-protocol rebalance selects at least 10 and at most 25 ETFs
- **THEN** objective 1 cardinality status is marked fulfilled for that run

#### Scenario: Selection is outside target range
- **WHEN** any principal-protocol rebalance selects fewer than 10 or more than 25 ETFs
- **THEN** objective 1 cardinality status MUST be marked not fulfilled operationally and the offending dates MUST be reported

### Requirement: Objective 1 Universe Period Validation
The system SHALL validate objective 1 against the 2021-2024 development/calibration period and SHALL separate 2025 out-of-sample evidence from 2015-2025 extended robustness evidence.

#### Scenario: Principal period is used
- **WHEN** the run uses 2021-2024 for development or calibration and 2025 for out-of-sample validation
- **THEN** the report marks the temporal protocol as thesis-aligned

#### Scenario: Extended period is used
- **WHEN** the run uses 2015-2025
- **THEN** the report marks it as robustness evidence and MUST NOT let it replace the principal thesis protocol

### Requirement: Objective 2 Classification Consistency Validation
The system SHALL validate objective 2 using classification diagnostics including forward performance by ELECTRE category, monotonicity, Jaccard stability, turnover, and pessimistic versus optimistic assignment divergence where available.

#### Scenario: Categories are monotonic and stable
- **WHEN** higher ELECTRE categories show better or more robust forward risk-return metrics and acceptable stability across rebalances
- **THEN** objective 2 may be marked fulfilled or strongly supported with diagnostic evidence

#### Scenario: Categories are not consistently monotonic
- **WHEN** higher ELECTRE categories do not dominate lower categories or stability is weak
- **THEN** objective 2 MUST be marked partial and the diagnostics MUST disclose the failure modes

### Requirement: Objective 3 Empirical Benchmark Evaluation
The system SHALL validate objective 3 by evaluating whether the optimized multicriteria portfolio improves risk-adjusted performance or risk control versus traditional strategies, without assuming superiority before results are observed.

#### Scenario: Strategy outperforms benchmarks
- **WHEN** the principal OOS strategy improves risk-adjusted metrics versus SPY, 60/40, and same-universe baselines under documented assumptions
- **THEN** objective 3 may be marked empirically supported and the report records which metrics improved

#### Scenario: Strategy does not outperform benchmarks
- **WHEN** the principal OOS strategy fails to improve risk-adjusted metrics versus benchmarks
- **THEN** objective 3 MUST be marked not empirically validated or partially supported, and the report MUST preserve the negative result and diagnostic explanation

#### Scenario: Strategy controls risk but does not improve return
- **WHEN** the strategy reduces drawdown or volatility but does not improve CAGR or Sharpe
- **THEN** objective 3 may be marked partially supported for risk control only, with no claim of superior risk-adjusted return

### Requirement: Benchmark Set Completeness
The system SHALL compare the thesis strategy against SPY buy-and-hold, 60/40 SPY/BND or documented equivalent, same-universe equal weight, and optimization baselines such as MinVariance where applicable.

#### Scenario: All required benchmarks are present
- **WHEN** all required benchmarks are computed for the same OOS window with compatible assumptions
- **THEN** the benchmark comparison is marked complete

#### Scenario: Benchmark is missing
- **WHEN** a required benchmark cannot be computed
- **THEN** the comparison is marked partial and objective 3 cannot be marked fully empirically supported

### Requirement: Compliance Summary
The system SHALL produce a compliance summary that classifies each objective as fulfilled, near-fulfilled, partial, not fulfilled operationally, or not empirically validated, with evidence paths and blocking gaps.

#### Scenario: Objective status is generated
- **WHEN** a thesis-aligned run completes
- **THEN** the compliance summary lists each objective, status, evidence artifact, data-quality limitations, and next action if incomplete

#### Scenario: Almost complete compliance
- **WHEN** all data, cardinality, consistency, and benchmark evaluation checks pass except for disclosed public-data limitations
- **THEN** the project may report near-complete compliance rather than claiming absolute institutional-grade completeness

### Requirement: Reported Claims Must Match Evidence
The system SHALL ensure claims in methodology and result reports do not exceed the evidence level established by data quality, criterion coverage, and empirical benchmark results.

#### Scenario: Evidence is pilot-only
- **WHEN** a run is classified as pilot-only or partial
- **THEN** reports MUST NOT present it as final thesis-grade evidence

#### Scenario: Objective 3 is negative
- **WHEN** benchmark comparison shows no outperformance or only partial risk-control benefits
- **THEN** reports MUST state that objective 3 was evaluated but not empirically validated as superior
