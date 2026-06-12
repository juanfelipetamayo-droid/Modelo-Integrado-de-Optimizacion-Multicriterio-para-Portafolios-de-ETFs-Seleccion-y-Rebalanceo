# Decisión final de ruta de datos ETF PIT 2015–2025

Fecha: 2026-06-09

## Veredicto ejecutivo

La ruta de datos queda cerrada así:

```text
source_primary: Norgate Data US Stocks Platinum + SEC EDGAR
source_secondary: SEC EDGAR-only + precios públicos ajustados como fallback inmediato sin pago
conditional_alternative: Polygon/Massive + SEC EDGAR solo si se valida cobertura de ETFs/ETNs delisted y tratamiento de dividendos/distribuciones

data_quality_verdict: primary = commercial_pit_validated_with_sec; secondary = public_approximate_pit
survivorship_bias_free: partial
pit_universe_supported: true para Norgate+SEC si se confirma cobertura ETF/ETN delisted; partial para SEC-only
total_return_supported: partial hasta validar política exacta de adjusted/total-return de Norgate para ETFs; partial/false para Polygon hasta validación de dividendos; partial para SEC-only vía N-PORT desde 2019Q4+ y precios públicos ajustados
cost: Norgate Platinum observado USD 630/año o USD 346.50/6 meses + SEC gratis; SEC-only gratis; Polygon/Massive según plan público, pero no aprobado
implementation_time: Norgate+SEC 7–14 días después de aprobación/licencia; SEC-only 21–30 días para v1 auditable; Polygon+SEC 10–20 días después de validar plan/campos
```

**Decisión:** usar **Norgate + SEC EDGAR** como diseño tesis-grade preferido sin CRSP/WRDS, pero no pagar ni iniciar trial sin aprobación explícita. Mientras no exista aprobación de pago, implementar únicamente la ruta **SEC-only + precios públicos** como aproximación pública y etiquetarla explícitamente como `public_approximate_pit`, no como CRSP-grade ni como survivorship-bias-free perfecto.

**Bloqueo activo:** no avanzar a tuning de modelo hasta que el pipeline de universo PIT tenga al menos un modo implementado y auditable, con reporte de cobertura por año/fold.

## Fuente principal: Norgate Data + SEC EDGAR

### Qué cubre

- **Norgate** será la autoridad comercial principal para precios diarios, volumen, instrumentos activos y delisted dentro del paquete US Stock Market Platinum/Diamond, siempre que la validación previa confirme que los Exchange Traded Products incluyen ETFs/ETNs/ETMFs delisted necesarios para 2015–2025.
- **SEC EDGAR** será la capa oficial/citable para trazabilidad académica: `CIK`, series/class, ticker, exchange, N-CEN, N-PORT, fechas observables y filing lags.

### Evidencia primaria

- Norgate US Stock Market packages: https://norgatedata.com/stockmarketpackages.php
- Norgate data content tables: https://norgatedata.com/data-content-tables.php
- Norgate prices: https://norgatedata.com/prices.php
- Norgate FAQ/API/licencia: https://norgatedata.com/faq.php
- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC company ticker/exchange JSON: https://www.sec.gov/files/company_tickers_exchange.json
- SEC Investment Company Series/Class annual CSV ejemplo 2015: https://www.sec.gov/files/investment/data/other/investment-company-series-and-class-information/investment_company_series_class_2015.csv
- SEC Form N-PORT data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- SEC Form N-CEN data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets

### Veredicto de calidad

```text
source_primary: Norgate Data US Stocks Platinum + SEC EDGAR
data_quality_verdict: commercial_pit_validated_with_sec
survivorship_bias_free: partial
pit_universe_supported: true, condicionado a validación de cobertura ETF/ETN delisted
survivorship_bias_rationale: Norgate incluye delisted securities en Platinum/Diamond y declara paquetes aptos para backtesting, pero su cobertura delisted no debe describirse como perfecta ni equivalente a CRSP hasta validación/documentación contractual.
total_return_supported: partial
total_return_rationale: Norgate documenta precios ajustados y datos corporativos; antes de afirmar total return ETF hay que probar tratamiento de dividendos/distribuciones y liquidaciones/delistings para ETFs/ETNs.
limitations:
  - No es CRSP/WRDS.
  - Requiere presupuesto y aprobación previa.
  - Norgate debe validarse en muestra de ETFs vivos, liquidados, fusionados y ETNs.
  - Delisted coverage debe declararse como práctica/comercial, no como exhaustiva si el proveedor no garantiza completitud absoluta.
  - SEC no cubre perfectamente ETNs o ETPs que no sean registered investment companies.
cost: USD 630/año observado para US Stocks Platinum; USD 346.50/6 meses; SEC gratis.
implementation_time: 7–14 días después de aprobación, instalación y validación inicial.
```

### Decisión operativa

Seleccionar esta ruta como **principal** para la tesis si se aprueba el gasto. La compra/trial requiere aprobación explícita. Antes de pagar, enviar al proveedor una checklist mínima:

1. ¿US Stocks Platinum incluye ETFs, ETNs y ETMFs activos y delisted para 2015–2025?
2. ¿Los adjusted prices de ETFs incorporan dividendos/distribuciones o solo splits/corporate actions?
3. ¿Existe campo/evento de liquidación, merger o último día de negociación usable para delisted ETPs?
4. ¿La licencia permite reportar resultados agregados en tesis académica?
5. ¿El paquete Python permite exportar universo, precios y metadata suficientes para reproducibilidad local?

## Fuente secundaria: SEC-only + precios públicos

### Qué cubre

Ruta sin pago para construir un universo ETF aproximado por fecha usando fuentes oficiales públicas y precios gratuitos/abiertos como capa separada. Esta ruta es implementable ahora, pero debe etiquetarse como aproximación pública.

### Evidencia primaria

- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC company ticker/exchange JSON: https://www.sec.gov/files/company_tickers_exchange.json
- SEC Series/Class annual CSVs: https://www.sec.gov/files/investment/data/other/investment-company-series-and-class-information/investment_company_series_class_2015.csv
- SEC N-PORT data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- SEC N-CEN data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets
- Nasdaq Trader Symbol Directory supplement: https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs
- Nasdaq `otherlisted.txt` current supplement: https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt
- Stooq historical data supplement: https://stooq.com/db/h/
- Yahoo Finance historical page only as prototype/sanity check, not source académica contractual: https://finance.yahoo.com/quote/SPY/history/

### Veredicto de calidad

```text
source_secondary: SEC EDGAR-only + public adjusted prices
data_quality_verdict: public_approximate_pit
survivorship_bias_free: partial
pit_universe_supported: partial
total_return_supported: partial
limitations:
  - Series/Class es legal/registral y anual, no un security master diario.
  - N-CEN/N-PORT tienen rezago; hay que aplicar `available_as_of` para evitar look-ahead.
  - N-PORT es más útil desde el régimen moderno 2019Q4+, por tanto no cubre igual todo 2015–2025.
  - SEC no es una fuente lista de precios diarios.
  - Precios públicos pueden perder ETFs liquidados, cambios de ticker, distribuciones, liquidating returns o historia corregida.
  - ETNs y ciertos ETPs pueden quedar fuera o requerir Norgate/vendor.
cost: gratis.
implementation_time: 21–30 días para v1 usable con parser, lag register, coverage report y backtest etiquetado.
```

### Decisión operativa

Usar esta ruta como **fallback inmediato** y como control de transparencia incluso si luego se compra Norgate. Su valor académico es que permite explicar y auditar el problema de universo PIT con fuentes oficiales. Su límite es que no debe venderse como base completa survivorship-bias-free.

## Ruta alternativa condicionada: Polygon/Massive + SEC EDGAR

### Evidencia primaria

- Polygon/Massive all tickers: https://polygon.io/docs/rest/stocks/tickers/all-tickers
- Polygon/Massive aggregates/custom bars: https://polygon.io/docs/rest/stocks/aggregates/custom-bars
- Polygon/Massive pricing: https://polygon.io/pricing

### Veredicto de calidad

```text
conditional_alternative: Polygon/Massive + SEC EDGAR
data_quality_verdict: api_pit_candidate_requires_validation
survivorship_bias_free: partial, not proven
pit_universe_supported: partial/true candidate via ticker date, active flag and delisted_utc
total_return_supported: partial/unknown until dividend/distribution adjustment is validated
limitations:
  - `date`, `active` y `delisted_utc` ayudan a reconstruir símbolos por fecha, pero no prueban por sí solos completitud de ETFs/ETNs delisted.
  - `adjusted` aggregates no debe asumirse como total return ETF completo sin validar dividendos/distribuciones.
  - Requiere revisar plan, límites, historia disponible, corporate actions y licenciamiento.
cost: planes públicos según pricing; no aprobado.
implementation_time: 10–20 días después de validar plan/campos.
```

### Decisión operativa

No escoger como ruta principal ahora. Mantenerla como plan B pagado/API-first si Norgate no se aprueba o falla la validación. Para desplazar a Norgate, Polygon/Massive tendría que pasar una prueba de cobertura contra una muestra de ETFs vivos, liquidados y fusionados de 2015–2025, y demostrar retorno ajustado por distribuciones.

## Matriz de decisión resumida

| Ruta | Costo | Calidad PIT | Delisted | Total return | Riesgo académico | Riesgo técnico | Tiempo | Decisión |
|---|---:|---|---|---|---|---|---|---|
| Norgate + SEC | ~USD 630/año + SEC gratis | Alta práctica, condicionada | Alta práctica, no perfecta | Parcial hasta validar ETF distributions | Bajo-medio | Medio | 7–14 días | Principal si se aprueba pago |
| SEC-only + públicos | Gratis | Media/parcial | Media-baja | Parcial | Medio | Alto | 21–30 días | Secundaria/fallback inmediato |
| Polygon/Massive + SEC | Plan pago/API | Media-alta candidata | Media, requiere prueba | Parcial/desconocido | Medio | Medio | 10–20 días | Alternativa condicionada |
| Institutional Morningstar/Bloomberg/LSEG/Lipper/FactSet | Licencia institucional | Muy alta si hay módulo histórico | Muy alta si contratado | Alta | Bajo | Medio | 14–45 días | Mejor si universidad otorga acceso |
| Nasdaq/Yahoo/Stooq/Tiingo/EODHD/Kibot/GitHub/Kaggle/foros | Gratis/pago variable | Baja como autoridad principal | Baja/desconocida | Variable | Alto si se usa como principal | Bajo-medio | 1–10 días | Solo suplementos/leads |

## Limitaciones que deben declararse en tesis

1. **Sin CRSP/WRDS**, no se puede afirmar equivalencia a una base institucional survivorship-bias-free canónica.
2. **Norgate reduce mucho el sesgo**, pero si el proveedor no garantiza completitud absoluta de delisted ETPs, la tesis debe declarar cobertura comercial validada, no perfección.
3. **SEC-only es oficial pero no suficiente por sí sola** para precios diarios y liquidating/delisting returns.
4. **N-PORT/N-CEN tienen rezagos de publicación**; todo dato de filings debe entrar al modelo solo desde `available_as_of`.
5. **Precios públicos ajustados no garantizan retorno total ETF completo**, especialmente en liquidaciones, cambios de ticker, mergers y distribuciones especiales.
6. El backtest 2015–2025 debe reportarse con un `data_quality_verdict` por experimento: `static_current_biased`, `public_approximate_pit` o `commercial_pit_validated_with_sec`.

## Reglas de implementación derivadas

1. Crear proveedor `constituents_as_of(rebalance_date)`; prohibido usar universo estático actual para evidencia de tesis.
2. Separar autoridad de universo de fuente de precios.
3. Exportar `universe_coverage_report.csv`, `membership_audit.csv`, `price_coverage_funnel.csv`, `delisting_events.csv` y `data_quality_verdict.json`.
4. Mantener benchmarks SPY y 60/40 fuera del filtro ELECTRE.
5. No hacer tuning de ELECTRE/MaxSharpe hasta tener al menos la ruta SEC-only auditable o aprobación de Norgate.

## Estado de Definition of Done

```text
source_primary: Norgate Data US Stocks Platinum + SEC EDGAR
source_secondary: SEC EDGAR-only + public adjusted prices

data_quality_verdict: primary commercial_pit_validated_with_sec after vendor validation; secondary public_approximate_pit
survivorship_bias_free: partial
pit_universe_supported: true/partial depending route; Norgate+SEC true after validation, SEC-only partial
total_return_supported: partial until ETF distribution/liquidation handling is validated
limitations: CRSP unavailable; Norgate delisted coverage not assumed perfect; SEC-only annual/filing lag; public prices incomplete for delisted/liquidation; no paid trials without approval
cost: Norgate observed USD 630/year or USD 346.50/6 months; SEC-only free; Polygon/Massive paid plans not selected
implementation_time: Norgate+SEC 7–14 days after approval; SEC-only 21–30 days; Polygon+SEC 10–20 days after validation
```

**GOAL 1 cerrado:** la ruta de datos queda decidida. Siguiente paso permitido: implementar la ruta SEC-only pública o solicitar aprobación explícita para Norgate. Siguiente paso no permitido todavía: tuning de modelo/performance.
