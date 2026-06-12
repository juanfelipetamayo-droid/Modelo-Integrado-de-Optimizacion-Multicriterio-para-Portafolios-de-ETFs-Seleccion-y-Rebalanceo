# Weight consistency report — GOAL 11

## Alcance

Este reporte formaliza pesos para los criterios MCDM de ETFs definidos en `configs/criteria_config.yaml`.
Los pesos manuales se conservan solo como baseline; el método principal documentado es BWM por requerir menos comparaciones que AHP para muchos criterios financieros.

## Mini-elicitation documentada

| Rol | Estado | Uso en este hito |
|---|---|---|
| experto 1: investigador/Hermes | Disponible | `BWM_weights_main` |
| experto 2: director/profesor | Pendiente de elicitation humana | No se inventan preferencias; registrar cuando esté disponible |
| experto 3: literatura/criterio institucional | Aproximado documentalmente | Usado en racionales y estructura de criterios; no sustituye experto humano |

## Rutas de pesos generadas

- `manual_weights_baseline`: baseline documentado, no método principal.
- `BWM_weights_main`: método principal provisional para tesis hasta recibir experto 2.
- `equal_weights_baseline`: control neutro.
- `random_weight_sensitivity`: 500 muestras aleatorias centradas en BWM para robustez.

## Consistencia BWM

- Mejor criterio: `rolling_max_drawdown`.
- Peor criterio: `fund_age_months`.
- Xi óptimo: `0.023641`.
- Máximo residuo absoluto: `0.023641`.
- Interpretación: menor Xi implica comparaciones más consistentes; este reporte debe actualizarse si el director/profesor entrega juicios distintos.

## Pesos BWM researcher

| Criterio | Peso | Racional |
|---|---:|---|
| momentum_12_1 | 0.106383 | Captura persistencia intermedia sin usar CAGR histórico dominante. |
| volatility_annualized | 0.106383 | Controla riesgo total ex ante dentro de la clasificación MCDM. |
| rolling_max_drawdown | 0.189125 | Prioridad principal BWM: limita fragilidad de cola observada en OOS largo. |
| rolling_sortino | 0.106383 | Premia retorno ajustado por downside sin depender de CAGR puro. |
| avg_dollar_volume | 0.070922 | Asegura liquidez operable después de filtros duros. |
| expense_ratio | 0.070922 | Penaliza fricción estructural del ETF. |
| tracking_error_vs_category_benchmark | 0.106383 | Favorece eficiencia de implementación frente al benchmark correcto. |
| beta_vs_category_benchmark | 0.070922 | Controla sensibilidad sistemática por categoría. |
| marginal_correlation_to_selected_universe | 0.106383 | Introduce beneficio de diversificación marginal. |
| fund_age_months | 0.023641 | Criterio secundario; estabilidad operativa, no driver principal. |
| aum_usd | 0.042553 | Proxy de escala/viabilidad, subordinado a riesgo y calidad de seguimiento. |

## Regla académica

No usar pesos manuales como resultado principal. La tesis debe reportar BWM como especificación primaria, equal-weight como baseline y random-weight sensitivity como robustez. Si experto 2 no está disponible, declarar explícitamente `director/profesor pendiente` y no presentarlo como juicio observado.
