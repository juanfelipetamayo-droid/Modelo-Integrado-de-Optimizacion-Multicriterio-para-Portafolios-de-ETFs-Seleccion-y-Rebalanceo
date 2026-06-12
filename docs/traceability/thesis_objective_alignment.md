# Alineación de objetivos del trabajo de grado

> Cambio OpenSpec: `align-thesis-objectives`  
> Hallazgos base: `openspec/changes/align-thesis-objectives/findings.md`  
> Fuente de verdad aceptada: `docs/trabajo_de_grado.md`

Este artefacto mapea los objetivos aceptados del trabajo de grado contra el estado actual del proyecto, la evidencia disponible y las brechas que deben resolverse para considerar la implementación totalmente alineada. No reemplaza ni corrige la tesis aceptada; guía la implementación para cumplirla.

## Objetivos aceptados

### Objetivo general

Desarrollar un modelo de optimización de portafolios de inversión basado en ETFs mediante análisis multicriterio, considerando rendimiento, volatilidad, Sharpe Ratio, liquidez, _tracking error_ y _expense ratio_, que sirva como herramienta de toma de decisiones de inversión.

### Objetivo específico 1

Diseñar e implementar un sistema de clasificación multicriterio que reduzca el universo del mercado estadounidense a un conjunto de 10-25 activos sobre datos del 2021-2024.

### Objetivo específico 2

Analizar el desempeño histórico de los ETFs clasificados como elegibles mediante indicadores financieros clave durante el período 2021-2024, con el propósito de caracterizar sus perfiles de riesgo-retorno y validar la consistencia de la selección multicriterio.

### Objetivo específico 3

Desarrollar e implementar un modelo de optimización de portafolios que maximice la rentabilidad ajustada por riesgo, con el propósito de construir portafolios eficientes y validar que el enfoque multicriterio genera mejores rentabilidades ajustadas por riesgo comparado con estrategias de inversión tradicionales.

## Protocolo temporal de alineación

| Periodo | Rol en la tesis | Uso esperado |
|---|---|---|
| 2021-2024 | Desarrollo/calibración aceptado | Construcción de criterios, perfiles, reglas ELECTRE y configuración principal. |
| 2025 | Validación out-of-sample aceptada | Evidencia primaria para validar desempeño y cumplimiento de objetivos. |
| 2015-2025 | Validación extendida | Robustez temporal, sensibilidad a régimen, diagnóstico de sobreajuste y sesgo de universo. No reemplaza el protocolo aceptado. |

## Matriz de trazabilidad

| Objetivo | Capacidades/archivos relacionados | Evidencia actual | Estado | Brechas para cierre |
|---|---|---|---|---|
| Objetivo general | `src/etf_optimizer/features.py`, `src/etf_optimizer/pipeline.py`, `src/etf_optimizer/selection/electre_tri.py`, `src/etf_optimizer/reporting/methodology_report.py`, `scripts/run_sprint_experiment.py` | El pipeline calcula CAGR, volatilidad, Sharpe/Sortino, liquidez por volumen, ejecuta ELECTRE Tri, optimización y reportes walk-forward. | Parcial | Completar `tracking_error` y `expense_ratio` como criterios reales/proxy auditado; etiquetar limitaciones cuando falten. |
| Objetivo específico 1 | `src/etf_optimizer/pipeline.py`, `src/etf_optimizer/selection/electre_tri.py`, futuros helpers thesis-aligned | ELECTRE clasifica y selecciona activos, pero la selección actual no garantiza explícitamente 10-25 ETFs. | En riesgo | Agregar regla final de cardinalidad 10-25; definir peer groups ETF; mantener 2021-2024 como calibración. |
| Objetivo específico 2 | `docs/results/electre_classification_diagnostics.md`, `src/etf_optimizer/reporting/classification_diagnostics.py` | Existen diagnósticos de categorías, forward returns, Jaccard y divergencia pesimista/optimista. | Parcial | Mejorar criterios/perfiles porque `above_preferred` no domina consistentemente; reportar consistencia por categorías de tesis. |
| Objetivo específico 3 | `src/etf_optimizer/optimization/*`, `src/etf_optimizer/backtesting/*`, `docs/performance_blocker_diagnosis.md`, `docs/results/selection_vs_allocation_ablation.md` | Hay optimización, rebalanceo, costos, benchmarks SPY/60-40/EqualWeight/MinVariance y validación extendida. | No validado empíricamente | Ejecutar protocolo principal 2021-2024/2025; separar selección/asignación; reportar si supera o no benchmarks sin ocultar resultados. |

## Criterios de cierre por objetivo

### Objetivo general

- La corrida thesis-aligned incluye los seis criterios aceptados: CAGR, volatilidad, Sharpe Ratio, liquidez, tracking error y expense ratio.
- Si un criterio usa proxy o está incompleto, el data-quality verdict lo declara y el objetivo queda como parcial.

### Objetivo específico 1

- La selección final contiene entre 10 y 25 ETFs.
- La selección se produce a partir de datos disponibles en 2021-2024.
- La selección usa categorías ELECTRE mapeadas a Excelentes, Aceptables y Rechazados.

### Objetivo específico 2

- Se reporta desempeño histórico de ETFs elegibles durante 2021-2024.
- Se valida consistencia de clasificación con monotonicidad forward, estabilidad Jaccard y divergencia pesimista/optimista.

### Objetivo específico 3

- La validación OOS 2025 compara la estrategia contra SPY, 60/40, EqualWeight, MinVariance y same-universe EqualWeight.
- Los reportes identifican selección, asignación, rebalanceo, costos y benchmarks.
- Si no hay superioridad ajustada por riesgo, el objetivo se marca como no validado empíricamente y se documenta el diagnóstico.

## Referencias de evidencia actuales

- `docs/methodology.md`: límites de claims, separación selección/asignación/rebalanceo y criterios reconocidos.
- `docs/performance_blocker_diagnosis.md`: evidencia de degradación 2021-2025 vs 2015-2025.
- `docs/results/electre_classification_diagnostics.md`: no monotonicidad actual de categorías ELECTRE.
- `docs/results/selection_vs_allocation_ablation.md`: comparación selección ELECTRE vs universo y efecto de MaxSharpe.
- `docs/recommended_data_architecture.md`: arquitectura recomendada para universo PIT/aproximado PIT.
