# Ranking consolidado de experimentos ETF por CAGR

> Estado: consolidación de hallazgos piloto al 2026-06-02.  
> Criterio principal solicitado: ranking por **CAGR**.  
> Claim boundary: evidencia piloto con datos públicos; no es todavía evidencia thesis-grade ni survivorship-bias-free.

## 1. Decisión de foco

El rango **2021–2025** debe tratarse como el rango principal para documentar los **best performers**, porque con la metodología nueva muestra el mejor equilibrio actual entre retorno, Sharpe y control de drawdown.

El rango más amplio solicitado **2020–2035** se conserva como **alcance adicional**: el `end=2035-12-31` queda registrado, pero los datos locales reales terminan en 2025, así que la simulación efectiva solo cubre 2020–2025. No debe mezclarse con el ranking principal sin advertir esa limitación.

## 2. Ranking principal — 2021–2025 por CAGR

Incluye las dos variantes corridas para 2021–2025: nueva metodología sin cap y nueva metodología con `category_exposure_cap=0.25`.

| Rank | Run | Estrategia | CAGR | Sharpe | Max drawdown |
| --- | --- | --- | --- | --- | --- |
| 1 | 2021-2025 nueva metodología sin cap | SPY_buy_hold | 23.32% | 1.93 | -7.58% |
| 2 | 2021-2025 nueva metodología + cap 25% | SPY_buy_hold | 23.32% | 1.93 | -7.58% |
| 3 | 2021-2025 nueva metodología + cap 25% | ELECTRE_MaxSharpe_walk_forward | 18.08% | 2.59 | -2.40% |
| 4 | 2021-2025 nueva metodología sin cap | 60/40_SPY_BND_fixed_weight | 15.85% | 1.96 | -3.80% |
| 5 | 2021-2025 nueva metodología + cap 25% | 60/40_SPY_BND_fixed_weight | 15.85% | 1.96 | -3.80% |
| 6 | 2021-2025 nueva metodología sin cap | ELECTRE_MaxSharpe_walk_forward | 11.40% | 1.04 | -8.40% |
| 7 | 2021-2025 nueva metodología + cap 25% | EqualWeight_walk_forward | 11.14% | 1.70 | -2.60% |
| 8 | 2021-2025 nueva metodología sin cap | EqualWeight_walk_forward | 11.14% | 1.70 | -2.60% |
| 9 | 2021-2025 nueva metodología sin cap | MaxSharpe_walk_forward | 5.59% | 1.16 | -1.80% |
| 10 | 2021-2025 nueva metodología + cap 25% | MaxSharpe_walk_forward | 5.59% | 1.16 | -1.80% |
| 11 | 2021-2025 nueva metodología + cap 25% | MinVariance_walk_forward | 1.84% | 0.79 | -1.76% |
| 12 | 2021-2025 nueva metodología sin cap | MinVariance_walk_forward | 1.84% | 0.79 | -1.76% |

## 3. Best performer recomendado para 2021–2025

**Ganador metodológico actual:** `ELECTRE_MaxSharpe_walk_forward` con `category_exposure_cap=0.25`.

- Resultado: `results/static_current_quarterly_2021_2025_new_method_cap025_cov095/`
- CAGR: **18.08%**
- Sharpe: **2.59**
- Max drawdown: **-2.40%**
- Volatilidad: **6.54%**
- OOS: **7 folds / 21 periodos OOS**
- Estado estadístico: `pilot_only_oos`

Interpretación: este candidato supera el umbral interno de tesis de `>10%` anualizado y supera a 60/40, EqualWeight, MinVariance y MaxSharpe en CAGR dentro de la muestra piloto. No supera a SPY en CAGR, pero sí mejora Sharpe y drawdown.

## 4. Impacto del cap de exposición

La comparación directa de la misma ventana 2021–2025 muestra que el control de concentración por bucket de riesgo fue material:

| Variante ELECTRE | CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|
| Sin cap | 11.40% | 1.04 | -8.40% |
| Con cap 25% | **18.08%** | **2.59** | **-2.40%** |

Conclusión: el cap de exposición debe mantenerse como componente central de la metodología endurecida, porque mejora retorno y reduce drawdown en esta ventana piloto.

## 5. Cobertura y suficiencia — 2021–2025 cap 25%

| Etapa | Count | % solicitado |
| --- | --- | --- |
| requested | 4554 | 100.00% |
| downloaded | 296 | 6.50% |
| sufficient_history | 75 | 1.65% |
| liquidity_pass | 75 | 1.65% |
| final_eligible | 75 | 1.65% |

La cobertura elegible sigue siendo estrecha: 75 ETFs finales sobre 4,554 solicitados. Por eso el resultado es prometedor pero no concluyente.

## 6. Alcance adicional — rango amplio 2020–2035 solicitado

Este rango queda como validación adicional / sensibilidad, no como ranking principal, porque no hay precios reales 2026–2035 en el parquet local.

Resultado: `results/static_current_quarterly_2020_2035_cov030/`

| Rank | Estrategia | CAGR | Sharpe | Max drawdown |
| --- | --- | --- | --- | --- |
| 1 | SPY_buy_hold | 22.32% | 1.74 | -8.33% |
| 2 | 60/40_SPY_BND_fixed_weight | 14.84% | 1.60 | -6.83% |
| 3 | EqualWeight_walk_forward | 6.80% | 0.90 | -6.39% |
| 4 | ELECTRE_MaxSharpe_walk_forward | 4.70% | 0.48 | -8.40% |
| 5 | MaxSharpe_walk_forward | 2.22% | 0.37 | -5.42% |
| 6 | MinVariance_walk_forward | 2.20% | 0.87 | -1.77% |

Lectura: en el alcance amplio efectivo 2020–2025, ELECTRE queda en **4.70% CAGR**, por debajo de SPY, 60/40 y EqualWeight. Esto debe presentarse como evidencia de robustez parcial/limitación, no como el caso ganador.

## 7. Alcance metodológico point-in-time SEC 2018–2022

Resultado: `results/point_in_time_quarterly_2018_2022_cov100/`

| Rank | Estrategia | CAGR | Sharpe | Max drawdown |
| --- | --- | --- | --- | --- |
| 1 | SPY_buy_hold | 3.93% | 0.29 | -23.93% |
| 2 | 60/40_SPY_BND_fixed_weight | -1.58% | -0.06 | -20.26% |
| 3 | MinVariance_walk_forward | -3.47% | -1.30 | -6.85% |
| 4 | MaxSharpe_walk_forward | -4.24% | -1.26 | -9.02% |
| 5 | EqualWeight_walk_forward | -5.28% | -0.46 | -18.69% |
| 6 | ELECTRE_MaxSharpe_walk_forward | -10.20% | -0.74 | -18.99% |

Lectura: el modo point-in-time reduce sesgo de universo estático, pero el piloto 2018–2022 fue empíricamente débil para ELECTRE. Además, la fuente SEC pública usada actualmente no entrega snapshots 2023–2025 en la URL directa, por lo que no permite aún correr 2021–2025 completo en point-in-time SEC.

## 8. Ranking consolidado de candidatos ELECTRE por CAGR

| Rank | Run | CAGR | Sharpe | Max drawdown | Artefacto |
| --- | --- | --- | --- | --- | --- |
| 1 | 2021-2025 nueva metodología + cap 25% | 18.08% | 2.59 | -2.40% | results/static_current_quarterly_2021_2025_new_method_cap025_cov095 |
| 2 | 2021-2025 nueva metodología sin cap | 11.40% | 1.04 | -8.40% | results/static_current_quarterly_2021_2025_new_method_cov095 |
| 3 | 2020-2035 solicitado (datos efectivos 2020-2025) | 4.70% | 0.48 | -8.40% | results/static_current_quarterly_2020_2035_cov030 |
| 4 | 2018-2022 point-in-time SEC piloto | -10.20% | -0.74 | -18.99% | results/point_in_time_quarterly_2018_2022_cov100 |

## 9. Recomendación para reporte/tesis

1. Presentar **2021–2025 con cap 25%** como el mejor candidato piloto actual.
2. Presentar **2021–2025 sin cap** como ablación que demuestra el valor del control de concentración.
3. Presentar **2020–2035 solicitado / efectivo 2020–2025** como alcance adicional y prueba de sensibilidad que revela degradación fuera del rango ganador.
4. Presentar **point-in-time 2018–2022** como avance metodológico y límite empírico; no usarlo como resultado ganador.
5. Mantener lenguaje cauteloso: “metodológicamente endurecido y empíricamente prometedor en 2021–2025, pero aún piloto”.

## 10. Artefactos fuente

- `results/static_current_quarterly_2021_2025_new_method_cap025_cov095/strategy_comparison.csv`
- `results/static_current_quarterly_2021_2025_new_method_cov095/strategy_comparison.csv`
- `results/static_current_quarterly_2020_2035_cov030/strategy_comparison.csv`
- `results/point_in_time_quarterly_2018_2022_cov100/strategy_comparison.csv`
- `results/static_current_quarterly_2021_2025_new_method_cap025_cov095/paired_benchmark_tests.csv`
- `results/static_current_quarterly_2021_2025_new_method_cap025_cov095/fold_diagnostics.json`
