# Anexo de validación metodológica

## Alcance

Este anexo documenta la validación metodológica disponible para el trabajo de grado. No corresponde a un acta firmada de validación por usuario externo; representa una validación técnica y documental basada en pruebas automatizadas, trazabilidad de objetivos, ejecución de experimentos y comparación frente a benchmarks.

## Evidencias revisadas

| Evidencia | Archivo o comando | Resultado |
|---|---|---|
| Suite de pruebas | `uv run pytest` | 198 pruebas aprobadas |
| Protocolo principal | `results/thesis_primary_2021_2025_run_no_cap` | Resultados 2021-2025 generados |
| Validación extendida | `results/thesis_extended_2015_2025_run_no_cap` | Resultados 2015-2025 generados |
| Figuras de tesis | `uv run python scripts/build_thesis_result_figures.py` | 24 archivos PNG/PDF generados |
| Trazabilidad de objetivos | `docs/traceability/thesis_objective_alignment.md` | Objetivos, evidencia y brechas documentadas |
| Revalidación experimental | `docs/traceability/thesis_experiment_revalidation_2026_06_11.md` | Comparación contra objetivos aceptados |

## Resultado de la validación

La validación confirma que el sistema implementa un pipeline funcional de selección, optimización y evaluación de portafolios de ETFs. Sin embargo, también confirma tres brechas principales: falta de incorporación completa de tracking error y expense ratio en las corridas finales, incumplimiento operacional de la cardinalidad 10-25 por rebalanceo y ausencia de superioridad empírica frente a benchmarks tradicionales.

## Uso en el documento final

Este anexo debe citarse como evidencia de revisión técnica y metodológica. Si posteriormente se obtiene una validación firmada por experto, entrevista o acta de revisión con directores, ese instrumento debe reemplazar o complementar este anexo.
