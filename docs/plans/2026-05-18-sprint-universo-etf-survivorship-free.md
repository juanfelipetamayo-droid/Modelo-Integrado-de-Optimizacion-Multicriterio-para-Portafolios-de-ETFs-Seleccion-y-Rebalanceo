# Sprint: Universo amplio de ETFs y backtesting survivorship-bias-aware

**Fecha:** 2026-05-18  
**Proyecto:** `portfolio-etf-optimizer`  
**Meta del sprint:** pasar del MVP técnico a un experimento histórico real con un universo amplio (~2k ETFs), trazable y defendible académicamente, reduciendo survivorship bias.

---

## 1. Decisión metodológica clave

El universo actual del MVP es una lista curada pequeña de ETFs líquidos. Eso sirve para probar código, pero **no sirve todavía para la tesis** porque introduce survivorship bias: solo contiene ETFs conocidos que existen hoy.

Para cumplir el objetivo del paper se necesita un universo histórico que incluya:

- ETFs activos hoy;
- ETFs cerrados/liquidados;
- ETFs fusionados;
- ETFs que existían durante 2021–2024 aunque ya no existan hoy;
- fechas de inicio y fin;
- identificadores trazables: ticker, CIK, nombre legal, exchange, sponsor/fund family.

---

## 2. Fuentes candidatas

### Opción A — CRSP Survivor-Bias-Free US Mutual Fund Database / CRSP Mutual Fund Database

**Tipo:** académica/comercial, estándar en finanzas empíricas.  
**Ventaja:** fuente citable, diseñada para evitar survivorship bias, incluye fondos muertos y vivos.  
**Desventaja:** normalmente requiere acceso universitario/licencia.  
**Uso recomendado:** mejor opción si Universidad del Valle o el director tiene acceso vía WRDS/CRSP.

**Rol en el proyecto:** fuente gold standard para universo y metadatos históricos.

### Opción B — Morningstar Direct / Lipper / Refinitiv / Bloomberg

**Tipo:** comercial institucional.  
**Ventaja:** datos amplios, histórico, fondos cerrados, expense ratios, AUM, categorías.  
**Desventaja:** licencia; exportación debe documentarse.  
**Uso recomendado:** alternativa institucional si hay acceso.

### Opción C — SEC EDGAR como fuente legal pública primaria

**Tipo:** pública/legal/citable.  
**Ventaja:** fuente oficial de la SEC, legalmente citable, auditable, gratuita.  
**Desventaja:** no es una base lista de tickers ETF; toca construir el universo desde filings, entidades registradas y series/classes.

**Uso recomendado:** fuente pública primaria para defender existencia legal de fondos y reducir dependencia de listas actuales.

Fuentes SEC útiles:

- Investment Company submissions;
- N-1A registration statements;
- N-CEN annual reports;
- N-PORT portfolio reports;
- company tickers / submissions API;
- series and class identifiers cuando estén disponibles.

### Opción D — Nasdaq ETF screener / ETF.com / VettaFi ETF Database

**Tipo:** pública/current snapshot.  
**Ventaja:** fácil de obtener, cubre muchos ETFs activos.  
**Desventaja:** usualmente solo activos actuales; no corrige survivorship bias por sí sola.  
**Uso recomendado:** complemento, no fuente principal.

### Opción E — Yahoo Finance / yfinance

**Tipo:** datos de precios públicos, no fuente oficial del universo.  
**Ventaja:** fácil para precios históricos.  
**Desventaja:** cobertura de delisted ETFs es incompleta; no debe usarse como única fuente del universo histórico.

**Uso recomendado:** fuente práctica de precios para prototipo; marcar limitación si no cubre delisted.

---

## 3. Recomendación

Usar una estrategia de dos niveles:

### Nivel 1 — Universo académico ideal

Intentar conseguir acceso a:

1. CRSP Survivor-Bias-Free Mutual Fund Database, o
2. Morningstar Direct / Lipper / Bloomberg.

Si hay acceso, esta será la fuente principal citable para ~2k ETFs y fondos cerrados.

### Nivel 2 — Universo público reproducible

Si no hay acceso institucional, construir un universo público con:

1. SEC EDGAR como fuente legal primaria;
2. Nasdaq/ETF.com/VettaFi como snapshot activo complementario;
3. Yahoo Finance/Stooq/Nasdaq Data Link para precios cuando estén disponibles;
4. un reporte explícito de cobertura y sesgo residual.

El paper debe ser transparente: **si no se obtiene base survivorship-free comercial, no se debe afirmar eliminación total del survivorship bias; se debe afirmar mitigación documentada.**

---

## 4. Objetivo cuantitativo del sprint

Apuntar a:

```text
~2,000 ETFs únicos candidatos
>=1,500 con metadatos básicos
>=1,000 con precios históricos útiles para 2021–2024
>=500 con historial suficiente para ventanas walk-forward robustas
```

La cifra final dependerá de disponibilidad de precios y delisted coverage.

---

## 5. Entregables del sprint

### Entregable 1 — Documento de fuentes y decisión metodológica

Archivo:

```text
docs/data_sources_etf_universe.md
```

Debe incluir:

- tabla comparativa de fuentes;
- licencia/uso permitido;
- citabilidad;
- cobertura de ETFs activos y cerrados;
- limitaciones;
- decisión final.

### Entregable 2 — Esquema de universo histórico

Archivo:

```text
docs/universe_schema.md
```

Columnas objetivo:

```text
fund_id,ticker,name,cik,series_id,class_id,exchange,sponsor,
asset_class,category,inception_date,termination_date,
source,source_url,active_flag,expense_ratio,aum,benchmark
```

### Entregable 3 — Módulo de ingesta de universo

Archivos:

```text
src/etf_optimizer/data/sec_universe.py
src/etf_optimizer/data/public_universe.py
src/etf_optimizer/data/universe_builder.py
```

Funciones mínimas:

```python
load_sec_company_tickers()
load_public_current_etf_snapshot()
merge_universe_sources()
validate_universe_schema()
write_universe_snapshot()
```

### Entregable 4 — Dataset de universo v0

Archivos:

```text
data/universe/etf_universe_raw.csv
data/universe/etf_universe_clean.csv
data/universe/etf_universe_coverage_report.csv
```

### Entregable 5 — Downloader robusto de precios

Extender:

```text
src/etf_optimizer/data/fetcher.py
scripts/download_data.py
```

Debe soportar:

- batches;
- retries;
- logging de fallos;
- output por ticker o matriz parquet;
- reporte de cobertura.

### Entregable 6 — Primer backtest real preliminar

Archivos esperados:

```text
results/sprint_universe_v0/features_table.csv
results/sprint_universe_v0/electre_selection.csv
results/sprint_universe_v0/strategy_comparison.csv
results/sprint_universe_v0/equity_curves.csv
results/sprint_universe_v0/drawdowns.csv
```

Estrategias mínimas:

```text
SPY
60/40 SPY+BND
Equal Weight universo elegible
Min Variance universo elegible
Max Sharpe universo elegible
ELECTRE + Max Sharpe
```

---

## 6. Plan de desarrollo por tareas

### Tarea 1 — Investigar y documentar fuentes

**Objetivo:** decidir fuente principal y fuente fallback.

**Archivos:**

- Crear `docs/data_sources_etf_universe.md`

**Verificación:**

- Documento contiene al menos 5 fuentes.
- Cada fuente tiene licencia/uso, cobertura, sesgo, citabilidad.
- Se declara explícitamente si corrige survivorship bias o no.

### Tarea 2 — Definir esquema canónico de universo

**Objetivo:** evitar que cada fuente tenga columnas incompatibles.

**Archivos:**

- Crear `docs/universe_schema.md`
- Crear `src/etf_optimizer/data/schema.py`
- Crear `tests/test_universe_schema.py`

**Verificación:**

```bash
uv run pytest tests/test_universe_schema.py -q
```

### Tarea 3 — Implementar ingesta pública inicial

**Objetivo:** construir la primera base amplia desde fuentes públicas.

**Archivos:**

- Crear `src/etf_optimizer/data/public_universe.py`
- Crear `tests/test_public_universe.py`

**Verificación:**

- Dedupe por ticker/fund_id.
- Normalización de tickers.
- Validación de columnas requeridas.

### Tarea 4 — Implementar capa SEC EDGAR

**Objetivo:** incorporar fuente legal/citable.

**Archivos:**

- Crear `src/etf_optimizer/data/sec_universe.py`
- Crear `tests/test_sec_universe.py`

**Verificación:**

- Descarga/parsing reproducible.
- Guarda `source_url` y `cik`.
- Respeta rate limits de SEC y user-agent descriptivo.

### Tarea 5 — Construir universe builder

**Objetivo:** unir fuentes, deduplicar y generar snapshot reproducible.

**Archivos:**

- Crear `src/etf_optimizer/data/universe_builder.py`
- Crear `scripts/build_universe.py`
- Crear `tests/test_universe_builder.py`

**Verificación:**

```bash
uv run python scripts/build_universe.py --out data/universe
```

Produce:

```text
etf_universe_raw.csv
etf_universe_clean.csv
etf_universe_coverage_report.csv
```

### Tarea 6 — Mejorar downloader histórico

**Objetivo:** descargar precios para ~2k tickers sin romper por fallos individuales.

**Archivos:**

- Modificar `src/etf_optimizer/data/fetcher.py`
- Modificar `scripts/download_data.py`
- Crear `tests/test_fetcher_batches.py`

**Verificación:**

- Batch download.
- Retries.
- Reporte de tickers fallidos.
- No falla toda la corrida por 1 ticker inválido.

### Tarea 7 — Crear benchmarks clásicos

**Objetivo:** comparar contra estrategias estándar.

**Archivos:**

- Crear `src/etf_optimizer/backtesting/benchmarks.py`
- Crear `tests/test_benchmarks.py`

Benchmarks:

```text
SPY
QQQ
60/40 SPY+BND
Equal Weight
Min Variance
Max Sharpe sin ELECTRE
```

### Tarea 8 — Crear comparison report

**Objetivo:** producir tablas finales del sprint.

**Archivos:**

- Crear `src/etf_optimizer/reporting/tables.py`
- Crear `src/etf_optimizer/reporting/plots.py`
- Crear `scripts/run_sprint_experiment.py`

**Verificación:**

Produce:

```text
strategy_comparison.csv
equity_curves.csv
drawdowns.csv
coverage_report.csv
```

### Tarea 9 — Ejecutar experimento preliminar

**Objetivo:** primer resultado real.

Comando objetivo:

```bash
uv run python scripts/run_sprint_experiment.py \
  --universe data/universe/etf_universe_clean.csv \
  --start 2021-01-01 \
  --end 2024-12-31 \
  --rebalance annual \
  --cost-bps 10 \
  --out results/sprint_universe_v0
```

**Verificación:**

- Tabla comparativa no vacía.
- Al menos 6 estrategias.
- Reporta universo inicial, universo descargado y universo elegible.

---

## 7. Qué se considera terminado al cierre del sprint

El sprint se considera exitoso si tenemos:

1. fuente de universo documentada;
2. universo amplio v0 con trazabilidad;
3. cobertura histórica medida;
4. downloader robusto;
5. primer backtest real 2021–2024;
6. comparación contra estrategias tradicionales;
7. limitaciones claras sobre survivorship bias.

---

## 8. Qué quedaría faltando para versión final

Después de este sprint aún faltaría:

### A. Robustez metodológica

- análisis de sensibilidad ELECTRE;
- variación de pesos;
- variación de lambda;
- perfiles optimistas/pesimistas;
- pruebas con distintos costos de transacción.

### B. Más estrategias

- Risk Parity;
- Mean-Variance con aversión al riesgo;
- CVaR opcional;
- restricciones por sector/asset class.

### C. Validación estadística

- bootstrap;
- intervalos de confianza;
- test de diferencia de Sharpe;
- análisis por subperiodos.

### D. Gráficos finales

- equity curves;
- drawdowns;
- pesos por rebalanceo;
- turnover;
- categorías ELECTRE;
- sensibilidad.

### E. Redacción académica

- metodología final;
- resultados;
- discusión;
- limitaciones;
- apéndice reproducible.

---

## 9. Estimación de avance

Estado actual aproximado:

```text
MVP técnico: 25–30%
Experimento empírico real: 0–10%
Versión defendible del paper: 20–25%
```

Después de este sprint:

```text
MVP técnico: 45–55%
Experimento empírico real: 35–45%
Versión defendible del paper: 40–50%
```

Para versión final quedarían aproximadamente:

```text
50–60% del trabajo académico/experimental
```

Principalmente en robustez, validación estadística, sensibilidad y escritura.

---

## 10. Riesgo principal

El riesgo crítico es **survivorship bias**.

Si usamos solo fuentes actuales gratuitas, el paper debe decir:

> El universo se construyó con fuentes públicas actuales y filings SEC, por lo que se mitiga parcialmente el sesgo de supervivencia, pero no se elimina por completo por ausencia de una base survivor-bias-free institucional.

Si conseguimos CRSP/Morningstar/Lipper, podremos afirmar una cobertura histórica mucho más fuerte.
