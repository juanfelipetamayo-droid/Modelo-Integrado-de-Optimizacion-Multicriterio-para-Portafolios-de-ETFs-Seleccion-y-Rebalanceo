# Historial de hitos y efecto sobre métricas del portafolio

Fuente máquina:

```text
docs/traceability/milestone_metrics_history.csv
```

> Límite de inferencia: las corridas largas 2015-2025 alcanzan suficiencia OOS en número de folds, pero siguen usando universo público activo/current snapshot y Yahoo Finance; por tanto son evidencia piloto pública, no prueba survivorship-bias-free institucional.

## Tabla comparativa

| Hito | CAGR | Δ CAGR | Sharpe | Δ Sharpe | Max DD | Δ Max DD | Turnover total | Δ Turnover | Calendar | Threshold | Category changes | Cap categoría |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| paper_style_rebalance_only | 13.61% | — | 1.499 | — | -4.23% | — | 2.191 | — | 4 | 0 | 0 | — |
| materiality_confirm2_min030 | 10.79% | -2.82% | 1.162 | -0.336 | -4.94% | -0.72% | 1.500 | -0.691 | 1 | 0 | 1 | — |
| thesis_grade_oos_2015_2025_pilot | -1.08% | -11.87% | 0.011 | -1.152 | -43.55% | -38.60% | 13.611 | 12.111 | 31 | 0 | 0 | — |
| category_cap025_2015_2025 | 0.41% | 1.49% | 0.093 | 0.082 | -24.84% | 18.71% | 10.314 | -3.297 | 31 | 0 | 0 | 25% |
| ready_candidate_every_confirm2_m030_cap025 | 2.47% | 2.06% | 0.247 | 0.154 | -24.01% | 0.82% | 4.016 | -6.298 | 1 | 0 | 4 | 25% |

## Lectura actual

- La validación corta 2020-2024 todavía muestra un modo atractivo (>10% CAGR), pero no es suficiente para presentación como conclusión fuerte.
- La validación pública larga 2015-2025 reveló el problema central: concentración en buckets temáticos/commodities/regionales, turnover alto y drawdown extremo.
- El control `category_exposure_cap=0.25` reduce el Max Drawdown desde -43.55% hasta -24.84% y vuelve positivo el CAGR.
- La configuración candidata de presentación combina:
  - recategorización `every_period`;
  - confirmación de categoría por 2 periodos;
  - materialidad ELECTRE mínima `0.30`;
  - cap de categoría `25%`;
  - drift `buy_and_hold`;
  - ELECTRE Tri pesimista sin veto.
- Esa configuración mejora el OOS largo frente al baseline largo: CAGR de -1.08% a 2.47%, Sharpe de 0.011 a 0.247, Max DD de -43.55% a -24.01%, turnover total de 13.61 a 4.02.

## Conclusión para presentación

El trabajo ya está en estado presentable como investigación honesta: no afirma que ELECTRE supere a SPY/60-40 con datos públicos, sino que demuestra un pipeline reproducible, trazable y extensible que detecta el fallo de generalización y lo mitiga con controles explícitos de concentración y recategorización.

El candidato actual no es todavía una estrategia de inversión final; es el **modelo de tesis defendible** sobre el cual ejecutar la futura versión institucional survivorship-bias-free.
