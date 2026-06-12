# Fuentes para universo ETF point-in-time y control de survivorship bias

Fecha de incorporación: 2026-05-20

## Estado actual del proyecto

El universo actual del proyecto se construye desde el screener público de Nasdaq:

- URL: `https://api.nasdaq.com/api/screener/etf?download=true`
- Archivo local: `data/universe/etf_universe_clean.csv`
- Snapshot local observado: `2026-05-18 19:40:41`
- Tamaño observado: `4554` instrumentos
- Fuente en CSV: `source = nasdaq`
- Naturaleza: universo activo/current, no point-in-time, no survivorship-bias-free.

Los precios se descargan con Yahoo Finance/yfinance para ventanas históricas, por ejemplo `2015-2025` o `2020-2024`, pero los tickers vienen de un universo actual. Por tanto, la validación histórica arrastra current-universe bias.

## Siguiente paso ideal

El siguiente paso ideal es usar una base institucional point-in-time como CRSP, Morningstar, Lipper, Bloomberg o Refinitiv/LSEG, o construir snapshots históricos por año si se encuentra una fuente pública archivada suficientemente estable.

La última revisión exhaustiva encontró una ruta pública especialmente útil para 2018: SEC Investment Company Series/Class annual CSVs. El archivo SEC 2018 contiene tickers de clases (`class_ticker_symbol`) y permite construir un universo histórico anual aproximado. Ver detalle en `docs/research/etf_historical_universe_last_review.md`.

## Matriz de fuentes candidatas

| Fuente | Tipo | ¿Abierta? | ¿Point-in-time? | Uso recomendado | Limitación principal |
|---|---|---:|---:|---|---|
| CRSP Survivor-Bias-Free US Mutual Fund Database vía WRDS | Institucional académica | No, requiere suscripción/licencia institucional | Sí, diseñada para reducir survivorship bias | Fuente preferida si la universidad tiene WRDS/CRSP. Validar cobertura específica de ETFs y fondos liquidados/fusionados | Acceso licenciado, no redistribuible |
| Morningstar Direct | Institucional comercial | No | Sí, según licencia/módulos contratados | Universo ETF/fondos, categorías, gastos, AUM, holdings, fondos muertos | Coste alto, licencia restrictiva |
| Lipper / LSEG | Institucional comercial | No | Sí, según producto | Universo de fondos/ETFs, clasificación, performance y referencia histórica | Coste alto, requiere contrato |
| Bloomberg Terminal / Bloomberg Data License | Institucional comercial | No | Sí, según campos/licencia | ETF reference data, históricos, holdings, fundamentals y validación cruzada | Coste alto, extracción limitada por licencia |
| Refinitiv/LSEG Workspace, Datastream o DataScope | Institucional comercial | No | Sí, según producto | Series históricas, reference data, mapping e instrumentos activos/inactivos | Coste alto, requiere contrato |
| SEC EDGAR Form N-PORT | Pública oficial | Sí | Parcial, por filings | Reconstruir holdings mensuales y evidencia de existencia de fondos registrados desde filings | No es universo ETF completo listo para backtest; cobertura desde N-PORT moderno, retrasos y ETNs pueden quedar fuera |
| SEC Investment Company Series/Class Information | Pública oficial | Sí | Parcial | Identificadores legales de series y clases para registered investment companies | No sustituye una base de retornos ni asegura universo ETF point-in-time completo |
| Nasdaq ETF Screener | Pública | Sí | No, snapshot actual | Fuente práctica para universo activo actual y snapshots futuros propios | No histórico, no fondos cerrados/liquidados |
| Yahoo Finance/yfinance | Pública/no oficial | Sí | No para universo | Precios históricos piloto | No garantiza universo, corporate actions perfectos ni fondos desaparecidos |
| OpenFIGI | Pública/API | Sí con límites | No como universo | Normalización de identificadores FIGI, ticker, exchange | No es base histórica de ETFs ni performance |
| Internet Archive / snapshots web | Pública no estructurada | Sí | Parcial y frágil | Recuperar snapshots anuales si existen capturas de Nasdaq/ETF.com/issuer pages | Cobertura irregular, parsing frágil, trazabilidad discutible |

## Recomendación por niveles

### Nivel A, tesis fuerte

1. Solicitar acceso institucional a WRDS/CRSP, Morningstar Direct, Lipper/LSEG, Bloomberg o Refinitiv/LSEG.
2. Extraer universo ETF/fund point-in-time por fecha de rebalanceo.
3. Incluir fondos muertos, liquidados, fusionados y cambios de ticker.
4. Repetir los backtests 2015-2025 usando solo instrumentos disponibles en cada fecha.
5. Documentar licencia, fecha de extracción, campos, filtros y cobertura.

### Nivel B, alternativa pública defendible

1. Mantener el Nasdaq current snapshot solo como baseline piloto.
2. Construir un pipeline SEC EDGAR:
   - descargar los CSV anuales de Investment Company Series/Class, por ejemplo `investment_company_series_class_2018.csv`;
   - normalizar `Series ID`, `Class ID`, `Class Ticker`, CIK y nombres;
   - filtrar candidatos ETF por heurísticas textuales y validación cruzada;
   - consultar submissions por CIK;
   - detectar filings N-PORT/N-CEN relevantes;
   - guardar snapshots por fecha de filing y reporting period.
3. Cruzar tickers con Yahoo Finance/yfinance o Stooq para precios.
4. Marcar explícitamente huecos: ETNs, fondos no registrados como investment companies, cambios de ticker y fondos sin datos.
5. Validar manualmente una muestra contra issuer pages o factsheets archivados.

### Nivel C, desde ahora hacia adelante

1. No sobrescribir `data/universe/etf_universe_clean.csv` como única verdad.
2. Guardar snapshots fechados:
   - `data/universe/snapshots/YYYY-MM-DD/etf_universe_clean.csv`
   - `data/universe/snapshots/YYYY-MM-DD/metadata.json`
3. Persistir `dataAsOf`, URL, timestamp UTC, hash SHA256, conteo de tickers y parámetros.
4. Para backtests futuros, seleccionar el snapshot disponible más cercano pero anterior a cada fecha de rebalanceo.

## Cambio metodológico recomendado para el código

Agregar un modo de universo:

```text
--universe-mode current_snapshot | archived_snapshot | institutional_point_in_time
```

Y una interfaz de proveedor:

```python
class UniverseProvider:
    def constituents_as_of(self, date: pd.Timestamp) -> pd.DataFrame:
        ...
```

Implementaciones sugeridas:

- `NasdaqCurrentUniverseProvider`, estado actual, solo piloto.
- `ArchivedSnapshotUniverseProvider`, usa snapshots propios por fecha.
- `SecSeriesClassAnnualUniverseProvider`, reconstrucción pública anual con SEC Series/Class.
- `SecNportUniverseProvider`, validación trimestral 2019Q4+ con N-PORT.
- `InstitutionalUniverseProvider`, adaptador para CRSP/Morningstar/Lipper/Bloomberg/Refinitiv exportado a CSV/Parquet.

## Claim académico permitido

Con datos actuales:

> Los resultados son evidencia piloto con universo activo/current y no deben interpretarse como libres de survivorship bias.

Con una fuente institucional point-in-time:

> El backtest puede evaluarse sobre el universo disponible en cada fecha de decisión, incluyendo fondos desaparecidos cuando la licencia lo permita.

Con snapshots públicos reconstruidos:

> El backtest reduce current-universe bias, pero mantiene limitaciones por cobertura irregular y debe reportar tasa de recuperación por año.
