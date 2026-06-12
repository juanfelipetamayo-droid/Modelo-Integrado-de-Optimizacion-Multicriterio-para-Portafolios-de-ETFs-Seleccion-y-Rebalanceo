## Context

El proyecto ya cuenta con pipeline de selección ELECTRE Tri, optimización, backtesting, diagnósticos de clasificación y reportes de calidad. Sin embargo, la revalidación experimental del 2026-06-11 mostró que las corridas actuales siguen limitadas por un universo `public_approximate_pit` con verdict `public_point_in_time_pilot`, criterios ETF incompletos y selección por rebalanceo fuera del rango 10-25.

Los objetivos aceptados del trabajo de grado exigen considerar rendimiento, volatilidad, Sharpe Ratio, liquidez, _tracking error_ y _expense ratio_; reducir el universo estadounidense a 10-25 activos sobre 2021-2024; validar consistencia de selección; y comparar el modelo contra estrategias tradicionales. El objetivo específico 3 se reformula de forma más realista para evaluar empíricamente ventajas frente a benchmarks, sin presuponer superioridad.

La ventana principal 2021-2024/2025 coincide con la disponibilidad pública útil de SEC N-PORT/N-CEN, por lo que una capa regulatoria enriquecida es proporcional y defendible para tesis. La ventana 2015-2025 se mantiene como robustez extendida, no como evidencia principal fully point-in-time.

## Goals / Non-Goals

**Goals:**

- Definir una arquitectura de datos pública/regulatoria para ETFs que mejore el universo `public_approximate_pit` y permita un verdict más fuerte en la ventana principal.
- Controlar _lookahead bias_ mediante separación explícita de `as_of_date`, `filed_date`, `accepted_datetime`, `public_available_date`, `decision_date` y `rebalance_date`.
- Normalizar identificadores ETF más allá del ticker usando CIK, series/class IDs, CUSIP, ISIN y FIGI, con confianza de mapeo.
- Cubrir de forma verificable los criterios de tesis: rendimiento, volatilidad, Sharpe, liquidez, _tracking error_ y _expense ratio_, además de AUM, antigüedad, categoría, benchmark y eventos de inicio/cierre cuando estén disponibles.
- Definir una matriz fuente-campo-fallback-confianza que permita corroborar cumplimiento casi completo de los objetivos.
- Exigir selección final 10-25 ETFs por rebalanceo para el protocolo principal.
- Distinguir claims permitidos y no permitidos según calidad de datos.

**Non-Goals:**

- No construir un universo institucional equivalente a CRSP/ETF Global/Refinitiv.
- No afirmar que el dataset público es fully point-in-time o survivor-bias-free para 2015-2025.
- No depender de vendors pagos para cerrar requisitos mínimos.
- No usar scraping comercial como fuente primaria si sus términos de uso no permiten el uso académico/reproducible.
- No garantizar que la estrategia supere SPY o 60/40; solo se exige evaluación empírica y reporte transparente.

## Decisions

### Decision 1: Usar un universo `regulatory_enriched_pit` para el protocolo principal

La fuente primaria del universo 2021-2024/2025 será una capa enriquecida con SEC N-PORT, SEC N-CEN, EDGAR submissions, OpenFIGI, metadatos de emisores y precios públicos.

Alternativas consideradas:

- Mantener `public_approximate_pit`: menos esfuerzo, pero no cierra las brechas de criterios ETF ni auditabilidad.
- Buscar un dataset público único de ETFs: deseable, pero no parece existir con cobertura, licencias y calidad suficientes.
- Usar vendors pagos: metodológicamente fuerte, pero fuera del alcance público/reproducible del proyecto.

### Decision 2: Separar identidad, filings, snapshots, features y reportes

La arquitectura conceptual se divide en tablas lógicas:

```text
SEC / EDGAR / Issuers / OpenFIGI / Prices
                │
                ▼
        ┌─────────────────┐
        │ source_registry │
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │ security_master │
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │ filing_index    │
        └────────┬────────┘
                 ▼
 ┌───────────────────────────────┐
 │ fund_snapshot / holdings_snap │
 └───────────────┬───────────────┘
                 ▼
        ┌─────────────────┐
        │ benchmark_map   │
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │ price_history   │
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │ electre_features│
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │ thesis reports  │
        └─────────────────┘
```

Esta separación permite auditar de dónde viene cada criterio y evitar que datos publicados después del rebalanceo entren en la decisión.

### Decision 3: Definir `public_available_date` como barrera temporal principal

Una feature solo puede alimentar ELECTRE en una fecha de decisión si cumple:

```text
feature.public_available_date <= decision_date
feature.measurement_date <= decision_date
feature.qc_status != invalid
```

Si solo existe `as_of_date` pero no fecha de publicación, el sistema debe aplicar un lag conservador configurable y marcar el fallback.

### Decision 4: Usar OpenFIGI como resolución de identificadores, no como fuente histórica absoluta

OpenFIGI mejora joins entre ticker, CUSIP, ISIN y FIGI, pero no reemplaza EDGAR ni el historial propio de identificadores. Cada mapeo debe guardar confianza, fecha de consulta y vigencia estimada.

### Decision 5: Tratar benchmark mapping por niveles de confianza

El _tracking error_ puede calcularse contra:

1. benchmark oficial con serie pública disponible;
2. benchmark declarado por issuer con proxy público documentado;
3. benchmark inferido por categoría/asset class;
4. missing/no calculable.

El reporte debe distinguir estos niveles para no afirmar “tracking error oficial” cuando se usen proxies.

### Decision 6: Reformular objetivo específico 3 como evaluación empírica realista

Formulación operativa propuesta:

> Desarrollar e implementar un modelo de optimización de portafolios que busque mejorar la rentabilidad ajustada por riesgo y controlar la exposición al riesgo, con el propósito de construir portafolios eficientes y evaluar empíricamente si el enfoque multicriterio ofrece ventajas frente a estrategias de inversión tradicionales.

Esto mantiene verbos en infinitivo y conserva la ambición, pero evita convertir un resultado empírico incierto en premisa.

## Data Model

### `source_registry`

- `source_id`
- `source_name`
- `source_type`: `regulatory`, `issuer`, `identifier_api`, `price_api`, `web_reference`, `manual_curated`
- `base_url`
- `license_or_terms_summary`
- `allowed_use`: `primary`, `fallback`, `manual_reference`, `disallowed`
- `retrieval_method`
- `rate_limit_policy`
- `quality_rank`
- `notes`

### `security_master`

- `security_id`
- `ticker`
- `cusip`
- `isin`
- `figi`
- `cik`
- `series_id`
- `class_id`
- `fund_name`
- `issuer`
- `exchange`
- `currency`
- `inception_date`
- `closure_date`
- `valid_from`
- `valid_to`
- `identifier_confidence`
- `identity_qc_flags`

### `filing_index`

- `filing_id`
- `source_id`
- `cik`
- `accession_number`
- `form_type`
- `period_end_date`
- `filed_date`
- `accepted_datetime`
- `public_available_date`
- `source_url`
- `is_amendment`
- `amends_accession`
- `filing_qc_flags`

### `fund_snapshot`

- `security_id`
- `filing_id`
- `as_of_date`
- `filed_date`
- `public_available_date`
- `aum_or_net_assets`
- `nav`
- `shares_outstanding`
- `expense_ratio`
- `issuer`
- `category`
- `asset_class`
- `benchmark_name`
- `etf_flag`
- `confidence`
- `snapshot_qc_flags`

### `holdings_snapshot`

- `security_id`
- `filing_id`
- `holding_id`
- `as_of_date`
- `public_available_date`
- `holding_name`
- `holding_cusip`
- `holding_isin`
- `holding_figi`
- `market_value`
- `weight`
- `shares`
- `asset_type`
- `sector`
- `country`
- `holding_qc_flags`

### `benchmark_map`

- `security_id`
- `benchmark_id`
- `benchmark_name`
- `benchmark_ticker_or_proxy`
- `benchmark_type`: `official`, `issuer_stated`, `proxy`, `inferred`, `missing`
- `valid_from`
- `valid_to`
- `mapping_confidence`
- `mapping_rationale`

### `price_history`

- `security_id`
- `date`
- `open`
- `high`
- `low`
- `close`
- `adjusted_close`
- `volume`
- `dividend`
- `split`
- `source_id`
- `retrieved_at`
- `price_qc_flags`

### `electre_features_pit`

- `security_id`
- `decision_date`
- `rebalance_date`
- `criterion`
- `value`
- `source_id`
- `source_date`
- `public_available_date`
- `fallback_level`: `primary`, `secondary`, `proxy`, `missing`
- `confidence`
- `qc_flags`

## Criterion-to-Source Matrix

| Objetivo | Criterio / dato | Fuente principal | Campo / derivación | Fallback | Confianza esperada |
|---|---|---|---|---|---|
| General | Rendimiento | Precios públicos ajustados | retornos trailing/OOS | yfinance/Stooq cross-check | Media |
| General | Volatilidad | Precios públicos ajustados | desviación anualizada | fuente alternativa de precios | Media |
| General | Sharpe Ratio | Precios + risk-free/proxy | retorno excedente / volatilidad | tasa cero o T-bill proxy documentado | Media |
| General | Liquidez | Precios/volumen | ADV, dollar volume, trading days | fuente secundaria de OHLCV | Media |
| General | Tracking error | `benchmark_map` + precios | std(ret ETF - ret benchmark) | proxy por categoría | Media |
| General | Expense ratio | issuer/prospectus/SEC | net/gross expense ratio | factsheet issuer; missing etiquetado | Media/Alta |
| Obj. 1 | Universo activo | EDGAR/N-CEN/N-PORT | filings + ETF flag + identifiers | issuer/OpenFIGI/precios | Media/Alta 2021+ |
| Obj. 1 | Inception/closure | EDGAR + issuer | first filing, launch, closure | first/last valid price con flag | Media |
| Obj. 1 | Categoría/peer group | issuer + taxonomía propia | asset_class/category | OpenFIGI/manual curated | Media |
| Obj. 1 | Selección 10-25 | ELECTRE + regla final | ranking elegibles por fecha | fallback por score con flags | Alta |
| Obj. 2 | Consistencia ordinal | diagnósticos ELECTRE | monotonicidad forward | bootstrap/sensitivity | Alta metodológica |
| Obj. 2 | Estabilidad | selección por rebalanceo | Jaccard/turnover | ventanas alternativas | Alta metodológica |
| Obj. 3 | Benchmarks tradicionales | SPY, 60/40, universe EW | CAGR, Sharpe, MDD, Sortino | BND/AGG variantes | Alta |
| Obj. 3 | Ventaja empírica | backtest OOS | comparación ajustada por riesgo | reporte negativo explícito | Alta metodológica |

## Claims Policy

Claims permitidos:

- “Universo ETF público/regulatorio enriquecido”.
- “Control point-in-time aproximado mediante fechas de disponibilidad”.
- “Reducción de lookahead bias frente al universo público piloto”.
- “Evaluación empírica contra benchmarks tradicionales”.
- “Tracking error calculado contra benchmark oficial o proxy documentado”.

Claims no permitidos salvo evidencia adicional:

- “Fully point-in-time”.
- “Survivorship-bias-free institucional”.
- “Universo completo de ETFs estadounidenses”.
- “Tracking error oficial para todos los ETFs”.
- “El enfoque genera alpha” o “siempre supera benchmarks”.

## Risks / Trade-offs

- **Lookahead bias por usar `as_of_date` sin `public_available_date`** → Requerir fechas de publicación o aplicar lag conservador y flags de fallback.
- **Survivorship bias por cierres incompletos** → Registrar closure/inception cuando se detecte; reportar cobertura y no reclamar universo survivor-bias-free.
- **Ticker reuse / identifier drift** → Usar `security_id` estable y tabla de identificadores con vigencia y confianza.
- **Benchmark mapping incompleto** → Clasificar benchmark como oficial/proxy/inferido/missing y degradar claims.
- **Scraping de emisores o sitios comerciales** → Preferir SEC y descargas oficiales; clasificar fuentes comerciales como fallback/manual_reference si hay dudas legales.
- **Demasiados criterios con datos incompletos** → Mantener núcleo de criterios aceptados y agregar AUM/edad/concentración como enriquecimiento con flags.
- **Performance puede no superar benchmarks** → Reportar resultado como evidencia empírica; no esconder resultados negativos.

## Migration Plan

1. Mantener el pipeline actual como baseline reproducible.
2. Introducir la arquitectura nueva como modo adicional de universo y no como reemplazo inmediato.
3. Construir primero registros fuente e identidad (`source_registry`, `security_master`, `filing_index`).
4. Generar snapshots y features PIT para 2021-2024/2025.
5. Ejecutar validación principal y comparar contra baseline `public_approximate_pit`.
6. Solo promover el nuevo modo a evidencia principal si los reportes de calidad cumplen criterios mínimos.
7. Mantener 2015-2025 como validación extendida con verdict degradado.

## Open Questions

- ¿Qué lag conservador usar cuando una fuente no expone `public_available_date` exacta?
- ¿Qué fuente pública se usará para tasas libres de riesgo si Sharpe se calcula con retorno excedente?
- ¿Qué benchmark proxy se usará por categoría cuando no exista benchmark oficial con serie pública?
- ¿Cuál será el umbral mínimo de cobertura para declarar `thesis_aligned_public_regulatory_pit`?
- ¿Qué fuentes de issuer son aceptables según términos de uso para uso académico y reproducible?
