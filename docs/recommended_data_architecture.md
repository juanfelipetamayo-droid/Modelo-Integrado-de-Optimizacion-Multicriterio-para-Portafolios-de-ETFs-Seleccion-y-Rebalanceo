# Arquitectura recomendada de datos PIT para ETFs 2015–2025

## Decisión de arquitectura

Implementar dos modos explícitos:

1. `point_in_time_sec_public` — gratuito e inmediato. Construye universo dinámico desde SEC Series/Class + EDGAR/N-CEN/N-PORT y usa precios públicos como capa separada.
2. `point_in_time_norgate_sec` — modo preferido si se aprueba Norgate. Usa Norgate para precios/volumen/activos+delisted y SEC para trazabilidad legal.

No volver a tratar `static_current` como evidencia de tesis; dejarlo como smoke test.

## Principios

- La membresía se decide en cada fecha de rebalanceo: `constituents_as_of(rebalance_date)`.
- Separar **universe authority** de **price source**.
- Aplicar lag de filing a N-CEN/N-PORT. La estrategia no puede usar datos antes de que fueran públicos.
- Exportar auditoría: tickers incluidos/excluidos, razones, cobertura de precios, fuente, fecha de observación, hash.
- Mantener benchmarks SPY y 60/40 como referencias fijas separadas, no como parte del filtro ELECTRE.

## Tablas mínimas

### `universe_master.parquet`

Campos:

- `ticker`, `canonical_ticker`, `security_name`, `issuer`
- `cik`, `series_id`, `class_id`, `reporting_file_number`
- `instrument_type` (`ETF`, `ETN`, `ETMF`, `unknown_etp`)
- `exchange`, `first_seen_date`, `last_seen_date`
- `inception_date`, `termination_date`, `delisted_utc`, `merger_liquidation_flag`
- `source`, `source_url`, `source_year`, `source_filing_accession`
- `is_etf_candidate`, `etf_confidence`, `exclusion_reason`

### `universe_membership_by_rebalance.csv`

Campos:

- `rebalance_date`, `ticker`, `membership_status`
- `source`, `available_as_of`, `age_months`
- `price_coverage_pct`, `avg_dollar_volume`, `eligible_for_electre`
- `eligibility_reason`

### `price_panel.parquet`

Campos diarios por ticker:

- `open`, `high`, `low`, `close`, `adjusted_close`, `volume`
- `dividend`, `split_factor`, `total_return_close` si disponible
- `source`, `source_timestamp`, `adjustment_policy`

### `filing_lag_register.csv`

- `cik`, `series_id`, `class_id`, `form_type`, `period_end`, `filing_date`, `available_as_of`, `url`, `accession`

## Flujo SEC-only

1. Descargar Series/Class CSV anuales 2015–2025 desde SEC.
2. Normalizar headers variables: `CIK`, `Series ID`, `Class ID`, `Class Ticker`.
3. Clasificar candidatos ETF/ETP por nombre: `ETF`, `EXCHANGE TRADED`, `SPDR`, `ISHARES`, `VANGUARD`, `INVESCO`, etc.; excluir mutual funds, money market, variable annuities cuando aplique.
4. Enriquecer por EDGAR submissions/N-CEN/N-PORT.
5. Para cada rebalance, construir membresía por fechas observables.
6. Descargar/preparar precios solo para miembros elegibles, pero registrar missingness y no reemplazar membresía por disponibilidad de precio.
7. Ejecutar backtest con etiqueta `public_approximate_pit`, no `institutional_thesis_grade`.

## Flujo Norgate+SEC

1. Confirmar y documentar licencia/paquete Norgate antes de pagar: US Stocks Platinum, ETF/ETN delisted, ajustes, Python.
2. Exportar universo Norgate activo+delisted y precios 2015–2025.
3. Mapear tickers Norgate a SEC (`cik`, `series_id`, `class_id`) cuando exista; para ETNs no registrados como investment companies, marcar fuente Norgate-only.
4. Usar SEC N-CEN/N-PORT como validación y evidencia legal, no como única fuente de precio.
5. Ejecutar backtest con claim `commercial_pit_data_validated_with_sec` si la cobertura supera umbrales.

## Umbrales de aceptación

- Cobertura de precios por fold: >= 80% de miembros elegibles o reportar fold no confiable.
- Mínimo age filter: 12 meses desde `max(first_seen_date, inception_date)`.
- No usar ETFs cuyo `first_seen_date` sea posterior al rebalance.
- Remover/liquidar instrumentos después de `last_seen_date`, `termination_date` o `delisted_utc`.
- Registrar delisting/termination event; si no hay retorno de liquidación, imputación conservadora documentada o exclusión con sensibilidad.

## Entregables técnicos esperados

- `data_quality_verdict.json`: `public_approximate_pit` o `commercial_pit_validated`.
- `universe_coverage_report.csv`: conteos por año/fuente/cobertura.
- `membership_audit.csv`: miembros por fecha.
- `excluded_tickers.csv`: razón de exclusión.
- `price_coverage_funnel.csv`: de candidatos SEC/Norgate a precios usables.
- `delisting_events.csv`: salida/liquidación/merger.
