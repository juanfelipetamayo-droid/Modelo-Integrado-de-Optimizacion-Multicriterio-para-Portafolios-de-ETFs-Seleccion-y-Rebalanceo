# Implementación `align-thesis-objectives`

## Cambios principales

- Se creó `docs/traceability/thesis_objective_alignment.md` para mapear objetivos aceptados, evidencia, estado y brechas.
- Se creó `docs/methodology/thesis_aligned_protocol.md` para separar protocolo principal 2021-2024/2025, robustez 2015-2025 y pilotos.
- Se creó `docs/deliverables/thesis_alignment_completion_report.md` como reporte de cumplimiento y evidencia mínima para defensa.
- Se agregaron `configs/thesis_primary_2021_2025.yaml` y `configs/thesis_extended_2015_2025.yaml`.
- Se agregó `src/etf_optimizer/thesis_alignment.py` con:
  - criterios requeridos de tesis;
  - mapeo de categorías ELECTRE a `excelentes`, `aceptables`, `rechazados`;
  - taxonomía inicial de peer groups ETF;
  - perfiles ELECTRE derivados por peer group con fallback global;
  - regla final de cardinalidad 10-25;
  - auditoría de cobertura y data-quality verdict thesis-aligned.
- Se extendió `src/etf_optimizer/features.py` para soportar `tracking_error`, `expense_ratio` y alias `liquidity`.
- Se extendió `src/etf_optimizer/pipeline.py` para soportar:
  - criterios externos de tesis;
  - perfiles por peer group;
  - selección final thesis-aligned;
  - columnas `thesis_category`, `peer_group` y `profile_scope` en trazabilidad.
- Se actualizó `src/etf_optimizer/reporting/methodology_report.py` para distinguir universo, fuente de precios, rol de validación, criterios faltantes y separación selección/asignación/rebalanceo/evaluación.
- Se agregó fallback markdown en `src/etf_optimizer/thesis_final.py` para no depender de `tabulate` en ambientes de prueba.

## Verificación ejecutada

### Targeted tests

Comando:

```bash
uv run pytest tests/test_features.py tests/test_thesis_alignment.py tests/test_pipeline.py tests/test_methodology_report.py
```

Resultado:

```text
19 passed in 5.03s
```

### Preflight aislado

Comando:

```bash
uv run pytest tests/test_run_sprint_experiment_preflight.py
```

Resultado:

```text
17 passed in 207.10s
```

### Suite completa

Comando:

```bash
uv run pytest
```

Resultado final:

```text
177 passed in 276.19s
```

## Nota de verificación

Antes del resultado final, la suite completa detectó una dependencia opcional faltante (`tabulate`) usada indirectamente por `pandas.DataFrame.to_markdown()` en `thesis_final.py`. Se resolvió con un fallback local sin agregar dependencias nuevas.
