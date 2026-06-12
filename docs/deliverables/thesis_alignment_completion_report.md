# Reporte de cumplimiento de objetivos aceptados

> Cambio OpenSpec: `align-thesis-objectives`  
> Trazabilidad: `docs/traceability/thesis_objective_alignment.md`  
> Protocolo: `docs/methodology/thesis_aligned_protocol.md`  
> Hallazgos: `openspec/changes/align-thesis-objectives/findings.md`

## Propósito

Este reporte consolida cómo el proyecto queda orientado a cumplir el objetivo general y los objetivos específicos aceptados en `docs/trabajo_de_grado.md`. No reemplaza los resultados empíricos finales; define qué evidencia debe revisarse para afirmar cumplimiento.

## Estado por objetivo

| Objetivo | Evidencia/artefactos | Estado actual | Cierre esperado |
|---|---|---|---|
| Objetivo general | `src/etf_optimizer/features.py`, `src/etf_optimizer/thesis_alignment.py`, `docs/methodology/thesis_aligned_protocol.md` | Parcial con ruta de cierre | La matriz de criterios debe incluir CAGR, volatilidad, Sharpe, liquidez, tracking error y expense ratio, o declarar limitación. |
| Específico 1 | `src/etf_optimizer/thesis_alignment.py`, `src/etf_optimizer/pipeline.py`, `configs/thesis_primary_2021_2025.yaml` | Parcial con soporte implementado | La corrida principal debe producir 10-25 ETFs finales usando ELECTRE y peer groups. |
| Específico 2 | `src/etf_optimizer/reporting/classification_diagnostics.py`, `docs/results/electre_classification_diagnostics.md` | Parcial | La clasificación debe reportar consistencia por categorías `excelentes`, `aceptables`, `rechazados`. |
| Específico 3 | `configs/thesis_primary_2021_2025.yaml`, `configs/thesis_extended_2015_2025.yaml`, reportes de backtest | No validado hasta ejecutar protocolo | Debe evaluarse 2025 OOS frente a SPY, 60/40, EqualWeight, MinVariance y same-universe EqualWeight. |

## Separación de resultados

| Tipo de resultado | Interpretación permitida |
|---|---|
| Piloto `static_current` o 2021-2025 sin todos los criterios | Desarrollo y diagnóstico, no evidencia principal. |
| Corrida principal 2021-2024/2025 | Evidencia directa de cumplimiento del trabajo de grado. |
| Corrida extendida 2015-2025 | Robustez, sensibilidad a régimen y diagnóstico de generalización. |
| Resultado MaxSharpe | Variante experimental de asignación; no debe atribuirse únicamente a ELECTRE. |

## Evidencia mínima para defensa

1. `criteria_matrix.csv` o equivalente con los seis criterios o limitaciones declaradas.
2. `selection_by_rebalance.csv` con `thesis_category`, `peer_group`, `selected` y cardinalidad final 10-25.
3. Reporte de calidad de datos con modo de universo, fuente de precios, cobertura y claims permitidos.
4. Resultados OOS 2025 contra benchmarks.
5. Robustez 2015-2025 etiquetada como extendida.
6. Diagnóstico de clasificación antes de discutir performance de portafolio.

## Condición de interpretación

Si la corrida principal no supera benchmarks en métricas ajustadas por riesgo, el proyecto sigue aportando evidencia metodológica, pero el objetivo específico 3 debe reportarse como no validado empíricamente para esa configuración. Esta conclusión debe conservarse en la documentación final en lugar de reemplazarse por ventanas piloto con alto CAGR.
