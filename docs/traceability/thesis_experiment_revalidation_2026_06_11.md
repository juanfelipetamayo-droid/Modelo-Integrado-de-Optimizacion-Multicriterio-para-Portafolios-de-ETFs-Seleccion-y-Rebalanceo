# Revalidación experimental contra objetivos aceptados

Fecha: 2026-06-11  
Cambio relacionado: `align-thesis-objectives`  
Fuente de verdad: `docs/trabajo_de_grado.md`  
Hallazgos base: `openspec/changes/align-thesis-objectives/findings.md`

## Comandos ejecutados

### Preparación de paneles locales

El dataset local disponible estaba en formato largo: `data/universe_master/price_ohlcv.parquet`. Se derivaron paneles wide para el runner:

- `data/universe_master/derived_panels/close.parquet`
- `data/universe_master/derived_panels/volume.parquet`

Cobertura: 296 tickers, 2765 fechas, desde 2015-01-02 hasta 2025-12-30.

### Corrida principal 2021-2025

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe-mode public_approximate_pit \
  --investable-universe-dir data/universe_master/investable_universe/investable_universe_snapshots \
  --prices data/universe_master/derived_panels/close.parquet \
  --volume data/universe_master/derived_panels/volume.parquet \
  --start 2021-01-01 \
  --end 2025-12-31 \
  --rebalance quarterly \
  --weight-drift buy_and_hold \
  --rebalance-policy calendar \
  --electre-assignment pessimistic \
  --cost-bps 10 \
  --min-coverage-pct 0.80 \
  --min-avg-dollar-volume 0 \
  --out results/thesis_primary_2021_2025_run_no_cap
```

Intento con `--category-exposure-cap 0.25`: falló por restricción inviable de grupos activos. Se conserva como hallazgo de robustez: el cap de exposición requiere manejo de factibilidad antes de usarse como configuración principal.

### Corrida extendida 2015-2025

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe-mode public_approximate_pit \
  --investable-universe-dir data/universe_master/investable_universe/investable_universe_snapshots \
  --prices data/universe_master/derived_panels/close.parquet \
  --volume data/universe_master/derived_panels/volume.parquet \
  --start 2015-01-01 \
  --end 2025-12-31 \
  --rebalance quarterly \
  --weight-drift buy_and_hold \
  --rebalance-policy calendar \
  --electre-assignment pessimistic \
  --cost-bps 10 \
  --min-coverage-pct 0.80 \
  --min-avg-dollar-volume 0 \
  --out results/thesis_extended_2015_2025_run_no_cap
```

### Diagnósticos de clasificación

Se generaron diagnósticos ELECTRE por categoría para ambas corridas:

- `results/thesis_primary_2021_2025_run_no_cap/electre_classification_diagnostics.md`
- `results/thesis_extended_2015_2025_run_no_cap/electre_classification_diagnostics.md`

## Calidad de datos y cobertura

| Corrida | Universo | Verdict | Survivorship-bias-free | Tickers solicitados | Tickers con datos | Cobertura periodos | OOS folds / meses |
|---|---|---|---|---:|---:|---:|---:|
| Principal 2021-2025 | `public_approximate_pit` | `public_point_in_time_pilot` | No | 52 | 52 | 96.17% | 7 / 21 |
| Extendida 2015-2025 | `public_approximate_pit` | `public_point_in_time_pilot` | No | 52 | 52 | 96.34% | 31 / 93 |

Interpretación: la corrida extendida tiene suficiencia OOS según conteo de folds/meses, pero ambas siguen limitadas por datos públicos aproximados PIT y no son evidencia institucional survivor-bias-free.

## Resultados de desempeño

### Principal 2021-2025

| Estrategia | CAGR | Sharpe | Max drawdown | Lectura |
|---|---:|---:|---:|---|
| ELECTRE EqualWeight | 12.88% | 1.198 | -7.54% | Supera el umbral interno de 10% CAGR, pero no supera a SPY ni 60/40. |
| ELECTRE MinVariance | 12.47% | 1.236 | -6.56% | Similar a ELECTRE EW, con menor drawdown. |
| ELECTRE MaxSharpe | 10.97% | 1.034 | -7.62% | Variante experimental; peor que ELECTRE EW/MV. |
| SPY buy-and-hold | 23.32% | 1.932 | -7.58% | Benchmark dominante en CAGR y Sharpe. |
| 60/40 SPY/BND | 15.85% | 1.964 | -3.80% | Supera a ELECTRE en CAGR, Sharpe y drawdown. |
| Universe EqualWeight | 11.98% | 1.695 | -3.48% | ELECTRE EW mejora CAGR levemente, pero con peor Sharpe/drawdown. |

### Extendida 2015-2025

| Estrategia | CAGR | Sharpe | Max drawdown | Lectura |
|---|---:|---:|---:|---|
| ELECTRE EqualWeight | 3.78% | 0.332 | -20.45% | Positivo, pero débil frente a benchmarks. |
| ELECTRE MinVariance | 3.40% | 0.320 | -20.23% | Similar a ELECTRE EW. |
| ELECTRE MaxSharpe | 2.67% | 0.257 | -21.06% | Variante experimental inferior. |
| SPY buy-and-hold | 13.85% | 0.867 | -23.93% | Muy superior en CAGR/Sharpe. |
| 60/40 SPY/BND | 9.16% | 0.844 | -20.26% | Supera claramente a ELECTRE. |
| Universe EqualWeight | 6.36% | 0.583 | -18.57% | Supera a ELECTRE; confirma que selección actual no agrega valor neto robusto. |

## Diagnóstico de selección ELECTRE

### Cardinalidad

| Corrida | Seleccionados promedio por rebalance | Mín | Máx | Cumple 10-25 por rebalance |
|---|---:|---:|---:|---|
| Principal 2021-2025 | 4.43 | 1 | 10 | No |
| Extendida 2015-2025 | 5.29 | 1 | 11 | No |

Aunque la selección agregada del runner reportó 14 activos en la principal y 27 en la extendida, el objetivo específico 1 exige una reducción operacional a 10-25 activos; por rebalanceo, la implementación ejecutada aún no cumple de forma consistente.

### Calidad ordinal por categoría

| Corrida | `above_preferred` vs categorías inferiores | Lectura |
|---|---|---|
| Principal 2021-2025 | Mejor retorno/Sharpe promedio agregado, pero solo 7 folds y 21 meses OOS. | Señal prometedora, aún piloto. |
| Extendida 2015-2025 | `above_preferred` mejora retorno/Sharpe promedio levemente, pero tiene peor drawdown promedio que categorías inferiores y varios folds no monotónicos. | Consistencia parcial; no suficiente para declarar clasificación robusta. |

Jaccard de seleccionados:

- Principal: variable, con mínimo 0.00 y varios cambios fuertes entre folds.
- Extendida: varios tramos con Jaccard 0.00 durante 2020-2021, confirmando inestabilidad en cambios de régimen.

## Revalidación contra hallazgos originales

| Hallazgo original | Resultado revalidado |
|---|---|
| 2021-2025 puede verse atractivo pero no es evidencia final | Confirmado. ELECTRE EW da 12.88% CAGR, pero queda debajo de SPY y 60/40 y solo tiene 21 meses OOS. |
| 2015-2025 expone caída de generalización | Confirmado. ELECTRE EW cae a 3.78% CAGR y queda debajo de Universe EW, 60/40 y SPY. |
| Universo público PIT aproximado reduce sesgo, pero no es survivor-bias-free | Confirmado por `data_quality_verdict.json`: `public_point_in_time_pilot`, `survivorship_bias_free=false`. |
| ELECTRE debe validarse antes de optimizar | Confirmado. La clasificación muestra señal parcial, pero no monotonicidad robusta ni cardinalidad consistente. |
| MaxSharpe no debe ser motor principal | Confirmado. MaxSharpe es peor que EqualWeight/MinVariance en ambas corridas. |
| Cap 25% puede ser útil, pero debe ser factible | Nuevo hallazgo: con esta data/configuración, el cap 25% falló por restricción inviable. |

## Revalidación contra objetivos aceptados

| Objetivo | Estado después de corridas | Evidencia |
|---|---|---|
| Objetivo general | Parcial | El pipeline evalúa rendimiento, volatilidad, Sharpe y liquidez; las corridas ejecutadas no incluyeron tracking error ni expense ratio reales. |
| Objetivo específico 1 | No cumplido operacionalmente | La selección por rebalanceo no mantiene 10-25 activos; principal promedio 4.43, extendida promedio 5.29. |
| Objetivo específico 2 | Parcial | Hay análisis de desempeño por categoría; la principal muestra señal piloto, la extendida muestra señal débil/no robusta. |
| Objetivo específico 3 | No validado empíricamente | ELECTRE no supera a SPY/60-40 en principal ni extendida; en extendida tampoco supera Universe EqualWeight. |

## Conclusión

La implementación está mejor alineada en trazabilidad y estructura metodológica, pero las corridas actuales todavía no cumplen plenamente los objetivos aceptados. La brecha principal ya no es solo supervivencia del universo: también faltan criterios ETF completos, cardinalidad 10-25 por rebalanceo, y robustez de la clasificación ELECTRE frente a benchmarks simples.

La tesis puede avanzar, pero la siguiente iteración debe ejecutar una corrida verdaderamente `thesis-aligned` que active la regla de cardinalidad 10-25, complete o etiquete tracking error/expense ratio, y use peer groups ELECTRE en el runner final.
