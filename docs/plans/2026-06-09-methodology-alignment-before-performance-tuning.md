# Plan inmediato: alineación metodológica antes de tunear performance

Fecha: 2026-06-09

## Decisión

Pausar tuning de performance. El modelo actual no debe seguir optimizándose hasta separar tres preguntas:

1. ¿El sorting multicriterio está implementado de forma fiel y defendible?
2. ¿La asignación de pesos posterior está destruyendo o mejorando la selección?
3. ¿El universo/datos permiten una inferencia histórica válida?

## Orden correcto de trabajo

### Fase 0 — congelar evidencia actual

- Mantener baseline negativo 2015–2025: CAGR 2.47%, Sharpe 0.247, MDD -24.01% en la configuración cap/confirmación reportada por el usuario.
- Mantener también la corrida previa `sprint_universe_paper_quarterly_2015_2025_oos` con CAGR -1.08%, Sharpe 0.011, MDD -43.55% como evidencia de configuración paper-style más frágil.
- No ocultar ninguna de las dos.

### Fase 1 — matriz paper → código

Crear `docs/research/paper_to_code_gap_matrix.csv` con filas como:

- ELECTRE categories;
- pessimistic/optimistic assignment;
- veto/no-veto;
- profiles;
- thresholds;
- weights;
- criteria;
- FlowSort;
- classification validation;
- allocation separation;
- temporal stability;
- data/universe.

### Fase 2 — ablations con código existente

Antes de implementar FlowSort o nuevos criterios, correr ablations con el código actual:

| Experimento | Objetivo |
|---|---|
| ELECTRE + equal-weight | Ver si MaxSharpe es la causa del fallo |
| ELECTRE + min-variance | Ver si selección funciona pero pesos agresivos fallan |
| MaxSharpe sin ELECTRE | Separar valor de selección vs optimizer |
| EqualWeight universo elegible | Baseline simple |
| Pesimista con veto vs sin veto | Confirmar recomendación de Emamat |
| Optimista con/sin veto | Medir divergencia/incomparabilidad |
| Overlap pesimista ∩ optimista | Replicar espíritu Xidonas |

### Fase 3 — diagnósticos paper-style

Agregar artefactos, no optimización:

- `classification_effectiveness.csv`: índice tipo `F` por fold.
- `category_forward_returns.csv`: retorno futuro por categoría.
- `pessimistic_optimistic_divergence.csv`: activos con asignaciones incompatibles.
- `category_stability.csv`: persistencia temporal.
- `selection_jaccard_by_fold.csv`.

### Fase 4 — pesos y perfiles

Sustituir o complementar pesos manuales con:

- BWM según Emamat;
- AHP opcional;
- sensibilidad formal;
- perfiles calibrados por distribución training-only, no por todo el periodo.

### Fase 5 — FlowSort

Implementar FlowSort como **comparador de selección**, no como rebalanceo.

Modos mínimos:

- V-shape + net flow;
- V-shape + leaving flow;
- level + net flow;
- usual + net flow.

Validar FlowSort con el mismo índice de clasificación `F` y con backtest posterior usando los mismos optimizadores.

### Fase 6 — criterios ETF ampliados

Agregar criterios cuando haya datos:

- max drawdown como criterio ELECTRE explícito;
- beta;
- tracking error por benchmark de bucket;
- avg dollar volume;
- fund age;
- expense ratio/AUM/spread si fuente lo permite.

### Fase 7 — universo PIT

En paralelo o después, resolver la fuente de datos:

- SEC-only público si no pagamos;
- Norgate+SEC si se aprueba presupuesto.

## Regla de investigación

No declarar que ELECTRE Tri falló hasta demostrar si falló:

- el sorting;
- los criterios;
- los pesos/perfiles;
- MaxSharpe;
- el rebalanceo;
- o el universo/data.

El resultado actual solo demuestra que **la configuración completa actual no generaliza**.

## Hipótesis de rediseño

La tesis debe pasar de:

> “ELECTRE Tri + MaxSharpe produce CAGR >10%”

A:

> “Un marco reproducible de sorting multicriterio para ETFs compara ELECTRE Tri y FlowSort, separa selección de asignación, corrige sesgo de universo y evalúa robustez walk-forward frente a benchmarks.”

Esto es más fuerte académicamente y reduce el riesgo de que toda la tesis dependa de una métrica de CAGR frágil.
