# GOAL 15 — Redacción metodológica defendible para tesis

## Principio de defensa

La tesis debe defender la arquitectura metodológica y la trazabilidad del protocolo, no una promesa de outperformance. Los resultados empíricos se reportan con límites de datos, intervalos de confianza, comparaciones pareadas y sensibilidad de parámetros.

## Frase recomendada

> Dado que no fue posible acceder a una base institucional survivor-bias-free como CRSP, se construyó un universo ETF público aproximado point-in-time a partir de fuentes regulatorias y de mercado, incorporando fechas de disponibilidad de información y etiquetas de calidad. Esta reconstrucción no elimina por completo el riesgo de sesgo de supervivencia, pero permite reducirlo y hacerlo explícito dentro del protocolo de backtesting.

## Claims permitidos

Se puede afirmar que:

- Se construyó un universo ETF público aproximado point-in-time.
- Se evitaron violaciones explícitas de look-ahead mediante `source_available_date`.
- Se etiquetó la calidad de cada observación.
- Se separó selección, asignación y rebalanceo.
- Se comparó ELECTRE Tri frente a FlowSort.
- Se evaluó la clasificación antes del portafolio.
- Se realizaron ablations para aislar fuentes de desempeño.
- Se reportaron intervalos de confianza y pruebas bootstrap pareadas antes de formular conclusiones empíricas.

## Claims prohibidos

No se debe afirmar que:

- La base es completamente survivor-bias-free.
- El modelo vence al mercado.
- ELECTRE optimiza portafolios.
- FlowSort rebalancea.
- El 18% CAGR es evidencia final.
- La corrida pública equivale a CRSP, Morningstar, Lipper, Bloomberg o Refinitiv/LSEG.

## Formulaciones seguras para resultados

Usar estas formulaciones cuando correspondan:

- “presenta mejor desempeño en la muestra”;
- “no presenta evidencia robusta de superioridad”;
- “mejora drawdown pero no CAGR”;
- “mejora estabilidad pero no retorno absoluto”;
- “la evidencia pública actual es diagnóstica y metodológica, no una recomendación de inversión”.

## Separación conceptual obligatoria

- ELECTRE Tri y FlowSort son métodos de clasificación/ordenamiento multicriterio.
- La asignación de pesos pertenece a la etapa posterior de portafolio: EqualWeight, MinVariance, InverseVol o estrategias experimentales.
- El rebalanceo lo ejecuta el motor de backtesting/política de cartera, no FlowSort ni ELECTRE.
- Los benchmarks y ablations deben distinguir selección, asignación y rebalanceo para evitar atribuir performance a la etapa equivocada.
