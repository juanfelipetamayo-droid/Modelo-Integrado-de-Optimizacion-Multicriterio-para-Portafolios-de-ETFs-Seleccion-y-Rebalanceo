## Context

El trabajo de grado aceptado (`docs/trabajo_de_grado.md`) establece que el proyecto debe desarrollar un modelo de optimización de portafolios ETF basado en análisis multicriterio, usando ELECTRE Tri para reducir el universo a 10-25 activos y luego validar el desempeño frente a benchmarks. La referencia metodológica principal (`docs/xidonas_electre_tri_latex_explicado.tex`) muestra que Xidonas et al. aplican ELECTRE Tri por clases sectoriales, con perfiles y criterios adecuados a cada clase, y validan consistencia temporal antes de interpretar resultados posteriores.

El proyecto ya cuenta con componentes relevantes: pipeline de selección/optimización, ELECTRE Tri, backtesting walk-forward, proveedores de universo point-in-time aproximado, benchmarks y diagnósticos. Sin embargo, los hallazgos consolidados en `findings.md` muestran brechas frente a los objetivos aceptados: criterios incompletos, falta de cardinalidad final 10-25, perfiles ELECTRE globales, validación 2021-2024/2025 no suficientemente aislada, y evidencia de que la configuración actual no generaliza bien a 2015-2025.

La decisión de diseño es alinear implementación y evidencia con la tesis aceptada, no reescribir los objetivos del trabajo de grado.

## Goals / Non-Goals

**Goals:**

- Establecer trazabilidad verificable entre objetivos aceptados, capacidades del sistema, experimentos y resultados.
- Completar la especificación de criterios ETF prometidos: rendimiento/CAGR, volatilidad, Sharpe Ratio, liquidez, tracking error y expense ratio.
- Adaptar Xidonas al contexto ETF mediante peer groups comparables, no mediante una única matriz global de perfiles.
- Garantizar que la etapa ELECTRE Tri produzca una selección final de 10-25 ETFs para el periodo de estudio.
- Mantener 2021-2024 como periodo de construcción/calibración y 2025 como validación OOS, usando 2015-2025 como prueba extendida de robustez.
- Separar explícitamente selección multicriterio, asignación de pesos, rebalanceo y evaluación.
- Reportar limitaciones de datos y universo de forma auditable.

**Non-Goals:**

- No cambiar el objetivo general ni los objetivos específicos aceptados en `docs/trabajo_de_grado.md`.
- No prometer que los resultados extendidos deben superar siempre a SPY o 60/40.
- No introducir una base de datos compleja como Postgres si DuckDB/Parquet/CSV auditables bastan para la tesis local.
- No tratar yfinance como autoridad de universo ETF.
- No ocultar resultados negativos o diagnósticos de no robustez.

## Decisions

### 1. `docs/trabajo_de_grado.md` será la fuente de verdad de objetivos

La implementación SHALL mapear cada resultado relevante a los objetivos de la tesis. La trazabilidad debe quedar visible en documentación y reportes, usando `findings.md` como registro de brechas iniciales.

**Alternativa considerada:** reescribir el framing de la tesis hacia una tesis puramente diagnóstica. Se descarta porque el documento ya fue aceptado; el objetivo ahora es cumplimiento, no reformulación.

### 2. ELECTRE Tri se aplicará por peer groups ETF

Para alinear con Xidonas, los ETFs no deben compararse todos contra perfiles globales. El sistema debe clasificar los ETFs en grupos comparables antes de aplicar perfiles, pesos y umbrales: por ejemplo, renta variable amplia, sectoriales, internacionales, renta fija, commodities, REITs/alternativos, temáticos y grupos especiales.

**Alternativa considerada:** mantener un único perfil global. Se descarta como ruta principal porque compara instrumentos heterogéneos y no reproduce la lógica sectorial de Xidonas.

### 3. Los seis criterios aceptados deben estar cubiertos o declarados como limitación

La ruta principal debe calcular o integrar CAGR, volatilidad, Sharpe, liquidez, tracking error y expense ratio. Si tracking error o expense ratio no están disponibles con datos completos, el sistema debe usar una fuente/proxy documentada o marcar la corrida como incompleta frente al objetivo general.

**Alternativa considerada:** continuar solo con OHLCV. Se permite para pilotos, pero no como cumplimiento completo del objetivo general.

### 4. La cardinalidad 10-25 será una regla explícita posterior a ELECTRE

La selección no termina al asignar categorías. Después de clasificar Excelentes/Aceptables/Rechazados, debe existir una etapa final que produzca entre 10 y 25 ETFs, resolviendo empates y déficits con reglas reproducibles.

**Alternativa considerada:** aceptar cualquier número de ETFs `above_preferred`. Se descarta porque no cumple el objetivo específico 1.

### 5. La validación se organizará en dos niveles temporales

El protocolo principal SHALL respetar la estructura aceptada: 2021-2024 como desarrollo/calibración y 2025 como OOS. La validación 2015-2025 SHALL usarse como robustez extendida y diagnóstico de sensibilidad, no como sustituto del periodo aceptado.

**Alternativa considerada:** reemplazar el estudio por 2015-2025. Se descarta porque desalinearía el trabajo aceptado.

### 6. La evidencia se reportará por capas

Cada experimento debe distinguir:

1. calidad de universo y datos;
2. calidad de clasificación ELECTRE;
3. selección final 10-25;
4. asignación de pesos;
5. rebalanceo;
6. evaluación frente a benchmarks.

Esto evita atribuir a ELECTRE fallos o mejoras que provienen de MaxSharpe, costos, universo o rebalanceo.

## Risks / Trade-offs

- **Tracking error y expense ratio pueden requerir fuentes no disponibles gratuitamente** → Mitigar con proxies explícitos, etiquetas de calidad y documentación de limitaciones.
- **Peer groups demasiado finos pueden sobreajustar** → Mitigar con taxonomía jerárquica y fallback a grupos superiores cuando haya pocos ETFs.
- **El rango 10-25 puede forzar inclusión de ETFs aceptables si hay pocos excelentes** → Mitigar con reglas de relleno documentadas y reporte de calidad de selección.
- **2025 OOS puede ser una muestra corta** → Mitigar manteniendo 2015-2025 como robustez extendida y subperiodos por régimen.
- **MaxSharpe puede dominar o deteriorar la selección** → Mitigar reportando asignadores simples como EqualWeight/InverseVol/MinVariance restringido junto a MaxSharpe.
- **Universo PIT aproximado no elimina todo sesgo de supervivencia** → Mitigar con etiquetas `public_approximate_pit`, coverage reports y advertencias de claim.

## Migration Plan

1. Crear trazabilidad objetivo→capacidad→evidencia con base en `docs/trabajo_de_grado.md` y `findings.md`.
2. Ajustar documentación metodológica y reportes para distinguir cumplimiento principal vs robustez extendida.
3. Completar criterios faltantes o etiquetar formalmente limitaciones.
4. Introducir taxonomía/peer groups ETF y perfiles ELECTRE por grupo.
5. Añadir regla final de selección 10-25 ETFs.
6. Ejecutar validación principal 2021-2024/2025 y validación extendida 2015-2025.
7. Actualizar reportes finales con cumplimiento de objetivos, brechas y límites.

Rollback: si alguna mejora de datos o clasificación no está lista, mantener la ruta actual como baseline documentado y etiquetarla como cumplimiento parcial, no como resultado final alineado.

## Open Questions

- ¿Qué fuente concreta se usará para expense ratio: SEC, proveedor comercial, dataset público o captura manual auditada?
- ¿Qué benchmark por peer group se usará para tracking error de ETFs que no tienen índice explícito disponible?
- ¿La regla final 10-25 priorizará solo Excelentes, o permitirá completar cupo con Aceptables de mayor score si hay menos de 10 Excelentes?
- ¿Leveraged/inverse ETFs quedan excluidos del análisis principal o en un peer group especial?
- ¿Cuál será la granularidad inicial de peer groups para evitar sobreajuste?
