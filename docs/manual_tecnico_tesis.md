# Manual técnico del sistema ETF Optimizer

## Arquitectura general

El sistema se organiza como un pipeline analítico compuesto por preparación de datos, cálculo de criterios financieros, clasificación multicriterio, optimización de portafolios, backtesting y generación de reportes. La implementación principal se encuentra bajo `src/etf_optimizer` y los experimentos reproducibles bajo `scripts`.

## Módulos principales

| Módulo o archivo | Responsabilidad |
|---|---|
| `src/etf_optimizer/features.py` | Cálculo de indicadores financieros como CAGR, volatilidad, Sharpe, liquidez y criterios adicionales cuando hay datos disponibles. |
| `src/etf_optimizer/selection/electre_tri.py` | Implementación de clasificación multicriterio ELECTRE Tri. |
| `src/etf_optimizer/pipeline.py` | Integración de selección, optimización, rebalanceo y validación. |
| `src/etf_optimizer/thesis_alignment.py` | Utilidades de alineación con objetivos de tesis, criterios y cardinalidad. |
| `src/etf_optimizer/thesis_validation.py` | Registro de objetivos y generación de reportes de cumplimiento. |
| `src/etf_optimizer/data/regulatory_universe.py` | Arquitectura para universo regulatorio enriquecido y controles point-in-time. |
| `scripts/run_sprint_experiment.py` | Runner empírico utilizado para los experimentos principales. |
| `scripts/build_thesis_compliance_artifacts.py` | Generación de artefactos de cumplimiento de objetivos. |
| `scripts/build_thesis_result_figures.py` | Generación de figuras finales para el documento. |

## Estructura de datos

Los datos históricos se manejan principalmente en formato Parquet. Los paneles utilizados por el runner se ubican en:

- `data/universe_master/derived_panels/close.parquet`
- `data/universe_master/derived_panels/volume.parquet`

Los resultados experimentales se almacenan en:

- `results/thesis_primary_2021_2025_run_no_cap`
- `results/thesis_extended_2015_2025_run_no_cap`

## Validación técnica

La validación técnica mínima consiste en ejecutar la suite de pruebas y regenerar las figuras del documento:

```bash
uv run pytest
uv run python scripts/build_thesis_result_figures.py
```

## Decisiones técnicas relevantes

- ELECTRE Tri se usa como método de clasificación, no como optimizador de pesos.
- La asignación de capital se ejecuta después de la selección multicriterio.
- La validación principal separa desarrollo/calibración 2021-2024 y evaluación out-of-sample 2025.
- La validación extendida 2015-2025 se usa como robustez, no como reemplazo del protocolo aceptado.
- El universo `public_approximate_pit` reduce ciertos sesgos frente a un universo estático, pero no constituye evidencia institucional completamente libre de survivorship bias.

## Limitaciones técnicas documentadas

- Las corridas finales no incorporan tracking error y expense ratio como criterios reales completos.
- La cardinalidad por rebalanceo no garantiza todavía el rango de 10 a 25 ETFs.
- La restricción de exposición por categoría con cap de 25% resultó inviable en una corrida experimental y requiere manejo explícito de factibilidad.
- Los resultados no validan superioridad robusta frente a SPY ni frente al portafolio 60/40.

## Reproducibilidad

Todos los comandos principales se ejecutan desde la raíz del repositorio. Para conservar reproducibilidad, cualquier nueva corrida debe registrar fecha, parámetros, ruta de salida y diferencias frente a la configuración documentada.
