# Implementation log — regulatory-enriched-etf-universe

Fecha: 2026-06-12

## Cambio OpenSpec

- Change: `regulatory-enriched-etf-universe`
- Schema: `spec-driven`
- Tasks: 58/58 implemented

## Implementación

Se implementó una capa pública/regulatoria mínima viable y verificable para soportar el nuevo contrato de datos y validación de objetivos:

- `src/etf_optimizer/data/regulatory_universe.py`
  - source registry y política de uso de fuentes;
  - identidad estable ETF con `security_id` no basado solamente en ticker;
  - mappings de identificadores y detección de ambigüedad;
  - filing index EDGAR/N-PORT/N-CEN con fechas de disponibilidad pública;
  - fund snapshots y holdings snapshots con quality flags;
  - price history normalizado y métricas de liquidez;
  - benchmark mapping y tracking error etiquetado por tipo de benchmark;
  - reglas PIT `public_available_date <= decision_date`;
  - features ELECTRE PIT largas con fuente/fallback/confianza;
  - verdict público/regulatorio y guardrails de claims.
- `src/etf_optimizer/thesis_validation.py`
  - objective registry con objetivo 3 operacional reformulado;
  - matriz objetivo → criterio → fuente → fallback → confianza;
  - validaciones para objetivo general, objetivo 1, objetivo 2 y objetivo 3;
  - benchmark completeness y compliance summary.
- `scripts/build_thesis_compliance_artifacts.py`
  - generador de artefactos de cumplimiento desde directorios de resultados.
- `src/etf_optimizer/thesis_alignment.py`
  - verdicts extendidos para `regulatory_enriched_pit`, proxies y claims prohibidos.
- `src/etf_optimizer/reporting/methodology_report.py`
  - limitaciones y guardrails para evidencia pública/regulatoria.
- `scripts/run_sprint_experiment.py`
  - modo y verdict `regulatory_enriched_pit`.
- Configs:
  - `configs/regulatory_thesis_primary_2021_2025.yaml`
  - `configs/regulatory_thesis_extended_2015_2025.yaml`

## Artefactos generados desde resultados existentes

Principal:

- `results/thesis_primary_2021_2025_run_no_cap/objective_feature_coverage.csv`
- `results/thesis_primary_2021_2025_run_no_cap/objective_data_quality_verdict.json`
- `results/thesis_primary_2021_2025_run_no_cap/objective_compliance_summary.csv`
- `results/thesis_primary_2021_2025_run_no_cap/objective_traceability_matrix.csv`
- `results/thesis_primary_2021_2025_run_no_cap/thesis_objective_registry.csv`
- `results/thesis_primary_2021_2025_run_no_cap/objective_compliance_summary.json`

Extendido:

- `results/thesis_extended_2015_2025_run_no_cap/objective_feature_coverage.csv`
- `results/thesis_extended_2015_2025_run_no_cap/objective_data_quality_verdict.json`
- `results/thesis_extended_2015_2025_run_no_cap/objective_compliance_summary.csv`
- `results/thesis_extended_2015_2025_run_no_cap/objective_traceability_matrix.csv`
- `results/thesis_extended_2015_2025_run_no_cap/thesis_objective_registry.csv`
- `results/thesis_extended_2015_2025_run_no_cap/objective_compliance_summary.json`

## Resultado de verificación

Comando ejecutado:

```bash
uv run pytest
```

Resultado:

```text
198 passed in 289.99s (0:04:49)
```

## Lectura metodológica actual

Los artefactos de cumplimiento reflejan honestamente que las corridas existentes todavía quedan como alineación parcial porque faltan `tracking_error` y `expense_ratio` en `features_table.csv`, la selección por rebalanceo no cumple siempre 10-25, y objetivo 3 no queda empíricamente validado frente a benchmarks. La nueva capa deja el contrato y las verificaciones listas para que una corrida futura con datos regulatorios enriquecidos pueda corroborar cumplimiento casi completo sin exceder los claims permitidos.
