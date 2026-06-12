## Why

Las corridas thesis-aligned actuales muestran que el proyecto ya tiene trazabilidad metodológica, pero no cumple completamente los objetivos aceptados por brechas de datos: el universo sigue clasificado como `public_point_in_time_pilot`, faltan criterios ETF reales o auditados como _tracking error_ y _expense ratio_, y la validación frente a benchmarks no debe prometer superioridad ex ante.

Este cambio propone construir una capa pública/regulatoria enriquecida para el universo de ETFs y ajustar la formulación del objetivo específico 3 hacia una validación empírica realista, de modo que el proyecto pueda corroborar cumplimiento casi completo sin ocultar límites metodológicos.

## What Changes

- Crear una capacidad de universo ETF regulatorio enriquecido para el protocolo principal 2021-2024/2025 usando fuentes públicas auditables: SEC N-PORT, SEC N-CEN, EDGAR submissions, OpenFIGI, metadatos de emisores y precios públicos.
- Definir controles point-in-time aproximados basados en `as_of_date`, `filed_date`, `accepted_datetime`, `public_available_date` y `decision_date` para reducir _lookahead bias_.
- Definir una arquitectura conceptual de datos con `security_master`, `filing_index`, `fund_snapshot`, `holdings_snapshot`, `benchmark_map`, `price_history`, `electre_features_pit` y `quality_flags`.
- Definir una matriz completa objetivo/criterio → fuente → campo → confiabilidad → fallback para rendimiento, volatilidad, Sharpe Ratio, liquidez, _tracking error_, _expense ratio_, AUM/net assets, antigüedad, benchmark, categoría y eventos de cierre/inicio.
- Exigir que la selección final usada para el objetivo específico 1 mantenga entre 10 y 25 ETFs por rebalanceo en el protocolo principal.
- Cambiar la formulación operativa del objetivo específico 3 para que no presuponga que el enfoque multicriterio siempre genera mejores resultados, sino que desarrolle la optimización y evalúe empíricamente su desempeño ajustado por riesgo frente a estrategias tradicionales.
- Mantener 2015-2025 como validación extendida/de robustez con degradación de claims documentada, no como sustituto del protocolo principal aceptado.
- No introducir cambios de implementación todavía; este cambio define el contrato verificable para una implementación posterior.

Propuesta de objetivo específico 3 reformulado:

> **Objetivo específico número tres:** Desarrollar e implementar un modelo de optimización de portafolios que busque mejorar la rentabilidad ajustada por riesgo y controlar la exposición al riesgo, con el propósito de construir portafolios eficientes y evaluar empíricamente si el enfoque multicriterio ofrece ventajas frente a estrategias de inversión tradicionales.

## Capabilities

### New Capabilities

- `regulatory-etf-universe`: Construcción, trazabilidad y control de calidad de un universo ETF público/regulatorio enriquecido con controles point-in-time aproximados.
- `thesis-objective-validation`: Reglas verificables para corroborar cumplimiento de objetivos de tesis, incluyendo la reformulación realista del objetivo específico 3 y la matriz objetivo/criterio/fuente.

### Modified Capabilities

No hay specs base archivadas en `openspec/specs/`; por tanto, este cambio introduce capacidades nuevas en lugar de modificar specs existentes.

## Impact

- Afectará conceptualmente la capa de datos del proyecto: proveedores de universo invertible, ingestión de metadatos ETF, normalización de identificadores, cálculo de features ELECTRE y verdicts de calidad.
- Afectará la configuración y ejecución de corridas thesis-aligned: el protocolo principal 2021-2024/2025 deberá usar datos disponibles a cada fecha de decisión, criterios ETF completos o fallbacks etiquetados, y selección final de 10-25 ETFs por rebalanceo.
- Afectará reportes metodológicos y de trazabilidad: deberán distinguir claims permitidos, claims no permitidos, limitaciones de fuentes públicas y diferencias entre validación principal y extendida.
- No requiere dependencias pagas ni vendors institucionales; cualquier fuente comercial o scraping no oficial solo podrá usarse como fallback documentado y con restricciones explícitas.
