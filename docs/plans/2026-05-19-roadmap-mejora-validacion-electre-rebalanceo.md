# Roadmap de Mejora e Investigación — ELECTRE Tri, Validación Empírica y Rebalanceo

> **Para Hermes:** ejecutar este plan por fases con TDD, sin sobrescribir resultados oficiales sin autorización. Toda funcionalidad nueva debe quedar registrada en `docs/traceability/feature_log.md` y en los artefactos generados por el experimento.

**Goal:** Convertir el proyecto en una tesis defendible y empíricamente sólida, manteniendo el modelo del paper citado y añadiendo modos comparativos sin eliminar funcionalidades existentes.

**Architecture:** El sistema debe separar claramente: selección multicriterio ELECTRE Tri, backend de clasificación, política de rebalanceo, simulación de pesos efectivos, optimización posterior y validación empírica. Cada modo debe ser parametrizable por CLI/configuración y producir artefactos auditables.

**Tech Stack:** Python 3.11, pandas, scipy/sklearn, pyDecision, pytest, ruff, Streamlit, artefactos CSV/JSON/Markdown.

---

## Principios de ejecución

1. **No simplificar el modelo:** replicar el enfoque del paper citado y añadir modos; no reemplazarlo por rankings simples.
2. **No borrar funcionalidad existente:** todo cambio debe ser aditivo salvo bug claro.
3. **Trazabilidad obligatoria:** cada funcionalidad nueva debe documentar archivo, comando, test y motivo.
4. **Validación antes de conclusiones:** no declarar superioridad si no hay OOS suficiente y comparación estadística.
5. **Resultados oficiales controlados:** usar `/tmp` para pruebas; mover a `results/` solo cuando se decida promover el experimento.

---

# Fase 0 — Estado ya implementado en esta sesión

## Funcionalidades incorporadas

- ELECTRE Tri con múltiples perfiles/categorías.
- Asignación `pessimistic` y `optimistic`.
- Modo con veto y sin veto.
- Backend interno y backend `pydecision_tri_b` vía pyDecision.
- Motor de rebalanceo con `constant_mix` y `buy_and_hold`.
- Simulación de drift de pesos entre rebalanceos.
- Exportación de `electre_effective_weights.csv`.
- CLI con `--weight-drift`, `--electre-assignment`, `--electre-backend`, `--disable-veto`, `--compare-electre-variants`.

## Verificación ejecutada

```bash
uv run pytest -q
uv run ruff check .
```

Resultado observado:

```text
119 passed
All checks passed
```

---

# Fase 1 — Promover experimento paper-style trimestral

**Objetivo:** Crear un experimento oficial reproducible que refleje el paper y supere el umbral mínimo de 10% anual en evidencia piloto.

## Task 1.1 — Promover corrida trimestral pesimista sin veto

**Archivos:**
- Crear/actualizar: `results/sprint_universe_paper_quarterly/`
- Registrar: `docs/traceability/feature_log.md`

**Comando base:**

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe data/universe/etf_universe_clean.csv \
  --prices data/raw/yfinance_pilot/close.parquet \
  --volume data/raw/yfinance_pilot/volume.parquet \
  --start 2020-12-31 \
  --end 2024-12-31 \
  --rebalance quarterly \
  --weight-drift buy_and_hold \
  --electre-assignment pessimistic \
  --disable-veto \
  --compare-electre-variants \
  --cost-bps 10 \
  --out results/sprint_universe_paper_quarterly \
  --min-coverage-pct 0.8 \
  --min-avg-dollar-volume 0
```

**Acceptance criteria:**

- Existe `strategy_comparison.csv`.
- Existe `methodology_variant_comparison.csv`.
- Existe `electre_effective_weights.csv`.
- `ELECTRE_MaxSharpe_walk_forward` tiene CAGR documentado.
- El reporte advierte que sigue siendo evidencia piloto.

---

# Fase 2 — Rebalanceo flexible avanzado

**Objetivo:** Pasar de calendario simple a políticas de rebalanceo comparables y realistas.

## Task 2.1 — Añadir política por tolerancia de drift

**Nuevo concepto:** rebalancear si el peso efectivo se aleja del peso objetivo más que un umbral.

**Ejemplo:**

```text
objetivo = 10%
tolerancia = 3pp
rebalancear si peso < 7% o peso > 13%
```

**Archivos:**
- Modificar: `src/etf_optimizer/backtesting/engine.py`
- Crear tests: `tests/test_rebalance_policies.py`

**API sugerida:**

```python
BacktestConfig(
    weight_drift="buy_and_hold",
    rebalance_policy="calendar" | "threshold" | "category_change" | "hybrid",
    drift_tolerance=0.03,
)
```

**Acceptance criteria:**

- `calendar` conserva comportamiento actual.
- `threshold` rebalancea cuando el peso efectivo supera tolerancia.
- Se registra turnover adicional.
- Costes se aplican solo cuando hay operación real.

## Task 2.2 — Re-categorización mensual con rebalanceo trimestral

**Objetivo:** Recalcular categorías ELECTRE mensualmente, pero operar solo si cambia el grupo o llega fecha de rebalanceo.

**Archivos:**
- Modificar: `src/etf_optimizer/pipeline.py`
- Modificar: `scripts/run_sprint_experiment.py`
- Tests: `tests/test_pipeline_recategorization.py`

**Parámetros CLI sugeridos:**

```bash
--recategorization monthly|quarterly|annual|rebalance_only
--rebalance-trigger calendar|category_change|threshold|hybrid
```

**Acceptance criteria:**

- `rebalance_only` conserva comportamiento actual.
- `monthly + category_change` genera eventos auditables.
- Se exporta `electre_category_events.csv`.

---

# Fase 3 — Robustez del optimizador posterior

**Objetivo:** Evitar fallos numéricos de MaxSharpe sin alterar ELECTRE Tri.

## Task 3.1 — Fallback explícito de optimización

**Archivos:**
- Modificar: `src/etf_optimizer/optimization/portfolio.py`
- Modificar: `src/etf_optimizer/pipeline.py`
- Tests: `tests/test_optimizer_fallback.py`

**API sugerida:**

```python
optimizer_fallbacks=["max_sharpe", "min_variance", "equal_weight"]
```

**Acceptance criteria:**

- Si `max_sharpe` falla, se registra el fallo y se usa `min_variance`.
- Si todos fallan, se usa `equal_weight` como último recurso.
- Se exporta `optimizer_diagnostics.csv`.

---

# Fase 4 — Criterios ETF-specific

**Objetivo:** Que ELECTRE Tri evalúe ETFs con variables propias de ETFs, no solo retornos históricos.

## Task 4.1 — Añadir beta, max drawdown y tracking error

**Archivos:**
- Modificar: `src/etf_optimizer/features.py`
- Tests: `tests/test_features_etf_specific.py`

**Criterios candidatos:**

```text
cagr: max
volatility: min
sharpe: max
sortino: max
max_drawdown: min
beta_spy: target/range o min desviación respecto a perfil
tracking_error_spy: min
```

**Acceptance criteria:**

- Las métricas se calculan solo con ventana de entrenamiento.
- No hay look-ahead bias.
- Las columnas aparecen en `features_table.csv`.

## Task 4.2 — Investigar fuentes para expense ratio, AUM y spread

**Entregable:** `docs/research_sources.md` actualizado con fuentes candidatas, licencia, cobertura y riesgo de survivorship bias.

**Fuentes a evaluar:**

- Nasdaq ETF screener.
- SEC/EDGAR.
- ETF.com si los términos lo permiten.
- Kaggle/datasets públicos solo si son reproducibles.
- Proveedor institucional si se consigue.

---

# Fase 5 — Validación empírica thesis-grade

**Objetivo:** Superar evidencia piloto.

## Task 5.1 — Aumentar historia y folds

**Criterio mínimo:**

```text
>= 5 folds
>= 60 meses OOS
```

**Artefactos requeridos:**

- `fold_diagnostics.json`
- `fold_diagnostics.csv`
- `strategy_comparison.csv`
- `methodology_variant_comparison.csv`
- `bootstrap_metric_intervals.csv`

## Task 5.2 — Comparación estadística pareada

**Archivos:**
- Crear/modificar: `src/etf_optimizer/reporting/statistical_tests.py`
- Tests: `tests/test_statistical_tests.py`

**Métricas:**

- diferencia CAGR vs SPY/60-40;
- diferencia Sharpe;
- diferencia drawdown;
- bootstrap pareado de retornos mensuales;
- intervalos de confianza.

**Acceptance criteria:**

- Exporta `paired_benchmark_tests.csv`.
- Reporta si la diferencia es positiva, negativa o no concluyente.

---

# Fase 6 — Dashboard y trazabilidad de modos

**Objetivo:** Que el usuario pueda ver qué metodología produjo cada resultado.

## Task 6.1 — Mostrar modo metodológico en dashboard

**Archivos:**
- Modificar: `src/etf_optimizer/dashboard/app.py`

**Mostrar:**

```text
ELECTRE assignment
veto on/off
backend
weight drift
rebalance frequency
selected assets
CAGR / Sharpe / drawdown
```

## Task 6.2 — Página de trazabilidad

**Archivos:**
- Modificar: `src/etf_optimizer/dashboard/app.py`
- Usar: `docs/traceability/feature_log.md`

**Acceptance criteria:**

- El dashboard lista funcionalidades incorporadas y artefactos producidos.
- Enlaza a `run_manifest.json`, `provenance.json` y `methodology_report.md`.

---

# Fase 7 — Redacción académica

**Objetivo:** Convertir la implementación en argumento defendible.

## Task 7.1 — Actualizar marco metodológico

**Archivo:** `docs/methodology.md`

Debe cubrir:

- ELECTRE Tri según paper;
- perfiles/categorías;
- asignación pesimista/optimista;
- veto/no veto;
- backend interno vs pyDecision;
- rebalanceo calendario vs drift;
- límites de evidencia piloto;
- criterios de validación thesis-grade.

## Task 7.2 — Tabla de contribuciones

**Archivo:** `docs/methodology.md`

Añadir tabla:

```text
Contribución | Implementación | Artefacto | Limitación
```

---

# Comandos de verificación global

```bash
uv run pytest -q
uv run ruff check .
```

# Criterio para promover resultados

Un resultado puede marcarse como candidato principal solo si cumple:

1. CAGR > 10% anual.
2. Sharpe competitivo frente a MaxSharpe y 60/40.
3. Drawdown razonable.
4. Al menos 5 folds o advertencia explícita de piloto.
5. Artefactos completos de trazabilidad.
6. Comparación contra SPY, 60/40, EqualWeight, MinVariance y MaxSharpe.

