# Entregables de sustentación — ETF ELECTRE Tri

Este directorio contiene los artefactos listos para presentación del trabajo de grado:

## Archivos principales

| Entregable | Ruta | Uso |
|---|---|---|
| Documento de tesis DOCX | `docs/deliverables/tesis_trabajo_grado_etf_electre.docx` | Documento formal ampliado con portada, resumen/abstract, objetivos, marco teórico, metodología, datos, implementación, diseño experimental, resultados, discusión, protocolo de auditoría, conclusiones, referencias y anexos. |
| Documento de tesis PDF | `docs/deliverables/tesis_trabajo_grado_etf_electre.pdf` | Render exacto desde LibreOffice para revisión y conteo real de páginas. |
| Presentación PPTX | `docs/deliverables/presentacion_sustentacion_etf_electre.pptx` | Slides para sustentación ejecutiva/académica. |
| Front estático | `docs/deliverables/front_presentacion/index.html` | Landing navegable con métricas clave y enlaces a artefactos. |
| Manifest | `docs/deliverables/deliverables_manifest.json` | Registro máquina de rutas, métricas y límites de claim. |

## Documento de tesis largo

El DOCX fue ampliado a un borrador formal fuerte. Validación programática actual:

```text
20,729 palabras incluyendo tablas
69 páginas exactas en PDF renderizado con LibreOffice 24.2.7.2
~69.1 páginas estimadas a 300 palabras/página
~75.4 páginas estimadas a 275 palabras/página
178 encabezados
6 tablas de contenido académico y 7 rótulos `Tabla N`
26 fórmulas con rótulo `Ecuación N` y nota metodológica
```

Incluye: portada, resumen, abstract, tabla de contenido manual, planteamiento del problema, objetivos, marco teórico, datos/sesgos, metodología, implementación, diseño experimental, resultados, discusión, protocolo de reproducibilidad, conclusiones, referencias y anexos.

## Candidato presentado

```text
results/sprint_universe_paper_quarterly_2015_2025_every_confirm2_m030_cap025/
```

Configuración:

```text
ELECTRE Tri pesimista
sin veto
rebalanceo trimestral
buy-and-hold drift
recategorización every_period
confirmación por 2 periodos
materialidad ELECTRE 0.30
category_exposure_cap 25%
costes 10 bps
```

## Métricas clave del candidato

| Métrica | Valor |
|---|---:|
| CAGR | 2.47% |
| Sharpe | 0.247 |
| Max Drawdown | -24.01% |
| Volatilidad | 13.61% |
| Turnover total | 4.02 |

## Límite de inferencia obligatorio

Estos artefactos son **presentables como investigación reproducible**, no como recomendación de inversión. La evidencia usa datos públicos y un universo activo/current snapshot; por tanto, no es survivorship-bias-free. La tesis debe afirmar que el pipeline detecta y mitiga el fallo de generalización del baseline, no que bate de forma concluyente a SPY o 60/40.

## Próximo paso de datos point-in-time

Se incorporó una matriz de fuentes en:

```text
docs/research/etf_point_in_time_data_sources.md
```

El siguiente paso ideal es usar una base institucional point-in-time como CRSP, Morningstar Direct, Lipper, Bloomberg o Refinitiv/LSEG, o construir snapshots históricos por año si se encuentra una fuente pública archivada suficientemente estable.

## Validación

Última validación ejecutada:

```bash
uv run ruff check .
uv run pytest -q
```

Resultado:

```text
All checks passed
142 passed
```
