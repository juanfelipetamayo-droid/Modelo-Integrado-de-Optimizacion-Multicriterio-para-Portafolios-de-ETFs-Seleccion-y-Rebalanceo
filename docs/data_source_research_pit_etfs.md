# Investigación de fuentes point-in-time para ETFs/ETNs 2015–2025

Fecha: 2026-06-09

## Decisión ejecutiva

**Recomendación final: Norgate + SEC como ruta preferida si se aprueba presupuesto; SEC-only como ruta inmediata sin pago.**

Motivo: para una tesis cuantitativa, el bloqueo principal no es conseguir precios históricos de ETFs vivos, sino reconstruir un universo invertible por fecha que incluya instrumentos desaparecidos y que no use información futura. CRSP/WRDS fue negado. Entre las alternativas revisadas, **Norgate US Stocks Platinum** es la opción comercial más implementable y relativamente barata: documenta ETPs/ETFs/ETNs dentro del paquete US Stock Market, delisted securities, precios ajustados, soporte Python y costo publicado. **SEC EDGAR** debe seguir como capa legal/oficial para series/class/CIK, N-CEN/N-PORT y trazabilidad académica. Polygon/Massive es útil como API moderna, pero para esta tesis queda por debajo de Norgate porque su ticker endpoint PIT y `delisted_utc` no prueban por sí solos retornos totales/delisting returns académicamente completos para ETFs; además el costo recurrente no queda claramente mejor que Norgate para el problema específico.

Ruta de trabajo:

1. **Sin pagar ahora:** construir `SEC-only + Yahoo/Stooq/Tiingo-free` como aproximación pública point-in-time, declarar limitaciones y medir cobertura.
2. **Con aprobación de pago:** comprar/contratar **Norgate US Stocks Platinum 12 meses** o solicitar trial solo después de autorización; usarlo para precios/volumen/listed+delisted y cruzarlo con SEC.
3. **No usar** Nasdaq current, Yahoo/yfinance, ETFdb/VettaFi o Kaggle como fuente principal de universo histórico. Son complementos o controles.

## Evidencia primaria revisada

### Norgate Data

Fuentes primarias:

- Paquetes de acciones: https://norgatedata.com/stockmarketpackages.php
- Contenido de datos: https://norgatedata.com/data-content-tables.php
- Precios: https://norgatedata.com/prices.php
- FAQ/licencia/API: https://norgatedata.com/faq.php

Hallazgos relevantes:

- El paquete **US Stock Market** declara cobertura de major-exchange-listed securities y separa categorías de instrumentos; dentro de Exchange Traded Products lista **Exchange Traded Funds, Exchange Traded Notes, Exchange Traded Managed Funds**.
- Los **delisted securities** están incluidos con suscripción US Stock Market **Platinum o Diamond**; la página explica que un security es delisted si negoció en una bolsa principal y ya no es negociable, con sufijo de año/mes de último trading.
- La comparación de paquetes indica para US Stocks: Platinum con historia diaria hasta 1990, delisted securities hasta 1990, fundamentos actuales, extras e historical index constituents; precio publicado **USD 630 por 12 meses** y **USD 346.50 por 6 meses**. Diamond llega a 1950 y cuesta **USD 787.50 por 12 meses**.
- Tiene documentación de **Python Package**. La FAQ dice que no existe “generic API” para aplicaciones propias, pero sí paquetes/plug-ins soportados; para tesis local Python es suficiente si el paquete expone la base Norgate.
- Free trial: la FAQ dice que entrega los últimos 2 años, insuficiente para 2015–2025 y no debe iniciarse sin aprobación del usuario.

Evaluación: **mejor balance tesis/costo/implementación** si el presupuesto de USD 630 se aprueba. Riesgo: confirmar antes de comprar que los ETFs/ETNs delisted tienen todos los campos necesarios para total return/adjusted close y acciones corporativas; Norgate habla de adjusted/dividends y delisted, pero la tesis debe registrar la prueba de cobertura real.

### Massive / Polygon

Fuentes primarias:

- All tickers: https://polygon.io/docs/rest/stocks/tickers/all-tickers
- Aggregates/custom bars: https://polygon.io/docs/rest/stocks/aggregates/custom-bars
- Pricing: https://polygon.io/pricing
- Corporate actions en docs de navegación: dividends/splits bajo REST stocks corporate actions.

Hallazgos relevantes:

- Endpoint de tickers permite filtros como `date`, `active`, `type`, `market`, `exchange` y devuelve campos como `active`, `delisted_utc`, `last_updated_utc`, `ticker`, `name`, `locale`, `market`.
- Los agregados tienen parámetro `adjusted`; los docs enlazan corporate actions de dividends/splits.
- Pricing observado en página pública: Stocks Basic free, Stocks Starter **USD 29/mes**, Developer **USD 79/mes**, Advanced **USD 199/mes**.

Evaluación: técnicamente atractivo para un pipeline API-first. Sin embargo, para 2015–2025 thesis-grade ETF PIT queda una duda académica: el ticker master con `active=false`/`delisted_utc` no equivale automáticamente a una base survivorship-bias-free de ETFs con retorno total y eventos de liquidación/merger/delisting. Además, “adjusted aggregates” resuelve split adjustments, no necesariamente total return completo por dividendos/distribuciones de ETFs. Requiere validación empírica antes de ser ruta principal.

### SEC EDGAR: data.sec.gov, Series/Class, N-CEN, N-PORT

Fuentes primarias:

- EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- `company_tickers_exchange.json`: https://www.sec.gov/files/company_tickers_exchange.json
- Series/Class annual CSV ejemplo 2015: https://www.sec.gov/files/investment/data/other/investment-company-series-and-class-information/investment_company_series_class_2015.csv
- Form N-PORT data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- Form N-CEN data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets

Hallazgos relevantes:

- `company_tickers_exchange.json` publica campos `cik`, `name`, `ticker`, `exchange`.
- Series/Class annual CSV publica `Reporting File Number`, `CIK`, registrant name, `Series ID`, `Series Name`, `Class ID`, `Class Name`, `Class Ticker`. Esto permite aproximar existencia legal de clases por año desde 2015.
- EDGAR submissions por CIK y filings N-CEN/N-PORT permiten validar existencia, series/class, tickers y reporting. N-PORT es útil desde la implementación moderna 2019Q4+ para holdings/activos y retornos mensuales reportados con lag; N-CEN ayuda para estado/terminación/estructura anual.

Evaluación: fuente **oficial, gratuita y citable**, pero no es una base de precios lista. No cubre perfectamente ETNs ni ETPs fuera de registered investment companies. Debe usarse con lag de filing y reporte de cobertura. Es defendible como aproximación pública, no como CRSP-grade.

### Nasdaq Trader Symbol Directory

Fuentes primarias:

- Definiciones Symbol Directory: https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs
- `otherlisted.txt`: https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt

Hallazgos relevantes:

- `otherlisted.txt` contiene columnas `ACT Symbol`, `Security Name`, `Exchange`, `CQS Symbol`, `ETF`, `Round Lot Size`, `Test Issue`, `NASDAQ Symbol`.
- Provee flag ETF actual diario, pero no histórico completo ni delisted histórico para 2015–2025.

Evaluación: útil para snapshots diarios propios desde ahora y validación de ticker/exchange actuales. No soluciona el bloqueador retroactivo.

### Tiingo

Fuentes primarias:

- EOD docs: https://api.tiingo.com/documentation/end-of-day
- Pricing: https://www.tiingo.com/pricing

Evaluación: API de precios ajustados EOD práctica; no debe usarse como autoridad de universo ETF PIT/delisted salvo que se contrate/confirme cobertura específica. Útil como capa de precios secundaria para tickers vivos y controles de calidad.

### EODHD

Fuentes primarias:

- Historical EOD API: https://eodhd.com/financial-apis/api-for-historical-data-and-volumes/
- Pricing: https://eodhd.com/pricing

Evaluación: buena API de precios/volúmenes y tiene planes comerciales; debe verificarse si el plan incluye delisted US ETFs y corporate-action/adjusted close suficientes. No queda como primera opción porque hay más incertidumbre académica que Norgate para delisted ETF coverage.

### Kibot

Fuente primaria:

- Historical data purchase: https://www.kibot.com/buy.aspx

Evaluación: vende datos históricos de stocks/ETFs, incluidos intradía. Más orientado a datos de trading que a universo PIT académico. No queda como ruta principal salvo compra específica y verificación de delisted/adjusted total return.

### Stooq

Fuente primaria:

- Historical data: https://stooq.com/db/h/

Evaluación: fuente pública útil para precios EOD de muchos instrumentos, pero no provee universo ETF PIT ni cobertura delisted confiable. Complemento de precios, no solución de data universe.

### Yahoo / yfinance

Fuente primaria/API pública observada:

- Yahoo Finance chart/download endpoints requieren cookies/crumb o login en algunos casos; ejemplo directo de descarga devolvió 401 sin sesión: `https://query1.finance.yahoo.com/v7/finance/download/SPY?...`.

Evaluación: excelente para prototipo y smoke tests, pero no oficial, no PIT, no delisted completo y licenciamiento/estabilidad problemáticos para tesis. Mantener solo como piloto o fallback de precios.

### ETFdb/VettaFi, Morningstar, Bloomberg, LSEG/Lipper, FactSet académico

Evaluación:

- ETFdb/VettaFi: buenos metadatos/categorías actuales, no base PIT completa gratuita.
- Morningstar Direct, Bloomberg, LSEG/Lipper/Refinitiv, FactSet: alternativas institucionales fuertes si la universidad tiene licencia. No iniciar contacto/uso con credenciales sin aprobación. Si el asesor puede conseguir acceso académico, estas superan la ruta SEC-only y pueden competir con Norgate.

### GitHub/Kaggle/Zenodo/OSF/Reddit/foros

Uso permitido: solo como pistas para repositorios de N-PORT procesado, listas históricas o parsers EDGAR. No deben ser evidencia final ni fuente principal. Cualquier dataset encontrado debe validarse contra SEC/Nasdaq/Norgate y revisar licencia.

## Ranking final de rutas

1. **Norgate + SEC**: recomendada si hay presupuesto. Costo bajo/moderado, mejor cobertura delisted y menor riesgo técnico.
2. **SEC-only + precios públicos**: recomendada inmediatamente sin pago para no bloquear tesis. Académicamente honesta como “aproximación pública PIT”.
3. **Polygon + SEC**: alternativa si se prefiere API y se acepta validar delisted/total return; no la elijo como principal.
4. **Institutional Morningstar/Bloomberg/LSEG/FactSet + SEC**: ideal si aparece acceso académico sin costo directo, pero no implementable hoy.
5. **Yahoo/Stooq/Tiingo/EODHD/Nasdaq current/Kaggle**: complementos, no ruta final de universe bias.
