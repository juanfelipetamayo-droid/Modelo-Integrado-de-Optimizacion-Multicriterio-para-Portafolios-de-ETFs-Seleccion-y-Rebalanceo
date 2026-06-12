# Manual de usuario del sistema ETF Optimizer

## Propósito

Este manual describe el uso básico del sistema desarrollado para clasificar, optimizar y validar portafolios de ETFs mediante análisis multicriterio. Su finalidad es permitir que un usuario académico reproduzca los experimentos principales del trabajo de grado y regenere las figuras incluidas en el documento.

## Requisitos mínimos

- Sistema con Python administrado mediante `uv`.
- Repositorio del proyecto disponible localmente.
- Paneles de datos en `data/universe_master/derived_panels/`.
- Carpeta de snapshots de universo invertible en `data/universe_master/investable_universe/investable_universe_snapshots`.

## Verificación del entorno

Desde la raíz del proyecto, ejecutar:

```bash
uv run pytest
```

La ejecución registrada para el documento reportó 198 pruebas aprobadas.

## Ejecutar protocolo principal 2021-2025

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

## Ejecutar validación extendida 2015-2025

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

## Generar figuras de tesis

```bash
uv run python scripts/build_thesis_result_figures.py
```

Las figuras se almacenan en `docs/figures/thesis_results` en formatos PNG y PDF.

## Interpretación básica de salidas

- `strategy_comparison.csv`: métricas de desempeño por estrategia.
- `equity_curves.csv`: curvas de capital acumuladas.
- `drawdowns.csv`: caídas máximas desde máximos históricos.
- `electre_selection_by_rebalance.csv`: activos seleccionados en cada fecha de rebalanceo.
- `objective_compliance_summary.csv`: cumplimiento empírico de objetivos.

## Advertencia de uso

El sistema tiene propósito académico y educativo. No constituye recomendación de inversión ni asesoría financiera personalizada.
