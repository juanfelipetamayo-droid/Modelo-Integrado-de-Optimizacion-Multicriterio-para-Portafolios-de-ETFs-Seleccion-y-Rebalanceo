# Diseño de criterios v2 para ELECTRE Tri ETF

## Estado y alcance

Este documento corresponde al **GOAL 10**. No modifica todavía el pipeline de backtesting ni los criterios ejecutados por el modelo. Es un artefacto metodológico posterior a los ablations del GOAL 9.

Archivo de configuración asociado:

```text
configs/criteria_config_v2.yaml
```

Límite de inferencia:

> Este rediseño no implica mejora de performance hasta que se implemente end-to-end, se recalculen features/perfiles ELECTRE y se repitan los diagnósticos OOS.

## Evidencia que motiva el rediseño

### GOAL 8: diagnóstico de clasificación

La categoría `above_preferred` no dominó a `between_minimum_preferred` ni a `below_minimum` en métricas forward:

| Categoría | Retorno forward medio | Sharpe forward medio | Drawdown forward medio |
|---|---:|---:|---:|
| `below_minimum` | 0.60% | 0.126 | -5.59% |
| `between_minimum_preferred` | 0.46% | 0.149 | -5.99% |
| `above_preferred` | 0.23% | 0.144 | -7.88% |

Conclusión: la clasificación actual no tiene monotonicidad forward suficiente para defender que ELECTRE está ordenando bien los ETFs.

### GOAL 9: selección vs asignación

| Estrategia | CAGR | Sharpe | MDD |
|---|---:|---:|---:|
| Universe EqualWeight | 5.60% | 0.524 | -20.57% |
| ELECTRE pessimistic no veto EqualWeight | 2.04% | 0.211 | -20.24% |
| ELECTRE pessimistic no veto MaxSharpe | 0.15% | 0.084 | -24.97% |
| Universe MaxSharpe | 2.55% | 0.353 | -16.28% |

Conclusiones:

1. ELECTRE EqualWeight pierde contra Universe EqualWeight, así que la selección no agrega valor neto con los criterios actuales.
2. MaxSharpe empeora tanto dentro de ELECTRE como en el universo completo, así que hay un problema adicional de optimización/estimación.
3. El siguiente paso correcto es rediseñar la clasificación antes de intentar rescatar la asignación MaxSharpe.

## Principios de diseño v2

1. **Eliminar CAGR histórico como criterio primario.** CAGR pasa a ser métrica de evaluación, no criterio dominante de clasificación.
2. **Usar momentum 12-1 en lugar de retorno bruto reciente.** Esto conserva señal de tendencia, pero reduce reversión de corto plazo y performance chasing.
3. **Hacer explícito el control de drawdown.** GOAL 8 mostró que `above_preferred` tuvo peor drawdown forward.
4. **Agregar sensibilidad de mercado y diversificación.** Beta y correlación marginal reducen la probabilidad de seleccionar simplemente ETFs de alta beta o redundantes.
5. **Mover liquidez, AUM y expense ratio a filtros duros o penalizaciones pequeñas.** No deben compensarse fácilmente con retorno pasado.
6. **Eliminar/deferir tracking error si no existe benchmark correcto por categoría.** Un tracking error contra benchmark incorrecto es peor que no usar el criterio.
7. **Agregar filtro de redundancia por correlación.** La selección debe evitar escoger varios ETFs económicamente equivalentes.

## Arquitectura: dos capas

### Capa 1 — filtros duros de invertibilidad

Los filtros duros definen si un ETF puede entrar al MCDM. No son criterios compensatorios.

| Criterio | Fórmula | Lookback | Orientación | Fuente | Missing-data rule | Winsorization | Normalization | Rationale |
|---|---|---|---|---|---|---|---|---|
| `product_type_etf_or_etmf_only` | `product_type in {'ETF','ETMF'}`; excluye mutual funds, CEFs, ETNs y non-funds salvo override explícito | as-of rebalance | pass/fail | SEC Series/Class, N-CEN, Nasdaq Trader, vendor security master | Si falta tipo, inferir por metadata/nombre; si no se resuelve, excluir en thesis-grade | none | none | Mantiene universo homogéneo de ETFs. |
| `exclude_leveraged_inverse_complex` | Rechaza leveraged, inverse, short, bear, volatility-linked o path-dependent ETFs | as-of rebalance | pass/fail | SEC/N-CEN strategy text, Nasdaq, nombres, vendor classifications | Flags faltantes se auditan por regex conservador; casos dudosos se excluyen | none | none | Evita productos con path dependence y riesgo de cola no comparable. |
| `minimum_history_months` | `months_between(max(inception_date, first_valid_total_return_date), rebalance_date) >= 24` | as-of rebalance | maximize | SEC Series/Class, N-CEN, price panel | Usar primer precio válido si falta inception; excluir si ambos faltan | none | none | Reduce estimaciones inestables de riesgo y momentum. |
| `minimum_price_coverage_pct` | `non_missing_total_return_observations / expected_observations >= 0.90` | training window / 24m mínimo | maximize | price panel PIT | Excluir si cobertura < umbral; no zero-fill | none | none | Evita falsos scores por datos faltantes. |
| `minimum_avg_dollar_volume` | `mean(adjusted_close * volume)` trailing 63d >= floor | trailing 63 trading days | maximize | OHLCV vendor / yfinance piloto | Excluir si falta precio/volumen o cobertura < 90% | none | none | Liquidez es invertibilidad, no alpha. |
| `minimum_aum_usd` | AUM PIT >= floor | latest available as-of rebalance | maximize | N-CEN/N-PORT/vendor PIT | En piloto público, no excluir solo por missing; marcar flag y sensitivity | none | none | AUM es estabilidad/invertibilidad, mejor como gate. |
| `maximum_expense_ratio` | `net_expense_ratio <= max` o penalización de costo | latest available as-of rebalance | minimize | prospectus/N-CEN/vendor PIT | No imputar missing como cero; public current data solo piloto | none | none | Costos deben reducir implementabilidad/net return. |
| `minimum_price_usd` | adjusted close latest <= rebalance date >= floor | rebalance/prior trading day | maximize | price panel | Excluir si no hay precio alineable | none | none | Evita quotes distorsionadas o fondos problemáticos. |

### Capa 2 — criterios MCDM

Estos criterios entran en ELECTRE Tri después de pasar filtros duros. Los pesos propuestos suman 1.00 y son **provisionales** hasta validación de monotonicidad forward.

| Criterio | Peso | Fórmula | Lookback | Orientación | Fuente | Missing-data rule | Winsorization | Normalization | Rationale |
|---|---:|---|---|---|---|---|---|---|---|
| `momentum_12_1` | 0.18 | `prod(1 + monthly_total_returns[t-12:t-1]) - 1` | trailing 12 months skip 1 month | maximize | adjusted/total-return series | Requiere >=11 retornos mensuales; si no, excluir ETF/fold | 5/95 cross-section | robust z-score | Sustituye CAGR histórico por momentum más defendible y con peso limitado. |
| `volatility_12m` | 0.12 | `std(monthly_returns_12m) * sqrt(12)` | trailing 12 months | minimize | adjusted/total-return series | Requiere >=11 retornos | 5/95 | robust z-score, menor mejor | Control básico de riesgo. |
| `max_drawdown_24m` | 0.20 | `min(cumulative_return_path / running_max - 1)` | trailing 24 months | maximize | adjusted/total-return series | Requiere >=21 retornos | 5/95 | robust z-score, más cerca de 0 mejor | Principal corrección por GOAL 8: drawdown forward falló. |
| `downside_risk_sortino_24m` | 0.12 | annualized mean excess return / downside deviation | trailing 24 months | maximize | returns + risk-free | Downside deviation cero se capa; observaciones insuficientes excluyen | 5/95 tras cap | robust z-score | Riesgo ajustado sin depender de MaxSharpe. |
| `beta_to_spy_24m` | 0.10 | `cov(ETF, SPY) / var(SPY)` | trailing 24 months | minimize | ETF returns + SPY total-return | Requiere >=21 pares; si no, flag/excluir criterio | clip [-1,3], luego 5/95 | robust z-score | Controla exposición de mercado; evita elegir solo alta beta. |
| `marginal_correlation_to_eligible_universe_24m` | 0.12 | media de correlaciones con ETFs elegibles | trailing 24 months | minimize | price panel PIT | Requiere peers suficientes; si bajo peer count, flag | bounds [-1,1] | robust z-score | Introduce diversificación directamente en clasificación. |
| `liquidity_penalty_log_adv` | 0.06 | `log1p(mean(adjusted_close * volume))` tras pasar floor | trailing 63 trading days | maximize | OHLCV | Debe existir tras gate; si no, excluir | 1/99 after log1p | robust z-score | Preferencia secundaria por tradabilidad. |
| `fund_age_stability_months` | 0.05 | months since inception/first_seen, cap 180 | as-of rebalance | maximize | SEC/N-CEN/vendor/price fallback | Usar first valid price fallback con flag | cap 180 | min-max or robust z-score | Penaliza fondos demasiado nuevos. |
| `expense_ratio_penalty` | 0.05 | latest PIT net expense ratio | latest as-of rebalance | minimize | prospectus/N-CEN/vendor PIT | Si no hay PIT, omitir criterio, no usar current backfill | 1/99 if enough obs | robust z-score | Penaliza costos solo cuando la fuente es PIT defendible. |

## Criterios eliminados o diferidos

| Criterio | Decisión | Rationale |
|---|---|---|
| `historical_cagr` | Eliminar del MCDM primario | GOAL 8 mostró que el ranking histórico no se tradujo en forward superiority. |
| `raw_recent_return` | Reemplazar por `momentum_12_1` | Reduce reversión de corto plazo y performance chasing. |
| `tracking_error_vs_category_benchmark` | Diferir | Sin benchmark correcto por categoría, el criterio es metodológicamente débil. |
| `avg_dollar_volume` como score principal | Mover a filtro + penalización pequeña | Liquidez define invertibilidad; no debe compensar drawdown malo. |
| `aum_usd` como score principal | Mover a filtro o optional zero-weight | Fuente PIT limitada; no contaminar piloto público. |
| `expense_ratio` como score principal | Hard filter o penalización opcional | No usar metadata actual no-PIT para clasificar pasado. |

## Filtro de redundancia por correlación

Después de ELECTRE, antes de producir la selección final:

```text
Si dos o más ETFs aceptados/excelentes tienen correlación trailing 24m >= 0.90,
formar cluster y mantener el ETF con mayor composite MCDM score y liquidez adecuada.
```

Campos requeridos:

| Campo | Regla |
|---|---|
| formula | correlación mensual trailing 24m entre candidatos aceptados/excelentes |
| lookback | trailing 24 months |
| orientation | minimize redundancy |
| source | adjusted/total-return series |
| missing-data rule | si falta ventana, no excluir solo por redundancia; flag `incomplete_redundancy_check` |
| winsorization | correlación ya está en [-1,1] |
| normalization | no normalizado; post-classification cluster filter |
| rationale | reduce selección de ETFs duplicados y mejora interpretabilidad/turnover |

## Perfil ELECTRE v2

La configuración v2 propone perfiles por cuantiles cross-sectional, no umbrales fijos heredados:

```text
minimum profile:   quantile 40%
preferred profile: quantile 70%
```

Justificación:

- El universo PIT público cambia de tamaño y composición por año.
- Los criterios v2 usan escalas heterogéneas y robust z-scores.
- Umbrales fijos legacy pueden volver artificialmente fácil/difícil estar en `above_preferred`.

Sensibilidad requerida:

```text
lambda_cut: 0.65, 0.70, 0.75, 0.80
assignment: pessimistic/optimistic × with/without veto
```

## Plan de implementación posterior

No ejecutar todavía como parte de GOAL 10. Próximo hito sugerido:

1. Crear validadores para `configs/criteria_config_v2.yaml`.
2. Implementar features nuevas: `momentum_12_1`, `max_drawdown_24m`, `beta_to_spy_24m`, `marginal_correlation_to_eligible_universe_24m`.
3. Implementar perfiles ELECTRE por cuantiles cross-sectional.
4. Implementar filtro de redundancia por correlación.
5. Repetir primero GOAL 8 con criterios v2.
6. Solo si la clasificación se vuelve monotónica, repetir GOAL 9 con EqualWeight, InverseVol y MinVariance.
7. Mantener MaxSharpe como diagnóstico, no como candidato principal, hasta demostrar que no destruye la selección.

## Definition of Done del GOAL 10

Cumplido por:

```text
configs/criteria_config_v2.yaml
docs/methodology/criteria_design_v2.md
```

Ambos incluyen para cada criterio:

```text
formula
lookback
orientation
source
missing-data rule
winsorization
normalization
rationale
```
