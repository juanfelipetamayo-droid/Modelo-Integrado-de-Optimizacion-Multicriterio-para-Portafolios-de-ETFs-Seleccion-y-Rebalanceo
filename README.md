# Modelo integrado de optimización multicriterio para portafolios de ETFs: selección y rebalanceo

Trabajo de grado de investigación, Programa de Ingeniería Industrial, Universidad del Valle.
Autor: Juan Felipe Tamayo Mejía. Directores: PhD. Diego Fernando Manotas Duque y PhD. Orlando Joaqui Barandica.

El modelo clasifica ETFs del mercado estadounidense con ELECTRE Tri, conserva como máximo 25 fondos de la categoría superior, asigna capital (equiponderada, mínima varianza y máximo Sharpe), rebalancea cada tres meses y se evalúa mediante simulación con ventanas sucesivas (*walk-forward*) frente a SPY, una cartera 60/40 y el universo equiponderado.

## Instalación

```bash
uv sync --extra dev
uv run pytest -q
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/etf_optimizer/` | Datos y universo invertible, criterios, ELECTRE Tri y FlowSort, optimización, rebalanceo y *backtesting* |
| `scripts/` | Descarga de datos, construcción del universo y simulación (`run_sprint_experiment.py`) |
| `scripts/analisis/` | Universo invertible por año, controles de selección, pruebas *bootstrap* y figuras |
| `configs/` | Configuraciones de criterios y pesos |
| `data/universe/` | Listado de ETFs del buscador de Nasdaq |
| `tests/` | Pruebas automáticas |

Los paneles de precios (`data/`) y los resultados (`results/`, `results_rerun/`) no se versionan por su tamaño; se entregan como anexo comprimido del trabajo.

## Reproducción de los resultados

1. Descargar precios y volúmenes (Yahoo Finance) del listado de Nasdaq y de la SEC:

   ```bash
   uv run python scripts/download_data.py --universe <lista_de_tickers.csv> --start 2015-01-01 --end 2025-12-31 --out data/raw/yfinance_universo_completo
   ```

2. Construir el universo invertible de cada año:

   ```bash
   uv run python scripts/analisis/construir_universo_invertible.py data/raw/yfinance_universo_completo/close.parquet data/raw/yfinance_universo_completo/volume.parquet data/rerun/universo_completo
   ```

3. Ejecutar la simulación (prueba principal; para la ampliada use `--start 2015-01-01`):

   ```bash
   uv run python scripts/run_sprint_experiment.py --universe-mode public_approximate_pit \
     --investable-universe-dir data/rerun/universo_completo/investable_universe_snapshots \
     --prices data/raw/yfinance_universo_completo/close.parquet \
     --volume data/raw/yfinance_universo_completo/volume.parquet \
     --start 2021-01-01 --end 2025-12-31 --rebalance quarterly --weight-drift buy_and_hold \
     --rebalance-policy calendar --electre-assignment pessimistic --cost-bps 10 \
     --min-coverage-pct 0.80 --min-avg-dollar-volume 0 --max-assets 25 \
     --out results_rerun/tope25_primary_2021_2025
   ```

4. Controles, pruebas estadísticas y figuras:

   ```bash
   uv run python scripts/analisis/selecciones_alternativas.py results_rerun/tope25_primary_2021_2025 data/raw/yfinance_universo_completo/close.parquet 2021-01-01 2025-12-31 results_rerun/controles_seleccion_primary.csv
   uv run python scripts/analisis/bootstrap_sharpe.py results_rerun/tope25_primary_2021_2025
   ```

## Licencia de los datos

Los datos provienen de fuentes públicas (Yahoo Finance, Nasdaq y la Comisión de Bolsa y Valores de Estados Unidos) y se usan únicamente con fines académicos.
