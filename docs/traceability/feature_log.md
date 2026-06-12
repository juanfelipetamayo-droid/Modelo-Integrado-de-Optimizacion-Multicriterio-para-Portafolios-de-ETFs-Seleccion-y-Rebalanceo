# Registro de trazabilidad de funcionalidades e investigación

Este archivo registra cambios funcionales, planes y entregables de investigación para que el usuario pueda auditar qué se hizo, por qué y cómo verificarlo.

---

## 2026-06-10 — GOAL 13 backtest final congelado thesis-grade

**Tipo:** corrida final reproducible / backtest OOS  
**Comando único:**

```bash
python main.py --config configs/thesis_final.yaml
```

**Archivos:**

- `main.py`
- `configs/thesis_final.yaml`
- `src/etf_optimizer/thesis_final.py`
- `tests/test_thesis_final.py`
- `results/thesis_final/tables/final_strategy_comparison.csv`
- `results/thesis_final/tables/final_equity_curves.csv`
- `results/thesis_final/tables/final_drawdowns.csv`
- `results/thesis_final/diagnostics/data_flags.json`
- `results/thesis_final/diagnostics/fold_diagnostics.json`
- `results/thesis_final/manuscript_outputs/thesis_final_summary.md`
- `results/thesis_final/run_manifest.json`

**Qué se hizo:**

- Se creó un entrypoint único `python main.py --config configs/thesis_final.yaml` para generar `results/thesis_final/` con `tables/`, `figures/`, `diagnostics/`, `configs/`, `logs/` y `manuscript_outputs/`.
- Se congeló la configuración solicitada: 2015–2025, rebalanceo trimestral, lookback 36 meses, costos 10 bps, turnover incluido y universe `public_approximate_pit`.
- Se reportaron modelos finales: SPY, 60/40, Universe EqualWeight/MinVariance, ELECTRE EqualWeight/MinVariance/InverseVol y FlowSort EqualWeight/MinVariance/InverseVol.
- `ELECTRE_MaxSharpe_walk_forward` queda marcado como `experimental`, no como especificación principal.
- La corrida alcanzó `31` folds y `93` meses OOS, por encima del mínimo de 60 meses.

**Validación programática:**

```text
ruff check src/etf_optimizer/thesis_final.py main.py tests/test_thesis_final.py
All checks passed!

pytest tests/test_thesis_final.py -q
1 passed

python main.py --config configs/thesis_final.yaml
results/thesis_final/run_manifest.json
```

**Resultado principal:** Ningún modelo final MCDA supera el umbral objetivo de 10% CAGR; SPY queda arriba. Esto debe reportarse como evidencia metodológica/OOS defendible con performance insuficiente, no como estrategia ganadora.

**Caveat:** Aunque el OOS es suficiente por folds/meses, el universe `public_approximate_pit` sigue siendo datos públicos aproximados, no base institucional survivorship-bias-free.

---

## 2026-06-10 — GOAL 12 FlowSort como comparador de clasificación

**Tipo:** metodología / comparación MCDM sorting  
**Archivos:**

- `src/etf_optimizer/selection/flowsort.py`
- `src/etf_optimizer/reporting/flowsort_comparison.py`
- `scripts/build_flowsort_comparison.py`
- `tests/test_flowsort.py`
- `results/electre_vs_flowsort/flowsort_assignments.csv`
- `results/electre_vs_flowsort/flowsort_flows.csv`
- `results/electre_vs_flowsort/electre_vs_flowsort_agreement.csv`
- `docs/results/electre_vs_flowsort.md`

**Qué se hizo:**

- Se implementó FlowSort como comparador de **clasificación multicriterio**, no como rebalanceo.
- Se evaluaron las cuatro variantes mínimas: `usual_net_flow`, `v_shape_net_flow`, `level_net_flow` y `v_shape_leaving_flow`.
- Se exportaron asignaciones FlowSort por fold/ticker/variante, componentes de flujo (`leaving`, `entering`, `net`, `ranking_flow`) y comparación ELECTRE vs FlowSort.
- La comparación incluye agreement de categoría, Jaccard de clase superior, Cohen's kappa, forward returns por categoría y estabilidad temporal entre folds.

**Validación programática:**

```text
ruff check src/etf_optimizer/selection/flowsort.py src/etf_optimizer/reporting/flowsort_comparison.py tests/test_flowsort.py scripts/build_flowsort_comparison.py
All checks passed!

pytest tests/test_flowsort.py -q
2 passed

python scripts/build_flowsort_comparison.py
results/electre_vs_flowsort/flowsort_assignments.csv
results/electre_vs_flowsort/flowsort_flows.csv
results/electre_vs_flowsort/electre_vs_flowsort_agreement.csv
docs/results/electre_vs_flowsort.md
```

**Caveat:** FlowSort solo valida la etapa de sorting/clasificación MCDM. No debe presentarse como método de asignación de pesos ni política de rebalanceo.

---

## 2026-06-10 — GOAL 11 pesos defendibles BWM/AHP + sensibilidad

**Tipo:** metodología / elicitation de pesos MCDM  
**Archivos:**

- `src/etf_optimizer/weight_elicitation.py`
- `tests/test_weight_elicitation.py`
- `configs/weights/weights_manual.csv`
- `configs/weights/weights_equal.csv`
- `configs/weights/weights_bwm.csv`
- `configs/weights/weights_sensitivity_samples.csv`
- `configs/weights/weight_consistency_report.md`
- `docs/methodology/weight_elicitation.md`

**Qué se hizo:**

- Se alinearon los nombres metodológicos al GOAL 11: `manual_weights_baseline`, `equal_weights_baseline`, `BWM_weights_main` y `random_weight_sensitivity`.
- Se mantiene BWM como especificación principal provisional por ser más manejable que AHP en un set amplio de criterios; AHP queda documentado como alternativa si hay matriz humana consistente.
- Se preservan pesos manuales solo como baseline, no como metodología principal.
- Se regeneraron los CSV de pesos y sensibilidad con 500 muestras Dirichlet centradas en BWM.
- Se agregó `docs/methodology/weight_elicitation.md` como documento metodológico de tesis.

**Validación programática:**

```text
pytest tests/test_weight_elicitation.py -q
2 passed
```

**Caveat:** No se inventó juicio del director/profesor. La elicitation humana sigue pendiente salvo que el usuario proporcione comparaciones AHP/BWM observadas.

---

## 2026-06-09 — GOAL 6 universo observado vs universo invertible

**Tipo:** data engineering / elegibilidad invertible point-in-time  
**Archivos:**

- `src/etf_optimizer/data/investable_universe.py`
- `tests/test_investable_universe.py`
- `data/universe_master/investable_universe/universe_eligibility_by_date.csv`
- `data/universe_master/investable_universe/universe_exclusions_by_reason.csv`
- `data/universe_master/investable_universe/universe_exclusion_details.csv`
- `data/universe_master/investable_universe/observed_universe_snapshots/`
- `data/universe_master/investable_universe/investable_universe_snapshots/`
- `data/universe_master/investable_universe/README.md`

**Qué se hizo:**

- Se separaron formalmente dos capas: `observed_universe_as_of(t)` e `investable_universe_as_of(t)`.
- `observed_universe_as_of(t)` aplica solo visibilidad/listing PIT (`source_available_date`, observación, ticker activo, delisting/termination).
- `investable_universe_as_of(t)` aplica filtros duros de invertibilidad: ETF/ETMF, mutual funds, closed-end funds configurable, ETNs configurable, leveraged, inverse, precio mínimo, historial mínimo, liquidez por dollar volume, missing returns y exchange tradable configurable.
- Se genera por fecha: `observed_universe_count`, `investable_universe_count` y `excluded_by_reason`.
- Se escriben snapshots separados de universo observado e invertible para auditoría.

**Artefacto generado:**

```text
data/universe_master/investable_universe/universe_eligibility_by_date.csv
```

Run anual 2015-01-01 a 2025-01-01: 11 fechas. En la corrida pública actual, `investable_universe_count` crece de 0 en 2015/2016 a 42 en 2025-01-01. La cobertura local de precios es limitada y se refleja explícitamente en `missing_price` / `avg_dollar_volume_unavailable`.

**Validación programática:**

```text
pytest tests/test_investable_universe.py -q
3 passed
```

**Caveat:** la corrida generada usa `tradable_exchange_only=False` porque el snapshot público SEC Series/Class actual no trae exchange confiable para la mayoría de filas. El código soporta `tradable_exchange_only=True`; debe activarse en corridas thesis-grade cuando exista metadata de exchange PIT/institucional o validada.

---

## 2026-06-09 — GOAL 5 formalización de pesos BWM/baselines

**Tipo:** metodología / elicitation de pesos MCDM  
**Archivos:**

- `src/etf_optimizer/weight_elicitation.py`
- `tests/test_weight_elicitation.py`
- `configs/weights/weights_manual.csv`
- `configs/weights/weights_bwm.csv`
- `configs/weights/weights_equal.csv`
- `configs/weights/weights_sensitivity_samples.csv`
- `configs/weights/weight_consistency_report.md`

**Qué se hizo:**

- Se formalizó BWM como método principal provisional de pesos para los 11 criterios MCDM del GOAL 4.
- Los pesos manuales se preservan solo como `manual_weights_baseline`, no como especificación principal.
- Se generó `equal_weights_baseline` como control neutro.
- Se generaron 500 muestras `sensitivity_random_weights` con perturbación Dirichlet centrada en BWM para robustez.
- La mini-elicitation queda documentada así: experto 1 investigador/Hermes disponible; experto 2 director/profesor pendiente; experto 3 literatura/criterio institucional usado como racional documental, sin inventar juicio humano.
- El BWM researcher selecciona `rolling_max_drawdown` como mejor criterio y `fund_age_months` como peor criterio para evitar performance chasing y priorizar control de fragilidad OOS.

**Validación programática:**

```text
pytest tests/test_weight_elicitation.py -q
2 passed
```

**Artefactos generados:**

```text
configs/weights/weights_manual.csv
configs/weights/weights_bwm.csv
configs/weights/weights_equal.csv
configs/weights/weights_sensitivity_samples.csv
configs/weights/weight_consistency_report.md
```

**Caveat:** BWM queda como especificación primaria provisional. Antes de cierre final de tesis, registrar la elicitation real del director/profesor o declarar explícitamente su ausencia; no presentar el juicio `director/profesor` como observado si no existe.

---

## 2026-06-09 — GOAL 4 rediseño de criterios ETF

**Tipo:** metodología / configuración auditada de criterios  
**Archivos:**

- `configs/criteria_config.yaml`
- `src/etf_optimizer/criteria_config.py`
- `tests/test_criteria_config.py`
- `pyproject.toml`

**Qué se hizo:**

- Se creó `configs/criteria_config.yaml` con la separación explícita entre filtros duros pre-ELECTRE y criterios MCDM.
- Los filtros duros cubren: ETF apalancados, inversos, ETNs, historial mínimo, volumen promedio mínimo, AUM mínimo, expense ratio máximo, precio mínimo y cobertura de datos.
- Los criterios MCDM cubren: `momentum_12_1`, volatilidad anualizada, max drawdown rolling, Sortino rolling, avg dollar volume, expense ratio, tracking error contra benchmark de categoría, beta contra benchmark de categoría, correlación marginal, edad del fondo y AUM.
- Se eliminó CAGR histórico como criterio MCDM dominante en la nueva configuración; CAGR queda como métrica de validación posterior, no como eje de clasificación.
- Cada entrada declara: `criterion_name`, `formula`, `lookback_window`, `orientation`, `is_hard_filter`, `missing_data_rule`, `winsorization_rule`, `normalization_rule` y `source`.
- Se agregó un loader/validador mínimo para que la configuración sea verificable por tests y no solo documentación.

**Validación programática:**

```text
pytest tests/test_criteria_config.py -q
3 passed
```

**Caveat:** esta meta rediseña y valida la configuración de criterios. El pipeline legacy todavía contiene criterios antiguos en scripts/tests históricos; la conexión completa de `criteria_config.yaml` al cálculo de features y perfiles ELECTRE debe hacerse en el siguiente hito para no mezclar rediseño conceptual con tuning empírico.

---

## 2026-06-09 — GOAL 3 separación formal selección/asignación/rebalanceo

**Tipo:** metodología / trazabilidad por fold  
**Archivos:**

- `src/etf_optimizer/pipeline.py`
- `src/etf_optimizer/selection/flowsort.py`
- `scripts/run_sprint_experiment.py`
- `tests/test_flowsort.py`
- `tests/test_pipeline.py`
- `results/goal3_smoke_fold_artifacts/fold_stage_artifacts/`

**Qué se hizo:**

- Se separó formalmente el pipeline en universo/filtros → criterios → ELECTRE Tri → FlowSort → validación de clasificación → selección → asignación → rebalanceo/backtest.
- Se añadió FlowSort como clasificador MCDM comparador, explícitamente no como método de rebalanceo.
- Cada fold puede exportar artefactos intermedios obligatorios: `universe_snapshot.csv`, `criteria_matrix.csv`, `electre_assignments.csv`, `flowsort_assignments.csv`, `selected_etfs.csv`, `portfolio_weights.csv`, `fold_performance.csv`, `classification_diagnostics.csv`.
- `run_sprint_experiment.py` ahora escribe estos artefactos en `fold_stage_artifacts/` para la corrida principal.

**Validación programática:**

```text
pytest tests/test_flowsort.py tests/test_pipeline.py tests/test_pipeline_walkforward_selection.py tests/test_rebalance_policies.py -q
17 passed
ruff check ...
All checks passed
```

**Smoke run:**

```bash
python scripts/run_sprint_experiment.py --universe-mode static_current --universe data/universe/etf_universe_clean.csv --prices data/raw/yfinance_pilot_2015_2025/close.parquet --volume data/raw/yfinance_pilot_2015_2025/volume.parquet --start 2018-01-31 --end 2022-12-31 --rebalance annual --min-coverage-pct 0.3 --out results/goal3_smoke_fold_artifacts
```

Resultado: `fold_stage_artifacts/fold_001_2021_02_28/` contiene los 8 archivos requeridos. El smoke sigue siendo `public_data_pilot`, no evidencia final de tesis.

---

## 2026-06-09 — GOAL 7 integración Universe Master al backtester

**Tipo:** backtesting / integración PIT sin tuning  
**Experimento:** `backtest_public_approximate_pit_v1_2015_2025`

**Archivos principales:**

- `src/etf_optimizer/data/investable_universe.py`
- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `tests/test_investable_universe.py`
- `tests/test_run_sprint_experiment_preflight.py`
- `results/pit_integration_baseline/`
- `docs/results/pit_vs_current_universe_baseline.md`

**Qué se hizo:**

- Se agregó `--universe-mode public_approximate_pit` para consumir snapshots de `data/universe_master/investable_universe/investable_universe_snapshots/` en cada rebalance.
- Se añadieron filas comparables para `ELECTRE_EqualWeight_walk_forward`, `ELECTRE_MinVariance_walk_forward`, `ELECTRE_MaxSharpe_walk_forward`, `Universe_EqualWeight_walk_forward`, `SPY_buy_hold` y `60/40_SPY_BND_fixed_weight`.
- Se corrieron 31 folds / 93 periodos OOS para `old_current_universe` y `new_public_approximate_pit_universe` con criterios, pesos, λ y parámetros base sin optimización de performance.
- Se generaron `combined_strategy_comparison.csv`, `pit_vs_current_metric_deltas.csv` y `run_diagnostics.csv`.

**Resultado headline:** PIT aproximado mejora ELECTRE MaxSharpe de CAGR -1.08% a 0.15% y MDD -43.55% a -24.97%, pero sigue muy por debajo de SPY 13.85%; el cambio de universo no resuelve el blocker de performance.

**Validación:**

```bash
pytest tests/test_investable_universe.py tests/test_pipeline.py tests/test_pipeline_walkforward_selection.py tests/test_run_sprint_experiment_preflight.py -q
ruff check src/etf_optimizer/data/investable_universe.py src/etf_optimizer/pipeline.py scripts/run_sprint_experiment.py tests/test_investable_universe.py tests/test_run_sprint_experiment_preflight.py
```

---

## 2026-06-09 — GOAL 2 ETF Universe Master público PIT

**Tipo:** data engineering / universo point-in-time ETF  
**Archivos principales:**

- `src/etf_optimizer/data/universe_master.py`
- `scripts/build_etf_universe_master.py`
- `tests/test_universe_master.py`
- `data/universe_master/fund_master.csv`
- `data/universe_master/ticker_history.csv`
- `data/universe_master/sec_series_class_map.csv`
- `data/universe_master/listings_by_date.csv`
- `data/universe_master/price_ohlcv.parquet`
- `data/universe_master/distributions_or_total_returns.csv`
- `data/universe_master/fund_metadata.csv`
- `data/universe_master/source_audit_log.csv`
- `data/universe_master/rebalance_universe_snapshots/`

**Qué se hizo:**

- Se creó un ETF Universe Master basado en SEC Series/Class anual y precios públicos locales.
- Se implementó la regla PIT obligatoria: `source_available_date <= rebalance_date`.
- Se generaron snapshots mensuales `rebalance_universe_2015_01.csv` a `rebalance_universe_2025_12.csv` con `data_quality_flag`.
- Se registró `public_approximate_pit_sec_series_class_annual_snapshot`; años SEC no disponibles públicamente en la URL anual se marcaron como `stale_forward_filled_from_prior_sec_snapshot_due_missing_annual_file`.

**Validación programática:**

```text
14 tests passed para universe master / SEC universe.
132 snapshots generados.
fund_master: 4,506 filas.
listings_by_date: 33,329 filas.
Regla PIT verificada en rebalance_universe_2015_01, 2015_04 y 2025_12.
```

**Comando reproducible:**

```bash
python scripts/build_etf_universe_master.py --out data/universe_master --start-year 2015 --end-year 2025 --price-dir data/raw/yfinance_pilot_2015_2025
pytest tests/test_universe_master.py tests/test_point_in_time_universe.py tests/test_sec_universe.py -q
```

**Claim boundary:** Esta ruta es `public_approximate_pit`, no CRSP-grade. No usar para claims finales survivorship-bias-free perfectos; sirve para cerrar la arquitectura SEC-only y medir cobertura/limitaciones antes de tuning.

---

## 2026-06-07 — Conversión de tesis compacta a documento formal largo

**Tipo:** entregable académico / documentación reproducible  
**Archivos:**

- `docs/deliverables/tesis_trabajo_grado_etf_electre.docx`
- `docs/deliverables/tesis_trabajo_grado_etf_electre.pdf`
- `scripts/build_long_thesis_docx.py`
- `docs/deliverables/deliverables_manifest.json`
- `docs/deliverables/README.md`

**Qué se hizo:**

- Se reemplazó el DOCX compacto por una tesis formal ampliada en español.
- El documento ahora incluye portada, resumen, abstract, tabla de contenido manual, planteamiento del problema, objetivos, marco teórico, datos/sesgos, metodología, implementación, diseño experimental, resultados, discusión, protocolo de reproducibilidad, conclusiones, referencias y anexos.
- Se mantuvo un límite de claim conservador: evidencia pública piloto, metodología reproducible, no recomendación de inversión ni prueba final survivor-bias-free.
- Se añadió un script reproducible para reconstruir el DOCX largo desde métricas y artefactos del repositorio.

**Validación programática:**

```text
DOCX: 20,729 palabras incluyendo tablas
PDF: 69 páginas exactas, renderizado con LibreOffice 24.2.7.2 / writer_pdf_Export
Estimación: 69.1 páginas a 300 palabras/página; 75.4 páginas a 275 palabras/página
875 párrafos no vacíos
178 encabezados
6 tablas de contenido académico y 7 rótulos `Tabla N`
26 fórmulas con rótulo `Ecuación N`
```

**Verificación:**

```bash
uv run python scripts/build_long_thesis_docx.py
uv run pytest tests/test_presentation_deliverables.py -q
uv run ruff check scripts/build_long_thesis_docx.py
```

**Nota operativa:** LibreOffice quedó disponible en el entorno y se generó el PDF final con `libreoffice --headless --convert-to pdf`. La paginación exacta reportada por `pdfinfo` es de 69 páginas tamaño carta.

Resultado observado: `5 passed`; ruff sin errores.

---

## 2026-06-02 — Ranking consolidado por CAGR de experimentos ETF 2021–2025

**Tipo:** consolidación de resultados / ranking empírico piloto  
**Archivo:** `docs/traceability/experiment_cagr_ranking_2021_2025.md`

**Qué se hizo:**

- Se consolidaron los hallazgos de la ventana principal `2021–2025` en formato ranking por CAGR.
- Se identificó como mejor candidato metodológico actual `ELECTRE_MaxSharpe_walk_forward` con `category_exposure_cap=0.25`: CAGR `18.08%`, Sharpe `2.59`, max drawdown `-2.40%`.
- Se registró el rango amplio `2020–2035` como alcance adicional, aclarando que los precios locales solo llegan hasta 2025 y que el resultado efectivo 2020–2025 de ELECTRE fue CAGR `4.70%`.
- Se conservó el experimento `point_in_time` 2018–2022 como avance metodológico y limitación empírica, no como caso ganador.

**Claim boundary:**

Resultado prometedor y superior al umbral interno `>10%` en 2021–2025, pero todavía `pilot_only_oos`, con universo estático y baja cobertura elegible. No debe presentarse como evidencia final survivorship-bias-free.

**Verificación:**

```bash
sed -n '1,220p' docs/traceability/experiment_cagr_ranking_2021_2025.md
```

---

## 2026-06-02 — Experimento piloto con universo ETF point-in-time SEC 2018–2022

**Tipo:** experimento empírico piloto / validación de integración  
**Resultado:** `results/point_in_time_quarterly_2018_2022_cov100/`

**Comando principal:**

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe-mode point_in_time \
  --sec-series-class-years 2018 2019 2020 2021 2022 \
  --download-sec-snapshots \
  --prices data/raw/yfinance_pilot_2015_2025/close.parquet \
  --volume data/raw/yfinance_pilot_2015_2025/volume.parquet \
  --start 2018-01-01 \
  --end 2022-12-31 \
  --rebalance quarterly \
  --weight-drift buy_and_hold \
  --rebalance-policy calendar \
  --electre-assignment pessimistic \
  --disable-veto \
  --cost-bps 10 \
  --out results/point_in_time_quarterly_2018_2022_cov100 \
  --min-coverage-pct 1.0 \
  --min-avg-dollar-volume 0
```

**Métricas principales:**

- Universo SEC master: 4,195 fondos/clases candidatos; 82 tickers con precio local disponible.
- OOS: 7 folds, 21 meses; `pilot_only_oos`, no thesis-grade.
- ELECTRE_MaxSharpe_walk_forward: CAGR `-10.20%`, Sharpe `-0.74`, max drawdown `-18.99%`.
- SPY_buy_hold: CAGR `3.93%`, Sharpe `0.29`, max drawdown `-23.93%`.
- 60/40: CAGR `-1.58%`, Sharpe `-0.06`, max drawdown `-20.26%`.

**Interpretación:**

- El nuevo modo point-in-time corre y genera artefactos, pero este piloto fue empíricamente débil para ELECTRE.
- La ventana OOS 2021–2022 contiene un cambio de régimen fuerte; los principales detractores incluyeron clean energy, China/ChiNext y online retail.
- El resultado no cumple el objetivo de `>10%` anualizado y debe tratarse como evidencia piloto negativa útil, no como claim final.

**Correcciones hechas durante el experimento:**

- Se amplió el parser SEC Series/Class para aceptar encabezados nuevos tipo `CIK Number`, `Series ID`, `Class Ticker` usados en 2019–2022.
- Se endurecieron benchmarks walk-forward para evitar fallos numéricos de MaxSharpe usando fallback a min-variance.
- Se filtraron benchmarks estáticos a columnas sin retornos faltantes, separando el universo benchmark de la membresía dinámica ELECTRE.

**Verificación:**

```bash
uv run pytest -q
uv run ruff check .
```

Resultado observado: `149 passed`; ruff sin errores.

---

## 2026-06-02 — Integración del universo point-in-time al flujo de experimentos

**Tipo:** implementación TDD / integración metodológica  
**Archivos:**

- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `tests/test_pipeline.py`

**Qué se hizo:**

- Se conectó `PointInTimeETFUniverseProvider` al pipeline walk-forward para que cada rebalanceo filtre los activos elegibles con `constituents_as_of(rebalance_date)` antes de calcular features, clasificar con ELECTRE y optimizar pesos.
- Se añadió soporte CLI para `--universe-mode point_in_time`, `--sec-series-class-years`, `--sec-series-class-dir`, `--download-sec-snapshots` y `--universe-min-age-months`.
- En modo `point_in_time`, el experimento exporta `point_in_time_universe_master.csv` y deja trazabilidad en `run_manifest.json`.
- Se evitó aplicar un filtro global de cobertura desde `start` para el modo point-in-time, porque eso excluiría ETFs nuevos legítimos; la cobertura/liquidez se aplica por rebalanceo usando solo datos disponibles hasta esa fecha.
- Se añadió test de pipeline que verifica que un ETF nuevo no aparece en el primer rebalanceo y que un ETF desaparecido sale en rebalanceos posteriores.

**Verificación:**

```bash
uv run pytest tests/test_run_sprint_experiment_preflight.py tests/test_pipeline.py tests/test_point_in_time_universe.py -q
uv run pytest -q
uv run ruff check .
uv run python scripts/run_sprint_experiment.py \
  --universe-mode point_in_time \
  --sec-series-class-years 2020 2021 2022 2023 2024 \
  --sec-series-class-dir /tmp/sec_series_class_smoke \
  --start 2020-01-01 \
  --end 2024-12-31 \
  --rebalance annual \
  --out /tmp/etf_pit_smoke \
  --min-coverage-pct 0.8 \
  --min-avg-dollar-volume 0
```

Resultado observado: `148 passed`; ruff sin errores; smoke test point-in-time generó artefactos en `/tmp/etf_pit_smoke`.

---

## 2026-06-02 — Implementación inicial de universo ETF point-in-time público

**Tipo:** implementación TDD / metodología de datos  
**Archivos:**

- `src/etf_optimizer/data/sec_universe.py`
- `tests/test_point_in_time_universe.py`

**Qué se hizo:**

- Se implementó `load_sec_series_class_snapshot(...)` para cargar snapshots anuales SEC Investment Company Series/Class y filtrar candidatos ETF con heurística textual conservadora.
- Se implementó `build_point_in_time_master(...)` para unir snapshots anuales preservando `first_seen_date`, `last_seen_date`, `source_year`, `series_id`, `class_id` y `cik`.
- Se implementó `PointInTimeETFUniverseProvider.constituents_as_of(...)` para devolver el universo observable en una fecha histórica, incorporando ETFs nuevos solo después de ser observables y excluyendo fondos que desaparecen.
- Se añadieron filtros opcionales por antigüedad mínima, cobertura de precios y volumen dólar promedio, para evitar look-ahead y ETFs sin historial/liquidez suficiente.

**Verificación:**

```bash
uv run pytest tests/test_point_in_time_universe.py -q
uv run pytest -q
uv run ruff check .
```

Resultado observado: `147 passed`; ruff sin errores.

---

## 2026-05-26 — Revisión de literatura sobre sesgo de universo ETF point-in-time

**Tipo:** investigación académica / metodología de datos  
**Archivo:** `docs/research/point_in_time_universe_bias_literature_review_es.md`

**Qué se hizo:**

- Se revisó el problema de usar universos ETF estáticos: `static_current` introduce survivorship/look-ahead bias y `static_start` introduce incumbent-only bias.
- Se sintetizaron trabajos fundacionales sobre survivorship bias: Brown et al. (1992), Elton et al. (1996), Carhart et al. (2002), literatura CRSP/Morningstar y backtest overfitting.
- Se documentó el estado del arte: bases survivor-bias-free institucionales y ruta pública defendible con SEC Series/Class anual + N-PORT desde 2019Q4.
- Se propuso formalmente `PointInTimeETFUniverseProvider` y los modos `static_current`, `static_start`, `point_in_time`.

**Verificación:**

```bash
sed -n '1,220p' docs/research/point_in_time_universe_bias_literature_review_es.md
```

---

## 2026-05-20 — Investigación de fuentes ETF point-in-time

**Tipo:** investigación de datos / metodología  
**Archivo:** `docs/research/etf_point_in_time_data_sources.md`

**Qué se hizo:**

- Se confirmó que el universo actual viene de un snapshot activo/current de Nasdaq, no de una base point-in-time.
- Se incorporó el siguiente criterio metodológico: el siguiente paso ideal es usar una base institucional point-in-time como CRSP, Morningstar Direct, Lipper, Bloomberg o Refinitiv/LSEG, o construir snapshots históricos por año si se encuentra una fuente pública archivada suficientemente estable.
- Se documentó una matriz de fuentes institucionales y abiertas, con acceso, capacidad point-in-time, uso recomendado y limitaciones.
- Se propuso agregar proveedores de universo `current_snapshot`, `archived_snapshot` e `institutional_point_in_time`.
- Revisión final adicional: `docs/research/etf_historical_universe_last_review.md` identificó SEC Investment Company Series/Class annual CSVs como la mejor ruta abierta para reconstruir un universo 2018 aproximado; el archivo 2018 observado contiene 45,349 filas, 45,347 tickers de clase no nulos y ~2,269 tickers ETF candidatos bajo heurística textual.

**Verificación:**

```bash
sed -n '1,160p' docs/research/etf_point_in_time_data_sources.md
```

---

## 2026-05-19 — Plan de mejora ELECTRE/rebalanceo

**Tipo:** documentación / roadmap  
**Archivo:** `docs/plans/2026-05-19-roadmap-mejora-validacion-electre-rebalanceo.md`

**Qué se hizo:**

- Se creó un roadmap por fases para robustecer el proyecto.
- Incluye promoción de experimento paper-style trimestral, rebalanceo por tolerancia, recategorización, optimizador con fallback, criterios ETF-specific, validación thesis-grade y dashboard de trazabilidad.

**Verificación:**

```bash
sed -n '1,80p' docs/plans/2026-05-19-roadmap-mejora-validacion-electre-rebalanceo.md
```

---

## 2026-05-19 — Investigación extensa de papers ELECTRE Tri / rebalanceo

**Tipo:** investigación académica  
**Archivo:** `docs/research/electre_tri_rebalanceo_50_papers_2016_2026.md`

**Qué se hizo:**

- Se investigaron papers 2016-2026 sobre ELECTRE Tri, MCDA, ETF portfolio optimization y rebalanceo.
- Se creó un ranking cualitativo de 50 trabajos desde mayor señal de rentabilidad esperada/evidenciada hasta menor comparabilidad.
- Se documentaron hallazgos sobre:
  - ELECTRE Tri pesimista/optimista;
  - veto vs sin veto;
  - BWM/pesos;
  - buy-and-hold vs constant-mix;
  - calendario vs tolerancia;
  - costes de transacción;
  - tracking error y liquidez ETF.

**Fuentes consultadas:**

- OpenAlex API.
- Semantic Scholar API.
- arXiv/Crossref metadata.
- Páginas editoriales públicas accesibles.

**Advertencia metodológica:**

El ranking no es aún un meta-análisis numérico. Muchos papers no reportan CAGR comparable en metadata/abstract. El siguiente paso responsable es extraer tablas completas de PDFs prioritarios.

**Verificación:**

```bash
sed -n '1,120p' docs/research/electre_tri_rebalanceo_50_papers_2016_2026.md
```

---

## 2026-05-20 — Atribución de holdings por fold + metadatos externos

**Tipo:** implementación TDD + diagnóstico con información externa  
**Archivos principales:**

- `src/etf_optimizer/reporting/holdings_attribution.py`
- `tests/test_holdings_attribution.py`
- `scripts/run_sprint_experiment.py`
- `results/sprint_universe_paper_quarterly_2015_2025_oos/fold_holdings_attribution.csv`
- `docs/traceability/external_etf_metadata_top_detractors.csv`
- `docs/traceability/top_detractors_external_interpretation.csv`

**Qué se hizo:**

- Se añadió `fold_holdings_attribution_table` para aproximar contribución por ETF dentro de cada fold OOS:

```text
total_contribution ≈ Σ effective_weight[ticker, t] × return[ticker, t]
```

- El artefacto se integra en cada corrida robusta y en provenance.
- Se usó información externa de Yahoo Finance vía `yfinance` para los principales detractores: categoría, familia, beta 3Y, activos y resumen del fondo.
- Se regeneró la corrida extendida 2015-2025.

**Top detractores acumulados 2015-2025:**

```text
CORN  Teucrium Corn Fund                         -15.34 pp
CGW   Invesco S&P Global Water Index ETF         -10.63 pp
CNXT  VanEck ChiNext Innovators ETF               -9.16 pp
CANE  Teucrium Sugar Fund                         -4.72 pp
CARZ  Future Vehicles & Technology ETF            -2.41 pp
COPX  Global X Copper Miners ETF                  -0.69 pp
```

**Interpretación externa:**

Los detractores se concentran en exposiciones temáticas/sectoriales y commodities:

- `Commodities Focused`: CORN, CANE;
- `Natural Resources`: CGW, COPX;
- `Greater China Region`: CNXT;
- `Technology`: CARZ.

**Lectura:**

La falla OOS larga no parece venir solo del optimizador MaxSharpe, sino de la selección de ETFs con exposiciones concentradas a commodities/recursos/China/temáticos que entraron con pesos relevantes y sufrieron en varios folds. El siguiente hito debe añadir controles explícitos de concentración por categoría externa y penalización de drawdown/riesgo de cola.

---

## 2026-05-20 — Diagnóstico fold-level OOS

**Tipo:** implementación TDD + diagnóstico de falla por régimen  
**Archivos principales:**

- `src/etf_optimizer/reporting/fold_performance.py`
- `tests/test_fold_performance.py`
- `scripts/run_sprint_experiment.py`
- `results/sprint_universe_paper_quarterly_2015_2025_oos/fold_performance.csv`

**Qué se hizo:**

- Se añadió `fold_performance_table` para partir los retornos OOS en folds de tamaño `test_size`.
- Cada fold reporta fechas, observaciones, retorno acumulado, CAGR, volatilidad, Sharpe, Sortino, max drawdown, Calmar y marca el peor fold por estrategia.
- Se integró `fold_performance.csv` como artefacto regular de cada corrida robusta y en provenance.
- Se regeneró la corrida extendida 2015-2025 con el nuevo artefacto.

**Diagnóstico de la corrida 2015-2025:**

- ELECTRE tiene 31 folds OOS:
  - 17 folds positivos;
  - 14 folds negativos.
- Peor fold ELECTRE:

```text
fold 9: 2020-02-29 a 2020-04-30
cumulative_return = -14.53%
max_drawdown      = -14.61%
Sharpe            = -1.34
```

- Otros folds débiles:
  - 2022-02 a 2022-04: -10.63%;
  - 2022-05 a 2022-07: -9.16%;
  - 2023-02 a 2023-04: -8.80%.
- Promedio de retorno por fold:
  - pre-2020: +0.64%;
  - 2020+: -0.44%.

**Lectura:**

La caída no viene de un único error aislado; hay un deterioro persistente en varios regímenes post-2020, especialmente crisis COVID/2022/2023. El siguiente hito debe mirar composición y criterios por fold para detectar qué ETFs/criterios cargan la pérdida.

---

## 2026-05-20 — Ampliación OOS 2015-2025

**Tipo:** validación empírica extendida / claim boundary  
**Archivos principales:**

- `data/raw/yfinance_pilot_2015_2025/`
- `results/sprint_universe_paper_quarterly_2015_2025_oos/`
- `docs/traceability/milestone_metrics_history.csv`
- `docs/traceability/milestone_metrics_history.md`

**Qué se hizo:**

- Se descargó un panel piloto extendido de 300 tickers para 2015-01-01 a 2025-12-31.
- Se ejecutó la configuración candidata principal en ventana larga:
  - `rebalance=quarterly`
  - `weight_drift=buy_and_hold`
  - `electre_assignment=pessimistic`
  - `electre_use_veto=False`
  - `cost_bps=10`
- La corrida efectiva usó `start=2015-01-05` para no excluir ETFs con primera fecha válida en el primer día bursátil de 2015.
- Se generaron artefactos completos, incluyendo `paired_benchmark_tests.csv`.

**Resultado OOS:**

```text
walk_forward_folds = 31
oos_periods = 93
sufficiency_label = thesis_grade_oos
```

**Resultado de performance:**

```text
ELECTRE CAGR        = -1.08%
ELECTRE Sharpe      = 0.011
ELECTRE Max DD      = -43.55%
SPY CAGR            = 13.85%
60/40 CAGR          = 9.16%
```

**Pruebas pareadas:**

- ELECTRE queda estadísticamente peor que SPY en CAGR, Sharpe, Sortino y Calmar.
- ELECTRE queda estadísticamente peor que 60/40 en CAGR, volatilidad, Sharpe, Sortino, max drawdown y Calmar.
- Frente a EqualWeight/MinVariance/MaxSharpe hay varias diferencias no concluyentes, pero la volatilidad/drawdown de ELECTRE empeora frente a algunas alternativas.

**Lectura responsable:**

Este es un resultado duro pero valioso: la ventana corta 2020-2024 era favorable, pero al ampliar OOS el modelo no generaliza. Esto es metodológicamente bueno porque evita overfitting y obliga a rediseñar criterios ETF-specific, filtros de régimen o políticas de rebalanceo antes de afirmar performance final.

---

## 2026-05-20 — Pruebas pareadas contra benchmarks

**Tipo:** implementación TDD + validación estadística piloto  
**Archivos principales:**

- `src/etf_optimizer/reporting/statistical_tests.py`
- `tests/test_statistical_tests.py`
- `scripts/run_sprint_experiment.py`
- `README.md`
- `docs/methodology.md`
- `docs/thesis_methodology_es.md`
- `results/sprint_universe_paper_quarterly_paired/paired_benchmark_tests.csv`

**Qué se hizo:**

- Se agregó `paired_benchmark_tests_table`, que alinea fechas entre la estrategia ELECTRE y cada benchmark.
- Usa bootstrap pareado de retornos mensuales para preservar la estructura estrategia-vs-benchmark en cada fecha.
- Reporta diferencias de métricas, intervalo de confianza y conclusión direccional:
  - `strategy_positive`
  - `strategy_negative`
  - `not_conclusive`
- Se integró el artefacto `paired_benchmark_tests.csv` en `scripts/run_sprint_experiment.py`, logs y provenance.
- Se regeneró una corrida candidata sin sobrescribir el directorio principal:

```text
results/sprint_universe_paper_quarterly_paired/
```

**Resultado piloto:**

- Para CAGR, ELECTRE queda:
  - por debajo de SPY: diferencia -11.28 pp, `not_conclusive`;
  - por debajo de 60/40: diferencia -1.51 pp, `not_conclusive`;
  - por encima de EqualWeight: diferencia +6.96 pp, `not_conclusive`;
  - por encima de MinVariance: diferencia +6.66 pp, `not_conclusive`;
  - por encima de MaxSharpe: diferencia +3.62 pp, `not_conclusive`.
- La única conclusión direccional fuerte en esta corrida fue contra MinVariance en volatilidad: `strategy_negative`, porque ELECTRE tuvo más volatilidad.

**Lectura responsable:**

Con solo 12 observaciones OOS, las diferencias de CAGR/Sharpe frente a benchmarks son estadísticamente no concluyentes. El artefacto sirve para impedir sobreafirmar resultados hasta ampliar historia/folds.

**Verificación:**

```bash
uv run pytest tests/test_statistical_tests.py -q
uv run pytest -q
uv run ruff check .
```

---

## 2026-05-20 — Consolidación metodológica de tesis en español

**Tipo:** documentación académica / claim boundaries  
**Archivos principales:**

- `README.md`
- `docs/thesis_methodology_es.md`

**Qué se hizo:**

- Se actualizó el estado verificado de tests en `README.md` de 106 a 128 tests.
- Se añadió una advertencia explícita de que las corridas públicas actuales son evidencia piloto, no evidencia thesis-grade ni survivorship-bias-free.
- Se creó un capítulo metodológico consolidado en español con:
  - planteamiento del problema y justificación del mercado ETF;
  - objetivo general e hipótesis;
  - arquitectura ELECTRE Tri → optimización → rebalanceo → validación;
  - límites de datos públicos y survivorship bias;
  - configuración candidata principal y resultados piloto;
  - tabla de contribuciones, artefactos y limitaciones;
  - prioridades para defensa final.

**Resultado documental:**

```text
docs/thesis_methodology_es.md
```

El capítulo fija el lenguaje responsable:

```text
metodológicamente válido y empíricamente prometedor en evidencia piloto,
pero aún no concluyente ni survivorship-bias-free.
```

**Verificación:**

```bash
uv run pytest -q
```

---

## 2026-05-19 — Filtro de materialidad mínima para cambios de categoría

**Tipo:** implementación TDD + experimento continuo  
**Archivos principales:**

- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `scripts/compile_milestone_metrics.py`
- `tests/test_pipeline_walkforward_selection.py`
- `tests/test_run_sprint_experiment_preflight.py`
- `docs/traceability/materiality_confirmation_sweep.csv`
- `docs/traceability/milestone_metrics_history.csv`
- `docs/traceability/milestone_metrics_history.md`
- `results/sweep_materiality_confirm2_*/`

**Qué se hizo:**

- Se añadió `category_change_min_score_improvement` a `PipelineConfig`.
- Se añadió CLI:
  - `--category-change-min-score-improvement FLOAT`
- En `recategorization_policy=every_period`, un `category_change` confirmado debe superar una mejora mínima de credibilidad ELECTRE frente al conjunto actual.
- Se agregó test TDD:
  - `test_category_change_min_score_improvement_blocks_immaterial_recategorization`
- Se ejecutó barrido con:
  - `category_confirmation_periods=2`
  - `turnover_penalty=0.0`
  - `category_change_min_score_improvement ∈ {0.00, 0.05, 0.10, 0.20, 0.30, 0.50, 0.75, 1.00, 1.10}`

**Resultado:**

```text
0.00–0.30: CAGR 10.79%, Sharpe 1.162, Max DD -4.94%, turnover 1.50
0.50:      CAGR 8.42%,  Sharpe 0.913, Max DD -4.94%, turnover 1.50
0.75+:     CAGR 4.49%,  Sharpe 0.505, Max DD -5.09%, turnover 0.50
```

**Lectura responsable:**

El filtro de materialidad por credibilidad ELECTRE no mejora el máximo: hasta 0.30 no cambia la decisión y desde 0.50 bloquea/desplaza cambios útiles. Queda como control de seguridad parametrizable, pero el siguiente filtro debería basarse en utilidad económica neta de costes o mejora esperada de Sharpe, no solo en credibilidad ELECTRE.

---

## 2026-05-19 — Barrido turnover penalty × confirmación de categoría

**Tipo:** experimento continuo + trazabilidad cuantitativa  
**Archivos principales:**

- `docs/traceability/turnover_confirmation_sweep.csv`
- `docs/traceability/milestone_metrics_history.csv`
- `docs/traceability/milestone_metrics_history.md`
- `results/sweep_turnover_confirm_*/`
- `results/sweep_turnover_confirm_refined_*/`

**Qué se hizo:**

- Se ejecutó un barrido inicial:
  - `turnover_penalty ∈ {0.25, 0.50, 0.75, 0.90}`
  - `category_confirmation_periods ∈ {1, 2, 3}`
- Como el mejor punto fue `turnover_penalty=0.25`, `category_confirmation_periods=2`, se refinó alrededor de penalidades bajas:
  - `turnover_penalty ∈ {0.00, 0.10, 0.15, 0.20, 0.30, 0.35}`
  - `category_confirmation_periods=2`
- Se guardó la tabla completa del barrido en `docs/traceability/turnover_confirmation_sweep.csv`.
- Se añadió al historial de hitos el mejor resultado refinado: `sweep_best_penalty000_confirm2`.

**Mejor resultado del barrido every-period:**

```text
turnover_penalty=0.00
category_confirmation_periods=2
CAGR=10.79%
Sharpe=1.162
Max DD=-4.94%
Turnover=1.500
Category-change events=1
```

**Lectura responsable:**

La confirmación de categoría aporta más valor que la penalización alta de turnover en esta muestra. El modo every-period vuelve a superar 10% CAGR cuando se exige persistencia de señal durante 2 períodos y no se suaviza artificialmente el trade. Aun así, sigue por debajo del candidato principal `paper_style_rebalance_only` con 13.61% CAGR y Sharpe 1.50.

---

## 2026-05-19 — Confirmación de categoría para reducir whipsaw

**Tipo:** implementación + experimento continuo  
**Archivos principales:**

- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `scripts/compile_milestone_metrics.py`
- `tests/test_pipeline_walkforward_selection.py`
- `tests/test_milestone_metrics.py`
- `docs/traceability/milestone_metrics_history.csv`
- `docs/traceability/milestone_metrics_history.md`
- `results/sprint_universe_paper_quarterly_recategorized_confirm2/`

**Qué se hizo:**

- Se añadió `category_confirmation_periods` a `PipelineConfig` y CLI.
- En `recategorization_policy=every_period`, un nuevo conjunto seleccionado debe persistir N períodos antes de operar `category_change`.
- Se probó `category_confirmation_periods=2` combinado con `turnover_penalty=0.75`.

**Tests añadidos:**

- `test_category_confirmation_periods_waits_for_persistent_selection_before_trading`
- Se extendió el historial de hitos para registrar `category_confirmation_periods`.

**Verificación:**

```bash
uv run pytest -q
uv run ruff check .
```

**Resultado observado:**

```text
127 passed
All checks passed
```

**Impacto frente al hito anterior (`every_period_turnover_penalty_075`):**

```text
CAGR: 5.59% → 6.04%  (+0.45 pp)
Sharpe: 0.646 → 0.683  (+0.037)
Max DD: -5.66% → -4.94%  (+0.72 pp)
Turnover total: 1.676 → 0.750  (-0.926)
Category-change events: 9 → 1
```

**Lectura responsable:**

La confirmación de categoría reduce whipsaw de forma clara y mejora el modo experimental `every_period`; sin embargo, todavía no supera el candidato principal `paper_style_rebalance_only` (13.61% CAGR). Próximo paso recomendado: barrido pequeño de hiperparámetros `turnover_penalty × category_confirmation_periods`.

---

## 2026-05-19 — Penalización de turnover e historial de métricas por hito

**Tipo:** implementación + trazabilidad cuantitativa  
**Archivos principales:**

- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `scripts/compile_milestone_metrics.py`
- `tests/test_pipeline_walkforward_selection.py`
- `tests/test_milestone_metrics.py`
- `docs/traceability/milestone_metrics_history.csv`
- `docs/traceability/milestone_metrics_history.md`
- `results/sprint_universe_paper_quarterly_recategorized_turnover_penalty/`

**Qué se hizo:**

- Se añadió `turnover_penalty` a `PipelineConfig` y CLI.
- En `recategorization_policy=every_period`, los nuevos pesos objetivo pueden mezclarse con los pesos actuales:
  - `0.0` = sin penalización, trade completo al nuevo target.
  - `0.75` = solo se mueve 25% hacia el nuevo target, reduciendo rotación.
- Se añadió script auditable:
  - `scripts/compile_milestone_metrics.py`
- Se generó historial de hitos:
  - `docs/traceability/milestone_metrics_history.csv`
  - `docs/traceability/milestone_metrics_history.md`

**Tests añadidos:**

- `test_turnover_penalty_reduces_category_change_turnover`
- `test_collect_milestone_metrics_records_deltas_and_event_counts`

**Verificación:**

```bash
uv run pytest -q
uv run ruff check .
```

**Resultado observado:**

```text
126 passed
All checks passed
```

**Impacto de métricas por hito:**

| Hito | CAGR | Δ CAGR | Sharpe | Δ Sharpe | Max DD | Δ Max DD | Turnover total | Δ Turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| paper_style_rebalance_only | 13.61% | — | 1.499 | — | -4.23% | — | 2.191 | — |
| every_period_category_change | 5.02% | -8.59 pp | 0.537 | -0.961 | -8.32% | -4.10 pp | 4.620 | +2.429 |
| every_period_turnover_penalty_075 | 5.59% | +0.57 pp | 0.646 | +0.109 | -5.66% | +2.66 pp | 1.676 | -2.943 |

**Lectura responsable:**

La penalización de turnover mejora claramente el modo `every_period` frente a recategorización sin penalización: sube CAGR/Sharpe, reduce drawdown y baja turnover. Sin embargo, sigue por debajo del modo principal `rebalance_only`; por tanto queda como modo de investigación. El próximo hito recomendado es exigir persistencia de cambio de categoría antes de operar (`category_confirmation_periods`).

---

## 2026-05-19 — Recategorización mensual y rebalanceo por cambio de categoría

**Tipo:** implementación + experimento comparativo  
**Archivos principales:**

- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `tests/test_pipeline_walkforward_selection.py`
- `tests/test_run_sprint_experiment_preflight.py`
- `results/sprint_universe_paper_quarterly_recategorized/`

**Qué se hizo:**

- Se añadió `recategorization_policy="rebalance_only" | "every_period"` a `PipelineConfig`.
- Se expuso en CLI:
  - `--recategorization-policy rebalance_only|every_period`
- `rebalance_only` mantiene el comportamiento anterior: ELECTRE se recalcula en las fechas de rebalanceo/fold.
- `every_period` recalcula ELECTRE en cada período OOS usando solo la ventana histórica disponible y opera solo si:
  - es el primer evento calendario;
  - cambia el conjunto de activos seleccionados/categoría (`category_change`);
  - o se activa threshold por drift cuando `--rebalance-policy threshold`.
- `rebalance_events.csv` ahora puede registrar `category_change`.

**Test RED/GREEN añadido:**

- `test_every_period_recategorization_records_category_change_rebalance`

**Verificación:**

```bash
uv run pytest tests/test_pipeline_walkforward_selection.py tests/test_pipeline.py tests/test_run_sprint_experiment_preflight.py -q
uv run pytest -q
uv run ruff check .
```

**Resultado observado:**

```text
124 passed
All checks passed
```

**Experimento generado:**

`results/sprint_universe_paper_quarterly_recategorized/`

Comando base:

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe data/universe/etf_universe_clean.csv \
  --prices data/raw/yfinance_pilot/close.parquet \
  --volume data/raw/yfinance_pilot/volume.parquet \
  --start 2020-12-31 \
  --end 2024-12-31 \
  --rebalance quarterly \
  --weight-drift buy_and_hold \
  --rebalance-policy threshold \
  --drift-tolerance 0.05 \
  --recategorization-policy every_period \
  --electre-assignment pessimistic \
  --disable-veto \
  --compare-electre-variants \
  --cost-bps 10 \
  --out results/sprint_universe_paper_quarterly_recategorized \
  --min-coverage-pct 0.8 \
  --min-avg-dollar-volume 0
```

**Resultado observado del experimento recategorizado:**

```text
ELECTRE_MaxSharpe_walk_forward CAGR = 5.0152%
Sharpe = 0.5373
Max drawdown = -8.3241%
```

Eventos registrados:

```text
category_change = 9
time/calendar   = 1
```

**Lectura responsable:**

La recategorización mensual/every-period sí funciona y genera eventos auditables, pero en el piloto empeoró el desempeño por alta rotación/cambios frecuentes. Por ahora debe tratarse como modo de investigación, no como configuración principal. La configuración principal sigue siendo `recategorization_policy=rebalance_only` con rebalanceo trimestral.

---

## 2026-05-19 — Fallback robusto del optimizador MaxSharpe

**Tipo:** implementación + robustez numérica  
**Archivos principales:**

- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `tests/test_pipeline.py`
- `tests/test_run_sprint_experiment_preflight.py`
- `results/sprint_universe_paper_quarterly/run_manifest.json`

**Qué se hizo:**

- Se añadió `optimizer_fallback=True` a `PipelineConfig`.
- La estrategia `max_sharpe` ahora puede caer responsablemente a:
  1. `max_sharpe`
  2. `min_variance`
  3. `equal_weight`
- Si se quiere comportamiento fail-fast, se expuso el flag:
  - `--disable-optimizer-fallback`
- El manifiesto reproducible ahora guarda:
  - `optimizer_fallback: true|false`
- Se añadieron tests RED/GREEN para:
  - fallback de MaxSharpe a MinVariance cuando falla el solver;
  - error explícito cuando el fallback está deshabilitado.

**Motivo:**

El roadmap identificó que MaxSharpe puede fallar numéricamente en ventanas cortas o matrices mal condicionadas. Esta funcionalidad evita que una corrida completa se rompa por un fold, sin ocultar la opción de modo estricto.

**Verificación:**

```bash
uv run pytest tests/test_pipeline.py tests/test_run_sprint_experiment_preflight.py -q
uv run pytest -q
uv run ruff check .
```

**Resultado observado:**

```text
123 passed
All checks passed
```

**Experimento regenerado:**

`results/sprint_universe_paper_quarterly/` fue regenerado con `optimizer_fallback=True` en `run_manifest.json`. El resultado principal se mantuvo:

```text
ELECTRE_MaxSharpe_walk_forward CAGR = 13.6083%
Sharpe = 1.4988
Max drawdown = -4.2276%
```

---

## 2026-05-19 — Implementación de rebalanceo por tolerancia y promoción experimento paper-style

**Tipo:** implementación + experimento reproducible  
**Archivos principales:**

- `src/etf_optimizer/backtesting/engine.py`
- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `tests/test_rebalance_policies.py`
- `results/sprint_universe_paper_quarterly/`

**Qué se hizo:**

- Se añadió `rebalance_policy="calendar" | "threshold"`.
- Se añadió `drift_tolerance`, expresado como desviación absoluta de peso, por ejemplo `0.05 = 5 puntos porcentuales`.
- Se agregó `rebalance_events.csv` para auditar cada evento de rebalanceo, su tipo, turnover y drift máximo.
- Se expuso en CLI:
  - `--rebalance-policy calendar|threshold`
  - `--drift-tolerance FLOAT`
- Se promovió el experimento paper-style trimestral a:
  - `results/sprint_universe_paper_quarterly/`

**Comando promovido:**

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe data/universe/etf_universe_clean.csv \
  --prices data/raw/yfinance_pilot/close.parquet \
  --volume data/raw/yfinance_pilot/volume.parquet \
  --start 2020-12-31 \
  --end 2024-12-31 \
  --rebalance quarterly \
  --weight-drift buy_and_hold \
  --rebalance-policy threshold \
  --drift-tolerance 0.05 \
  --electre-assignment pessimistic \
  --disable-veto \
  --compare-electre-variants \
  --cost-bps 10 \
  --out results/sprint_universe_paper_quarterly \
  --min-coverage-pct 0.8 \
  --min-avg-dollar-volume 0
```

**Resultado principal observado:**

```text
ELECTRE_MaxSharpe_walk_forward CAGR = 13.6083%
Sharpe = 1.4988
Max drawdown = -4.2276%
```

**Nota:** en esta corrida threshold no disparó eventos intratrimestrales adicionales; `rebalance_events.csv` registró eventos calendario trimestrales. La funcionalidad queda disponible para ventanas más largas/frecuencias diferentes.

**Verificación:**

```bash
uv run pytest tests/test_rebalance_policies.py -q
```

---

## 2026-05-19 — Funcionalidades ya incorporadas antes de esta investigación

**Tipo:** implementación  
**Archivos principales:**

- `src/etf_optimizer/selection/electre_tri.py`
- `src/etf_optimizer/backtesting/engine.py`
- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `tests/test_electre_tri_modes.py`
- `tests/test_backtesting.py`
- `pyproject.toml`
- `uv.lock`

**Qué se incorporó:**

- ELECTRE Tri con múltiples perfiles/categorías.
- Asignación pesimista y optimista.
- Modo con veto y sin veto.
- Backend interno y backend `pydecision_tri_b`.
- Rebalanceo `constant_mix` y `buy_and_hold`.
- Simulación de drift de pesos entre rebalanceos.
- Exportación de `electre_effective_weights.csv`.
- CLI con:
  - `--weight-drift`
  - `--electre-assignment`
  - `--electre-backend`
  - `--disable-veto`
  - `--compare-electre-variants`

**Verificación ejecutada:**

```bash
uv run pytest -q
uv run ruff check .
```

**Resultado observado:**

```text
119 passed
All checks passed
```

---

## 2026-05-20 — Estado listo para presentación: cap de categoría + recategorización confirmada

**Tipo:** implementación TDD + hardening empírico + artefactos de presentación  
**Archivos principales:**

- `src/etf_optimizer/optimization/exposure.py`
- `tests/test_exposure_controls.py`
- `src/etf_optimizer/pipeline.py`
- `scripts/run_sprint_experiment.py`
- `results/sprint_universe_paper_quarterly_2015_2025_cap025/category_exposure_report.csv`
- `results/sprint_universe_paper_quarterly_2015_2025_every_confirm2_m030_cap025/`
- `docs/traceability/milestone_metrics_history.csv`
- `docs/traceability/milestone_metrics_history.md`

**Qué se hizo:**

- Se añadió un clasificador transparente de buckets ETF (`commodities`, `greater_china`, `natural_resources`, `thematic`, `fixed_income`, `broad_equity`, `other`).
- Se añadió `category_exposure_cap` para limitar exposición por bucket de riesgo y evitar concentraciones como el 78% observado en CGW durante el shock COVID.
- El pipeline ahora amplía la selección si el cap necesita más buckets que los inicialmente seleccionados, preservando la lógica ELECTRE pero evitando carteras infeasibles.
- Cada experimento genera `category_exposure_report.csv`.
- Se promovió el candidato presentable largo 2015-2025: `every_period + confirm2 + materialidad 0.30 + cap 25%`.

**Resultado frente al OOS largo sin cap:**

```text
Baseline largo 2015-2025:       CAGR -1.08%, Sharpe 0.011, Max DD -43.55%, turnover 13.61
Cap categoría 25%:              CAGR  0.41%, Sharpe 0.093, Max DD -24.84%, turnover 10.31
Candidato listo presentación:    CAGR  2.47%, Sharpe 0.247, Max DD -24.01%, turnover  4.02
```

**Interpretación:**

El sistema ya está listo para presentación como investigación reproducible: identifica un fallo de generalización, lo atribuye a concentración temática/commodity/regional, aplica controles auditables y muestra mejoras OOS largas. No se debe presentar como estrategia final que bate a SPY/60-40; sí como pipeline académico defendible y listo para una futura corrida institucional survivorship-bias-free.

---

## 2026-05-20 — Entregables formales de tesis, presentación y front

**Tipo:** documentación final + artefactos de sustentación  
**Archivos principales:**

- `scripts/build_presentation_deliverables.py`
- `tests/test_presentation_deliverables.py`
- `docs/deliverables/tesis_trabajo_grado_etf_electre.docx`
- `docs/deliverables/presentacion_sustentacion_etf_electre.pptx`
- `docs/deliverables/front_presentacion/index.html`
- `docs/deliverables/deliverables_manifest.json`
- `docs/deliverables/README.md`

**Qué se hizo:**

- Se generó documento DOCX en formato de trabajo de grado con resumen, marco teórico, metodología, implementación, resultados, límites, conclusiones, referencias y anexo reproducible.
- Se generó presentación PPTX con narrativa para sustentación.
- Se generó front estático HTML con métricas clave, límites de inferencia y enlaces a entregables.
- Se incluyeron citaciones de métodos, librerías y bases de datos: ELECTRE Tri, Markowitz, Ledoit-Wolf, pandas, NumPy, SciPy, scikit-learn, pyDecision, yfinance/Yahoo Finance, Nasdaq ETF Screener, SEC EDGAR, PyArrow y Streamlit.

**Verificación:**

```text
142 passed
Ruff: All checks passed
DOCX: 62 párrafos, 2 tablas, referencias y pyDecision presentes
PPTX: 5 slides
HTML: métricas clave presentes
```

---

## 2026-06-09 — GOAL 8 diagnóstico de clasificación MCDM/ELECTRE

**Tipo:** validación MCDM / diagnóstico clasificación antes de portafolio  
**Archivos:**

- `src/etf_optimizer/reporting/classification_diagnostics.py`
- `scripts/build_electre_classification_diagnostics.py`
- `tests/test_classification_diagnostics.py`
- `results/electre_classification_diagnostics/classification_effectiveness.csv`
- `results/electre_classification_diagnostics/category_forward_returns.csv`
- `results/electre_classification_diagnostics/category_forward_sharpe.csv`
- `results/electre_classification_diagnostics/category_forward_drawdown.csv`
- `results/electre_classification_diagnostics/pessimistic_optimistic_divergence.csv`
- `results/electre_classification_diagnostics/category_transition_matrix.csv`
- `results/electre_classification_diagnostics/selection_jaccard_by_fold.csv`
- `docs/results/electre_classification_diagnostics.md`

**Qué se hizo:**

- Se separó explícitamente la evaluación de la clasificación ELECTRE de la performance del portafolio.
- Se midieron retornos, Sharpe y drawdown forward por categoría (`below_minimum`, `between_minimum_preferred`, `above_preferred`) usando los folds del baseline `public_approximate_pit`.
- Se recalcularon variantes ELECTRE pesimista/optimista con y sin veto sobre las matrices de criterios fold-level para medir divergencia y efecto del veto.
- Se exportó estabilidad temporal mediante matriz de transición de categorías y Jaccard de selección entre folds consecutivos.

**Hallazgo principal:**

```text
above_preferred no domina a between_minimum_preferred ni a below_minimum en retorno forward, Sharpe ni drawdown.
Jaccard medio de seleccionados entre folds consecutivos: 54.45%.
Pesimista vs optimista sin veto: 75.49% de acuerdo de categoría y 51.36% de Jaccard de seleccionados.
```

**Validación programática:**

```text
python scripts/build_electre_classification_diagnostics.py
pytest tests/test_classification_diagnostics.py tests/test_pipeline.py tests/test_pipeline_walkforward_selection.py -q
15 passed
ruff check src/etf_optimizer/reporting/classification_diagnostics.py scripts/build_electre_classification_diagnostics.py tests/test_classification_diagnostics.py
All checks passed
```

**Caveat:** la evidencia se calcula sobre `public_approximate_pit` y precios públicos; es diagnóstico metodológico de tesis, no claim institucional survivorship-bias-free.

---

## 2026-06-09 — GOAL 9 ablation selección vs asignación

**Tipo:** validación empírica / ablation tests selección ELECTRE vs optimización de pesos  
**Archivos:**

- `src/etf_optimizer/reporting/selection_allocation_ablation.py`
- `scripts/build_selection_allocation_ablation.py`
- `tests/test_selection_allocation_ablation.py`
- `results/ablation_selection_allocation/strategy_comparison.csv`
- `results/ablation_selection_allocation/ablation_grid.csv`
- `results/ablation_selection_allocation/strategy_returns.csv`
- `results/ablation_selection_allocation/equity_curves.csv`
- `results/ablation_selection_allocation/drawdowns.csv`
- `results/ablation_selection_allocation/turnover_summary.csv`
- `docs/results/selection_vs_allocation_ablation.md`

**Qué se hizo:**

- Se corrieron ablations de universo completo con EqualWeight, MinVariance y MaxSharpe.
- Se corrieron ablations ELECTRE con EqualWeight, InverseVol, MinVariance y MaxSharpe.
- Se evaluaron variantes ELECTRE pesimista/optimista con y sin veto, manteniendo EqualWeight para aislar clasificación de optimización.
- Se usaron los mismos fold-stage artifacts del baseline `public_approximate_pit`, ventana 2015-2025, 31 folds trimestrales, `buy_and_hold` y costo 10 bps.

**Hallazgo principal:**

```text
Universe EqualWeight: 5.60% CAGR, Sharpe 0.524, MDD -20.57%.
ELECTRE pessimistic no veto EqualWeight: 2.04% CAGR, Sharpe 0.211, MDD -20.24%.
ELECTRE pessimistic no veto MaxSharpe: 0.15% CAGR, Sharpe 0.084, MDD -24.97%.
Universe MaxSharpe: 2.55% CAGR, Sharpe 0.353, MDD -16.28%.
```

**Interpretación:** ELECTRE EqualWeight pierde contra Universe EqualWeight, por tanto la clasificación no agrega valor neto en el baseline actual. Además MaxSharpe empeora tanto en universo completo como dentro de ELECTRE, lo que apunta a una segunda fuente de daño en optimización/estimación de retornos.

**Validación programática:**

```text
python scripts/build_selection_allocation_ablation.py
pytest tests/test_selection_allocation_ablation.py tests/test_classification_diagnostics.py tests/test_pipeline.py tests/test_pipeline_walkforward_selection.py -q
16 passed
ruff check src/etf_optimizer/reporting/selection_allocation_ablation.py scripts/build_selection_allocation_ablation.py tests/test_selection_allocation_ablation.py
All checks passed
```

**Caveat:** la evidencia usa universo `public_approximate_pit` y precios públicos; útil para diagnóstico de tesis, no para claim institucional survivorship-bias-free.

---

## 2026-06-09 — GOAL 10 diseño de criterios v2 post-ablation

**Tipo:** metodología / recalibración de criterios MCDM sin modificar pipeline  
**Archivos:**

- `configs/criteria_config_v2.yaml`
- `docs/methodology/criteria_design_v2.md`

**Qué se hizo:**

- Se creó una especificación v2 posterior a GOAL 8/9, sin tocar todavía el backtester ni los criterios legacy ejecutados.
- Se elimina `historical_cagr` del MCDM primario y se reemplaza retorno bruto por `momentum_12_1` con peso acotado.
- Se agrega `max_drawdown_24m` como criterio central, más `beta_to_spy_24m` y `marginal_correlation_to_eligible_universe_24m` para controlar beta/redundancia.
- Liquidez, AUM y expense ratio pasan a filtros duros o penalizaciones pequeñas/condicionales a fuente PIT.
- `tracking_error_vs_category_benchmark` queda diferido hasta tener benchmark correcto por categoría.
- Se define filtro de redundancia por correlación >= 0.90 antes de selección final.

**Validación programática:**

```text
python - <<'PY'
from pathlib import Path
import yaml
p=Path('configs/criteria_config_v2.yaml')
data=yaml.safe_load(p.read_text())
criteria=data['criteria']
required={'criterion_name','formula','lookback','orientation','source','missing_data_rule','winsorization','normalization','rationale'}
assert all(required <= set(c) for c in criteria)
assert abs(sum(data['proposed_primary_weight_sum_check']['included_nonzero_weights'].values())-1.0)<1e-9
PY
criteria_config_v2 valid
criteria_count 18
nonzero_weight_sum 1.0
```

**Caveat:** GOAL 10 es diseño metodológico. La siguiente etapa debe implementar features/perfiles v2 y repetir primero el diagnóstico de clasificación antes de afirmar mejora de performance.
