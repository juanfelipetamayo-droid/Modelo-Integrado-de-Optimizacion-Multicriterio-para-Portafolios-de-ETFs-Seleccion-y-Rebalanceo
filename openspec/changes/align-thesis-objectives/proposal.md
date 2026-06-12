## Why

El trabajo de grado aceptado define como compromiso central un modelo de portafolios ETF basado en análisis multicriterio, con ELECTRE Tri, reducción del universo a 10-25 activos, optimización posterior y validación frente a benchmarks. La implementación y documentación actuales contienen piezas importantes, pero todavía presentan brechas frente a esos objetivos: criterios incompletos, clasificación ELECTRE poco consistente, falta de cardinalidad explícita, uso parcial de universo point-in-time y resultados largos que no validan robustamente la superioridad esperada.

Esta propuesta alinea el proyecto con el documento aceptado sin reescribir sus objetivos: formaliza qué debe cumplir la implementación, cómo debe trazarse cada objetivo y qué evidencia debe producirse para considerar la tesis metodológicamente satisfecha.

## What Changes

- Crear una especificación de alineación con el trabajo de grado que trate `docs/trabajo_de_grado.md` como fuente de verdad para objetivo general y objetivos específicos.
- Documentar los hallazgos críticos de la revisión en `findings.md` dentro del cambio y referenciarlo desde las especificaciones.
- Exigir trazabilidad explícita entre objetivos aceptados, capacidades implementadas, experimentos ejecutados y evidencia generada.
- Completar la especificación de selección multicriterio ELECTRE Tri para ETFs:
  - criterios prometidos: CAGR, volatilidad, Sharpe Ratio, liquidez, tracking error y expense ratio;
  - categorías: Excelentes, Aceptables y Rechazados;
  - reducción final a 10-25 ETFs;
  - adaptación de Xidonas mediante grupos comparables/peer groups ETF.
- Formalizar la construcción de universo ETF y la calidad de datos:
  - distinguir fuente de universo de fuente de precios;
  - soportar universo dinámico point-in-time o aproximado point-in-time;
  - registrar limitaciones de datos públicos como yfinance/Nasdaq/SEC.
- Formalizar validación y optimización:
  - mantener 2021-2024 como periodo de desarrollo/calibración y 2025 como validación OOS, según el trabajo de grado;
  - usar 2015-2025 como validación extendida de robustez, no como sustituto del periodo aceptado;
  - separar selección, asignación de pesos, rebalanceo y evaluación;
  - comparar contra SPY, 60/40, EqualWeight, MinVariance y baselines del mismo universo.

## Capabilities

### New Capabilities
- `thesis-objective-alignment`: trazabilidad entre objetivos del trabajo de grado aceptado, artefactos del proyecto, evidencia experimental y brechas pendientes.
- `etf-electre-selection`: clasificación multicriterio ELECTRE Tri para ETFs alineada a los criterios, categorías, cardinalidad y adaptación de Xidonas definidos en la tesis.
- `etf-universe-data-quality`: construcción de universo ETF y control de calidad de datos para evitar que resultados dependan del universo perfecto actual.
- `portfolio-validation-protocol`: validación walk-forward, optimización/rebalanceo y comparación frente a benchmarks de acuerdo con los periodos y métricas aceptados.

### Modified Capabilities
- None.

## Impact

- Afecta principalmente documentación metodológica, especificaciones OpenSpec, scripts de experimentación, pipeline de selección/optimización, generación de reportes y trazabilidad de resultados.
- No introduce dependencias obligatorias nuevas por sí mismo; las tareas posteriores podrán definir si `tracking error`, `expense ratio` o datos PIT requieren fuentes adicionales.
- No cambia los objetivos aceptados del trabajo de grado; establece criterios verificables para que código, resultados y documentación queden alineados con ellos.
