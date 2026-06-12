# GOAL 11 — Elicitación defendible de pesos: BWM/AHP + sensibilidad

## Objetivo

Los pesos manuales dejan de ser la metodología principal. Se conservan únicamente como baseline auditable para comparar contra métodos defendibles de decisión multicriterio.

## Ruta recomendada y estado implementado

| Ruta | Rol metodológico | Estado |
|---|---|---|
| `manual_weights_baseline` | Comparador histórico; no es especificación principal. | Generado en `weights_manual.csv`. |
| `equal_weights_baseline` | Control neutro para detectar dependencia excesiva de pesos expertos. | Generado en `weights_equal.csv`. |
| `BWM_weights_main` | Especificación principal provisional porque BWM requiere menos comparaciones pareadas que AHP cuando hay muchos criterios. | Generado en `weights_bwm.csv`. |
| `random_weight_sensitivity` | Robustez: perturbaciones aleatorias Dirichlet centradas en BWM, sin tuning de performance. | 500 muestras en `weights_sensitivity_samples.csv`. |

## Por qué BWM es la ruta principal

BWM pide seleccionar el mejor y el peor criterio y luego compara el mejor contra los demás y los demás contra el peor. Para un conjunto amplio de criterios ETF es más manejable que AHP completo, que exige muchas comparaciones pareadas y puede volverse costoso de mantener. AHP queda como alternativa posible si el director/profesor entrega una matriz de comparaciones consistente, pero no se inventan juicios humanos.

## Juicios BWM documentados

- Mejor criterio: `rolling_max_drawdown`.
- Peor criterio: `fund_age_months`.
- Xi óptimo de consistencia: `0.023641`.
- Máximo residuo absoluto: `0.023641`.

## Pesos principales BWM

- `momentum_12_1`: peso BWM `0.106383`.
- `volatility_annualized`: peso BWM `0.106383`.
- `rolling_max_drawdown`: peso BWM `0.189125`.
- `rolling_sortino`: peso BWM `0.106383`.
- `avg_dollar_volume`: peso BWM `0.070922`.
- `expense_ratio`: peso BWM `0.070922`.
- `tracking_error_vs_category_benchmark`: peso BWM `0.106383`.
- `beta_vs_category_benchmark`: peso BWM `0.070922`.
- `marginal_correlation_to_selected_universe`: peso BWM `0.106383`.
- `fund_age_months`: peso BWM `0.023641`.
- `aum_usd`: peso BWM `0.042553`.

## Regla de tesis

En resultados principales usar `BWM_weights_main`. Reportar `manual_weights_baseline` y `equal_weights_baseline` como controles, y `random_weight_sensitivity` como sensibilidad. Si no existe elicitation humana del director/profesor, declararlo explícitamente como pendiente.
