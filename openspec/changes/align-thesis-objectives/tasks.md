## 1. Trazabilidad de objetivos y hallazgos

- [x] 1.1 Crear un artefacto de trazabilidad que copie el objetivo general y los tres objetivos específicos desde `docs/trabajo_de_grado.md` y los mapee a capacidades, archivos, experimentos y evidencia.
- [x] 1.2 Referenciar `openspec/changes/align-thesis-objectives/findings.md` desde la documentación metodológica o de trazabilidad creada para este cambio.
- [x] 1.3 Clasificar cada objetivo como `cumplido`, `parcial`, `en riesgo` o `no cumplido`, incluyendo evidencia y brechas pendientes.
- [x] 1.4 Documentar que 2021-2024/2025 es el protocolo principal aceptado y que 2015-2025 es validación extendida de robustez.

## 2. Universo ETF y calidad de datos

- [x] 2.1 Revisar la ruta actual de universo (`static_current`, `point_in_time`, `public_approximate_pit`) y documentar cuál es válida para evidencia principal de tesis.
- [x] 2.2 Asegurar que los reportes distingan fuente de universo y fuente de precios, especialmente cuando se use yfinance/OHLCV público.
- [x] 2.3 Generar o actualizar un reporte de cobertura con conteos requested, observed, priced, sufficient-history, liquid, eligible y final-selected.
- [x] 2.4 Incorporar en los reportes un data-quality verdict que indique si la corrida es piloto, public-approximate-PIT o thesis-aligned.
- [x] 2.5 Verificar que entradas, salidas, delistings, mergers, ticker changes o falta de historia se traten con reglas documentadas cuando los datos estén disponibles.

## 3. Criterios aceptados por la tesis

- [x] 3.1 Auditar la matriz de features actual y confirmar cobertura de CAGR, volatilidad, Sharpe Ratio y liquidez.
- [x] 3.2 Definir e implementar la ruta de tracking error por ETF contra benchmark del peer group o benchmark específico disponible.
- [x] 3.3 Definir e implementar la ruta de expense ratio mediante fuente real, proxy auditado o limitación explícita.
- [x] 3.4 Etiquetar cualquier criterio faltante con estado de cobertura y evitar que una corrida incompleta se presente como cumplimiento total del objetivo general.
- [x] 3.5 Actualizar pruebas o fixtures para validar que una corrida thesis-aligned incluye los seis criterios prometidos o reporta limitaciones.

## 4. Selección ELECTRE Tri alineada con Xidonas

- [x] 4.1 Definir una taxonomía inicial de peer groups ETF equivalente a las clases sectoriales de Xidonas para el contexto ETF.
- [x] 4.2 Asignar cada ETF elegible a un peer group antes de calcular perfiles ELECTRE.
- [x] 4.3 Implementar perfiles, pesos y umbrales ELECTRE por peer group, con fallback documentado a grupo padre o perfil global cuando haya pocos datos.
- [x] 4.4 Mapear las categorías internas de ELECTRE a `excelentes`, `aceptables` y `rechazados` en reportes de tesis.
- [x] 4.5 Agregar una regla final reproducible que reduzca la selección a 10-25 ETFs.
- [x] 4.6 Validar consistencia de clasificación antes de optimizar: monotonicidad forward por categoría, divergencia pesimista/optimista y estabilidad Jaccard.

## 5. Optimización, rebalanceo y validación

- [x] 5.1 Configurar una corrida principal que use 2021-2024 para desarrollo/calibración y 2025 como out-of-sample.
- [x] 5.2 Configurar una corrida extendida 2015-2025 como robustez y etiquetarla explícitamente como validación extendida.
- [x] 5.3 Separar en reportes selección, asignación, rebalanceo y evaluación para cada estrategia.
- [x] 5.4 Comparar ELECTRE con asignadores EqualWeight, InverseVol, MinVariance restringido y MaxSharpe, evitando atribuir efectos de asignación únicamente a ELECTRE.
- [x] 5.5 Incluir benchmarks SPY, 60/40, EqualWeight, MinVariance y same-universe EqualWeight alineados a las mismas fechas OOS.
- [x] 5.6 Reportar turnover y resultados netos de costos para cada estrategia.

## 6. Reportes finales y verificación

- [x] 6.1 Generar un reporte final de cumplimiento de objetivos aceptados con links a resultados, tablas y artefactos.
- [x] 6.2 Actualizar documentación para que los resultados piloto, principales y extendidos no se mezclen.
- [x] 6.3 Agregar pruebas unitarias para criterios, peer groups, cardinalidad 10-25 y data-quality verdict.
- [x] 6.4 Agregar pruebas/integración para una corrida pequeña thesis-aligned que produzca matriz de criterios, selección 10-25 y reporte de benchmarks.
- [x] 6.5 Ejecutar la suite relevante de tests y registrar comandos/resultados en la documentación de implementación.
