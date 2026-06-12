# Última revisión exhaustiva: universo ETF histórico / point-in-time

Fecha: 2026-05-20

## Veredicto ejecutivo

Sí existe una ruta pública/no institucional que se acerca a lo que necesitamos, pero no es tan limpia como CRSP/Morningstar/Lipper/Bloomberg/Refinitiv.

La mejor fuente abierta encontrada para responder “¿qué ETFs existían en 2018?” es:

```text
SEC Investment Company Series and Class Information
```

La página pública de la SEC ofrece archivos CSV/XML anuales de series y clases de investment companies con `Series ID`, `Class ID`, `Class Ticker`, CIK y nombres. En la revisión se confirmó acceso a archivos anuales, incluyendo 2018:

```text
https://www.sec.gov/files/investment/data/other/investment-company-series-and-class-information/investment_company_series_class_2018.csv
```

Prueba observada sobre 2018:

```text
rows = 45,349
class_ticker_symbol non-null = 45,347
heurística ETF rows = 3,237
heurística ETF unique tickers = 2,269
```

Esto no es una base final tipo CRSP, pero es suficiente para construir un universo histórico abierto mucho más defendible que usar un snapshot Nasdaq 2026 para backtests desde 2018.

## Hallazgo principal para el proyecto

El universo actual `data/universe/etf_universe_clean.csv` es un snapshot activo/current de Nasdaq 2026. Para backtests desde 2018, eso introduce current-universe/survivorship bias.

La revisión encontró dos fuentes públicas útiles:

1. **SEC Investment Company Series/Class annual CSVs**, útiles para reconstruir membresía histórica aproximada por año desde al menos 2012.
2. **SEC Form N-PORT Data Sets / Jay Kahn N-PORT processed dataset**, útiles desde 2019 Q4 para series-level fund panel, assets y características de fondos registrados.

La combinación recomendada es:

```text
SEC Series/Class yearly snapshots → universo histórico de tickers por año
N-PORT 2019Q4+ → validación de existencia, assets y características por trimestre
Yahoo/Stooq/EODHD/etc. → precios, con límites explícitos
```

## Fuentes revisadas y clasificación

| Fuente | ¿Abierta? | ¿Sirve para universo 2018? | Utilidad real | Veredicto |
|---|---:|---:|---|---|
| SEC Investment Company Series/Class Information | Sí | Sí, archivo anual 2018 confirmado | Ticker, CIK, Series ID, Class ID, nombres; permite snapshots anuales | **Usar como base pública principal** |
| SEC Form N-PORT Data Sets | Sí | No para 2018; empieza 2019 Q4 | Filings trimestrales/mensuales de fondos registrados, holdings/assets | **Usar para 2019Q4+ y validación** |
| Jay Kahn processed N-PORT dataset | Sí | No para 2018; 2019Q4+ | CSV procesado, 243k+ filings, series-level panel | **Muy útil para acelerar N-PORT** |
| Nasdaq ETF Screener | Sí | No | Snapshot activo actual | Mantener solo como current baseline |
| StockAnalysis ETF list | Sí | No | Lista actual de ETFs | No suficiente para PIT |
| ETF.com closures | Parcial/web bloqueada | Parcial | Cierres ETF, útil para auditoría manual | Complemento, no base principal |
| ETF Reference / albertored ETFDB GitHub | Sí | No como PIT | Base estática global/current con metadata e inception | Complemento, no PIT |
| Stooq historical market data | Sí | Parcial | Precios gratuitos por símbolo; no universo PIT robusto | Complemento para precios |
| MasterDATA / MasterDATACSV | No plenamente abierto, comercial | Sí, potencialmente | Holdings/listas históricas desde 2009 según página | Bueno pero suscripción/licencia |
| EODHD delisted data | Freemium/comercial | Parcial | Datos de empresas delistadas, APIs de precios/fundamentals | Posible opción barata, validar ETF coverage |
| Norgate Data | Comercial | Parcial/depende de cobertura ETF | Survivorship-bias-free equities, Windows/proprietary | Bueno para acciones; validar ETF/ETP |
| QuantConnect ETF constituents universes | Freemium/plataforma | No para universo ETF total | Constituents de ETFs, no lista de ETFs vivos/muertos | No resuelve universe membership |
| OpenFIGI | Sí con límites | No | Mapping de identificadores, no universo histórico | Complemento de symbology |
| CRSP / WRDS | No, institucional | Sí | Ideal académico | Mejor opción si hay acceso |
| Morningstar Direct / Lipper / Bloomberg / Refinitiv/LSEG | No, institucional | Sí | Ideal comercial/institucional | Mejor opción con licencia |

## Detalle de fuentes públicas útiles

### 1. SEC Investment Company Series and Class Information

Página:

```text
https://www.sec.gov/data-research/sec-markets-data/investment-company-series-class-information
```

Archivos observados:

```text
investment_company_series_class_2012.csv
investment_company_series_class_2015.csv
investment_company_series_class_2018.csv
investment_company_series_class_2020.csv
investment-company-series-class-2025.csv
```

Columnas observadas en 2018:

```text
rep_file_num
CIK
entity_name
entity_org_type
series_id
series_name
class_id
class_name
class_ticker_symbol
street1
street2
city
state_code
zip
```

Ventajas:

- Fuente oficial SEC.
- Tiene tickers de clase y series/classes legales.
- Permite construir snapshots por año, incluyendo 2018.
- Reduce el error más grave: usar tickers actuales para años pasados.

Limitaciones:

- Incluye mutual funds, variable accounts y otros registered investment companies, no solo ETFs.
- Hay que filtrar ETFs con heurísticas y/o cruzar con nombres, tickers, N-PORT, exchange data y metadata externa.
- No cubre necesariamente ETNs, commodity pools u otros ETPs que no estén estructurados como registered investment companies.
- Es anual, no exacto al día de rebalanceo.
- No contiene precios.

Filtro inicial recomendado:

```text
contiene ETF / EXCHANGE TRADED / EXCHANGE-TRADED en entity_name, series_name o class_name
+ ticker no nulo
+ excluir money market, variable insurance, annuity, mutual-fund share classes obvias
+ cruzar contra precios disponibles en la fecha
```

### 2. SEC Form N-PORT Data Sets

Página:

```text
https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
```

Cobertura observada en la página:

```text
October 2019 - March 2026
```

Archivos trimestrales ZIP observados, por ejemplo:

```text
2019q4_nport.zip
2020q1_nport.zip
...
2026q1_nport.zip
```

Ventajas:

- Fuente oficial SEC.
- Filings de fondos registrados.
- Útil para validar existencia, assets, holdings y características por fecha.
- Mejor granularidad que snapshots anuales.

Limitaciones:

- No sirve para 2018 porque arranca en 2019 Q4.
- Descargas grandes, cientos de MB por trimestre.
- Requiere parsing robusto.
- No cubre todos los ETPs no registrados como investment companies.

### 3. Jay Kahn processed N-PORT dataset

Página:

```text
https://j-kahn.com/nport/
```

Archivo observado:

```text
https://j-kahn.com/files/bkms_nport_public.zip
```

Datos observados:

```text
Cobertura: 2019 Q4 to present
Filings procesados: 243,159+
ZIP: ~53.8 MB
CSV descomprimido: ~301 MB
Columnas: 193
```

Campos observados:

```text
seriesid
serieslei
seriesname
regname
regfilenumber
regcik
reppddate
totassets
totliabs
netassets
asset allocation shares
```

Ventajas:

- Mucho más fácil que parsear todos los XML N-PORT desde cero.
- Sirve para construir panel trimestral de fondos/ETFs desde 2019Q4.
- Fuente académica reutilizable con cita.

Limitaciones:

- No incluye ticker directo en las primeras columnas observadas.
- Hay que mapear `seriesid`/CIK a tickers usando SEC Series/Class.
- No cubre 2018.

## Lo que NO resuelve el problema por sí solo

### ETF closures lists

ETF.com y otras páginas de cierres ayudan a saber qué ETFs cerraron, pero no construyen un universo completo por fecha. Sirven como auditoría de fondos muertos, no como base principal.

### GitHub ETFDB / ETF Reference

El repositorio `albertored/etfdb` tiene CSVs actuales/globales con metadata como ticker, nombre, inception_date, TER, proveedor, holdings, etc. Es útil como complemento, pero no parece proveer snapshots históricos por año ni delisted coverage completo.

### Stooq / Yahoo Finance

Sirven para precios, no para saber qué debía existir en cada fecha. Pueden tener datos de algunos símbolos desaparecidos, pero no son universo PIT.

### EODHD / Norgate / MasterDATA

Son opciones prácticas si se acepta una fuente comercial más barata que Bloomberg/Morningstar. No son “abiertas” en sentido estricto. Deben validarse por cobertura ETF/ETN, licencia y capacidad de exportar delisted instruments.

## Plan recomendado para el código

### Fase 1, inmediata y pública

Implementar un proveedor SEC anual:

```text
SecSeriesClassAnnualUniverseProvider
```

Entrada:

```text
--universe-mode sec_annual_series_class
--universe-year 2018
```

Salida esperada:

```text
data/universe/sec_series_class/2018_universe_raw.csv
data/universe/sec_series_class/2018_etf_candidates.csv
data/universe/sec_series_class/2018_coverage_report.csv
```

Lógica:

1. Descargar CSV anual SEC.
2. Normalizar columnas entre formatos 2012/2015/2018/2020/2025.
3. Filtrar tickers no nulos.
4. Marcar candidatos ETF por heurística textual.
5. Enriquecer con precios disponibles.
6. Guardar snapshot con hash, URL y timestamp.

### Fase 2, 2019Q4+

Implementar proveedor N-PORT:

```text
SecNportUniverseProvider
```

Uso:

- validar series activas por trimestre;
- añadir net assets;
- mejorar filtros de tamaño/liquidez;
- detectar desaparición de series.

### Fase 3, point-in-time real

Si aparece acceso institucional:

```text
InstitutionalUniverseProvider
```

Adaptadores:

```text
CRSP/WRDS export
Morningstar Direct export
Lipper/LSEG export
Bloomberg/Refinitiv export
```

## Conclusión para el backtest desde 2018

La afirmación del usuario es correcta:

> De nada sirve un backtest desde 2018 si el universo viene de 2026.

Después de esta revisión, la mejor respuesta práctica es:

1. No usar Nasdaq 2026 como universo principal para 2018.
2. Construir el universo 2018 desde SEC `investment_company_series_class_2018.csv`.
3. Filtrar candidatos ETF por texto y mapping de tickers.
4. Descargar precios solo para esos candidatos.
5. Para 2019Q4 en adelante, complementar con N-PORT.
6. Mantener CRSP/Morningstar/Lipper/Bloomberg/Refinitiv como gold standard si se consigue acceso.

## Veredicto final

Hay algo aprovechable y abierto:

```text
SEC Series/Class annual snapshots + N-PORT desde 2019Q4
```

No es perfecto, pero es suficientemente importante como para cambiar el roadmap del proyecto. El siguiente paso técnico recomendado es implementar `SecSeriesClassAnnualUniverseProvider` y regenerar los backtests 2018+ con el universo SEC del año correspondiente, no con el snapshot Nasdaq 2026.
