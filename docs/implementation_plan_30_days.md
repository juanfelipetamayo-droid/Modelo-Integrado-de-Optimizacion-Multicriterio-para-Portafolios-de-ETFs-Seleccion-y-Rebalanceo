# Plan de implementación de 30 días

Regla: no modificar el código hasta que este plan sea aprobado. Este plan asume trabajo posterior con TDD y trazabilidad.

## Semana 1 — decisión de datos y prototipo SEC-only

**Día 1–2**

- Congelar resultados actuales 2015–2025 como baseline negativo: CAGR 2.47%, Sharpe 0.247, MDD -24.01%, SPY 13.58%, 60/40 9.00%.
- Crear `data_source_decision_register.md` con decisión: no thesis-grade con universo actual.
- Confirmar con asesor si hay acceso a Morningstar/Bloomberg/LSEG/FactSet; no usar credenciales sin aprobación.

**Día 3–5**

- Descargar Series/Class SEC 2015–2025.
- Construir tabla maestra SEC con headers normalizados y conteos por año.
- Crear heurística ETF/ETP y muestreo manual de precisión/recall.

**Día 6–7**

- Diseñar `PointInTimeETFUniverseProvider.constituents_as_of(date)`.
- Exportar primer `universe_coverage_report.csv` sin backtest.

## Semana 2 — precios, cobertura y validación legal

- Enriquecer por `company_tickers_exchange.json` y EDGAR submissions.
- Identificar N-CEN/N-PORT por CIK/series con lag de filing.
- Descargar precios públicos para muestra 2015–2025; medir no solo tickers con precio sino miembros SEC elegibles sin precio.
- Exportar `price_coverage_funnel.csv`.
- Decidir si SEC-only alcanza cobertura mínima para tesis como aproximación pública.

## Semana 3 — Norgate decision gate o SEC-only backtest

Gate de presupuesto:

- Si usuario/asesor aprueba pago: comprar o solicitar prueba Norgate **solo después de aprobación explícita**; documentar paquete/licencia. Integrar Norgate como price/universe provider.
- Si no hay pago: seguir SEC-only y documentar limitaciones.

Tareas técnicas:

- Implementar modo `point_in_time_sec_public` con tests.
- Ejecutar smoke backtest pequeño 2018–2022.
- Verificar que no hay global coverage filter que excluya ETFs nacidos después del start.

## Semana 4 — backtest 2015–2025 y diagnóstico de performance

- Ejecutar 2015–2025 con PIT público/comercial.
- Exportar fold diagnostics, holdings attribution, category exposure, paired benchmark tests.
- Comparar tres universos: `static_current` vs `static_start` vs `point_in_time`.
- Preparar sección de tesis: si performance sigue <10%, reencuadrar contribución como pipeline reproducible que detecta falla de generalización y sesgos, no como estrategia superior.

## Criterios de éxito al día 30

- Hay un universe provider dinámico auditado.
- Se puede responder “qué ETFs eran elegibles en fecha X y por qué”.
- La tesis no depende de un universo current-active.
- Existe una corrida 2015–2025 con claim boundary correcto.
- La decisión Norgate vs SEC-only está justificada por cobertura/costo, no por intuición.
