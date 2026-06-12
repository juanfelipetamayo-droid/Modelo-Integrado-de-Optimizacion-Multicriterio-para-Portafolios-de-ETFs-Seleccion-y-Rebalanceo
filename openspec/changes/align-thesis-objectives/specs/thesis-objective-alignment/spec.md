## ADDED Requirements

### Requirement: Accepted Thesis Objectives Are Source of Truth
The system SHALL treat `docs/trabajo_de_grado.md` as the source of truth for the accepted objective general and three objective específicos when evaluating thesis alignment.

#### Scenario: Objectives are extracted for alignment
- **WHEN** thesis alignment documentation or reports are generated
- **THEN** they MUST include the objective general and three objective específicos from `docs/trabajo_de_grado.md`

#### Scenario: Implementation conflicts with accepted objectives
- **WHEN** a methodological decision conflicts with the accepted thesis objectives
- **THEN** the project MUST document the conflict as a gap instead of silently changing the objective

### Requirement: Findings Reference Is Preserved
The change SHALL preserve the review findings in `openspec/changes/align-thesis-objectives/findings.md` and SHALL reference that file from planning and implementation documentation that explains why alignment work is needed.

#### Scenario: Reader audits the origin of the change
- **WHEN** a reader opens the change proposal, design, specs, or resulting methodology updates
- **THEN** they MUST be able to locate the findings reference and understand the observed gaps

### Requirement: Objective Traceability Matrix
The project SHALL maintain a traceability matrix that maps each accepted objective to implemented components, generated artifacts, experiments, evidence, current status, and remaining gaps.

#### Scenario: Objective compliance is reviewed
- **WHEN** the thesis project is reviewed for compliance
- **THEN** each objective MUST be classified as `cumplido`, `parcial`, `en riesgo`, or `no cumplido` with supporting evidence

#### Scenario: A gap remains unresolved
- **WHEN** an objective is not fully satisfied
- **THEN** the traceability matrix MUST state the missing capability, affected files or artifacts, and required follow-up task

### Requirement: Thesis Language Matches Evidence
The project SHALL ensure final thesis-facing documentation distinguishes between implemented capability, experimental evidence, pilot result, robustness result, and limitation.

#### Scenario: High pilot performance exists
- **WHEN** a pilot window reports high CAGR or Sharpe
- **THEN** the report MUST label it as pilot evidence unless the same claim is supported by the accepted validation protocol and data-quality verdict

#### Scenario: Extended validation underperforms
- **WHEN** extended validation underperforms benchmarks
- **THEN** the report MUST include that result as robustness evidence and MUST NOT omit it from thesis alignment artifacts
