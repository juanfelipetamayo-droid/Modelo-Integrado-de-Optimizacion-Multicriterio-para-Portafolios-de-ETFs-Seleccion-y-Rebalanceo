# Protocolo thesis-aligned para selección y validación ETF

Este documento operacionaliza el cambio `align-thesis-objectives` para que la implementación cumpla los objetivos aceptados en `docs/trabajo_de_grado.md`.

## 1. Ruta de universo válida para evidencia principal

| Modo | Uso permitido | Claim permitido |
|---|---|---|
| `static_current` | Smoke tests, pilotos de desarrollo, comparación diagnóstica | No es evidencia principal; depende del universo activo actual y puede introducir sesgo de supervivencia/current-universe. |
| `point_in_time` | Evidencia principal si la cobertura y fuente son suficientes | Universo observable por fecha de rebalanceo; claim condicionado a calidad/cobertura de fuente. |
| `public_approximate_pit` | Ruta pública principal si no hay base institucional | Aproximación point-in-time pública; reduce y documenta sesgo, pero no es survivor-bias-free institucional. |
| `institutional_survivorship_free` | Ruta ideal si se obtiene fuente comercial/académica | Evidencia thesis-grade si incluye activos/delisted, precios ajustados, eventos y folds OOS suficientes. |

La fuente de universo y la fuente de precios deben reportarse separadas. yfinance/Yahoo puede proveer OHLCV, pero no debe describirse como autoridad del universo ETF.

## 2. Criterios aceptados por la tesis

La corrida principal debe incluir o justificar explícitamente estos seis criterios:

| Criterio | Implementación esperada | Estado si falta |
|---|---|---|
| CAGR | Retorno anual compuesto con datos históricos previos a la decisión. | Incompleto. |
| Volatilidad | Desviación estándar anualizada. | Incompleto. |
| Sharpe Ratio | Exceso de retorno por unidad de riesgo. | Incompleto. |
| Liquidez | Proxy auditable: volumen promedio en dólares u otra fuente documentada. | Parcial si solo hay volumen sin spread. |
| Tracking error | Desviación anualizada del retorno activo contra benchmark del ETF o peer group. | Parcial si se usa proxy de peer group. |
| Expense ratio | Fuente fund-level, SEC/proveedor externo o proxy auditado. | Parcial si no hay fuente real. |

## 3. Adaptación de Xidonas a ETFs

Xidonas aplica ELECTRE Tri dentro de clases sectoriales. La adaptación ETF debe usar peer groups comparables antes de aplicar perfiles:

- `equity_broad`
- `equity_sector`
- `equity_international`
- `fixed_income`
- `commodities`
- `real_assets_alternatives`
- `thematic`
- `leveraged_inverse_special`
- `other`

Si un peer group tiene pocos ETFs o historia insuficiente, el sistema puede usar perfil global como fallback, pero debe reportar `profile_scope=global_fallback`.

## 4. Regla de selección final 10-25

La clasificación ELECTRE produce categorías, pero el objetivo específico 1 exige una selección final entre 10 y 25 activos.

Regla thesis-aligned:

1. Priorizar ETFs `excelentes`.
2. Ordenar por credibilidad ELECTRE.
3. Si hay más de 25, retener los 25 mejores.
4. Si hay menos de 10, completar con los mejores `aceptables` y reportar que la selección usó regla de relleno.
5. Si el universo total no permite llegar a 10, marcar la corrida como incumplimiento de cardinalidad.

## 5. Validación principal y extendida

| Corrida | Periodo | Interpretación |
|---|---|---|
| Principal | 2021-2024 desarrollo/calibración, 2025 OOS | Cumplimiento directo del trabajo de grado. |
| Extendida | 2015-2025 | Robustez, sensibilidad a régimen y diagnóstico de sobreajuste. |

Los reportes deben separar:

1. selección;
2. asignación de pesos;
3. rebalanceo;
4. costos/turnover;
5. evaluación frente a benchmarks.

## 6. Benchmarks mínimos

- SPY buy-and-hold.
- 60/40 SPY/BND.
- EqualWeight.
- MinVariance.
- Same-universe EqualWeight.
- Variantes ELECTRE con EqualWeight, InverseVol, MinVariance restringido y MaxSharpe.

## 7. Reporte de cobertura requerido

Cada corrida thesis-aligned debe reportar:

- requested;
- observed;
- priced;
- sufficient_history;
- liquid;
- eligible;
- final_selected.

## 8. Interpretación de resultados

Si la corrida principal no supera benchmarks en rentabilidad ajustada por riesgo, el objetivo específico 3 queda no validado empíricamente para esa configuración. Ese resultado debe reportarse junto con diagnóstico, no ocultarse ni reemplazarse por una ventana piloto.
