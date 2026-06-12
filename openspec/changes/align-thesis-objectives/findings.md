# Hallazgos de alineación de tesis

Este archivo conserva los hallazgos revisados antes de crear la especificación `align-thesis-objectives`. Su propósito es evitar que se pierda el razonamiento metodológico y servir como referencia para `proposal.md`, `design.md` y los specs del cambio.

## Fuente de verdad aceptada

- `docs/trabajo_de_grado.md` es la fuente de verdad del objetivo general y objetivos específicos aceptados.
- La intención del cambio no es corregir ni reemplazar la tesis aceptada, sino alinear implementación, reportes y metodología con lo que ese documento ya prometió.
- `docs/xidonas_electre_tri_latex_explicado.tex` es la referencia conceptual principal para interpretar la adaptación de Xidonas et al. (2009).

## Objetivos aceptados en el trabajo de grado

### Objetivo general

Desarrollar un modelo de optimización de portafolios de inversión basado en ETFs mediante análisis multicriterio, considerando rendimiento, volatilidad, Sharpe Ratio, liquidez, tracking error y expense ratio, que sirva como herramienta de toma de decisiones de inversión.

### Objetivo específico 1

Diseñar e implementar un sistema de clasificación multicriterio que reduzca el universo del mercado estadounidense a un conjunto de 10-25 activos sobre datos del 2021-2024.

### Objetivo específico 2

Analizar el desempeño histórico de los ETFs clasificados como elegibles mediante indicadores financieros clave durante el período 2021-2024, con el propósito de caracterizar sus perfiles de riesgo-retorno y validar la consistencia de la selección multicriterio.

### Objetivo específico 3

Desarrollar e implementar un modelo de optimización de portafolios que maximice la rentabilidad ajustada por riesgo, con el propósito de construir portafolios eficientes y validar que el enfoque multicriterio genera mejores rentabilidades ajustadas por riesgo comparado con estrategias de inversión tradicionales.

## Estado actual frente a objetivos

| Objetivo | Estado observado | Brecha principal |
|---|---|---|
| Objetivo general | Parcial | CAGR, volatilidad, Sharpe y liquidez están encaminados; tracking error y expense ratio no están completos con datos reales de fondos. |
| Específico 1 | Parcial / en riesgo | ELECTRE clasifica, pero falta garantizar reducción final explícita a 10-25 ETFs y cerrar la narrativa 2021-2024 como calibración. |
| Específico 2 | Parcial | Hay diagnósticos de clasificación, pero `above_preferred` no domina consistentemente en retorno/Sharpe/drawdown forward. |
| Específico 3 | Implementación parcial; resultado no demostrado | Existen optimizadores y benchmarks, pero la validación extendida 2015-2025 no valida superioridad robusta frente a SPY/60-40. |

## Hallazgos metodológicos clave

1. **La tesis aceptada debe guiar la implementación.** El cambio debe adaptar el proyecto al documento aceptado, no reescribir el objetivo central.
2. **La adaptación de Xidonas está incompleta si ELECTRE usa perfiles globales.** Xidonas separa acciones por clases sectoriales y aplica ELECTRE dentro de cada clase. Para ETFs, la adaptación equivalente requiere peer groups: renta variable amplia, sectoriales, renta fija, commodities, internacional, temáticos, alternativas, etc.
3. **El universo no puede depender del conjunto perfecto actual.** `static_current` o universos current-active introducen sesgo de supervivencia/current-universe. El proyecto debe preferir `public_approximate_pit` o una ruta PIT/comercial validada, y reportar limitaciones.
4. **Yahoo/yfinance debe tratarse como fuente de precios, no como autoridad del universo ETF.** La autoridad de universo debe venir de fuentes de universo/snapshots/SEC/Norgate u otra fuente documentada.
5. **Los seis criterios de la tesis deben estar presentes en la ruta principal.** Si tracking error o expense ratio no tienen fuente completa, el sistema debe marcarlos como faltantes/proxy y reportar la limitación.
6. **La cardinalidad 10-25 debe ser una regla verificable.** No basta con clasificar `above_preferred`; debe existir una etapa final que produzca un conjunto candidato dentro del rango prometido.
7. **La clasificación ELECTRE debe validarse antes de la performance del portafolio.** Debe revisarse si Excelentes > Aceptables > Rechazados en métricas forward y estabilidad temporal.
8. **MaxSharpe no debe ocultar el valor de selección.** La tesis debe separar selección, asignación y rebalanceo; MaxSharpe puede ser variante, pero no puede confundirse con ELECTRE.
9. **2021-2024/2025 sigue siendo el periodo principal aceptado.** 2015-2025 debe usarse como validación extendida de robustez, no como sustituto del diseño aprobado.
10. **Los resultados negativos largos son evidencia útil.** Si el modelo no supera benchmarks en 2015-2025, debe reportarse como diagnóstico de robustez, no como razón para alterar la tesis aceptada.

## Archivos de referencia

- `docs/trabajo_de_grado.md`: objetivos aceptados, metodología, criterios, validación y alcance.
- `docs/xidonas_electre_tri_latex_explicado.tex`: adaptación conceptual de Xidonas, clases sectoriales, consistencia temporal y validación.
- `docs/methodology.md`: pipeline actual, claim boundaries y criterios reconocidos/faltantes.
- `docs/performance_blocker_diagnosis.md`: evidencia 2021-2025 vs 2015-2025 y diagnóstico de performance.
- `docs/results/electre_classification_diagnostics.md`: evidencia de no monotonicidad actual de categorías ELECTRE.
- `docs/results/selection_vs_allocation_ablation.md`: separación selección vs asignación y debilidad de ELECTRE/MaxSharpe actual.
- `docs/recommended_data_architecture.md`: propuesta de universo PIT/aproximado PIT y auditoría de datos.
