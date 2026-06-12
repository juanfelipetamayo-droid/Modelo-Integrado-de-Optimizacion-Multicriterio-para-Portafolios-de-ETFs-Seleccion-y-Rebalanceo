# Auditoría metodológica: Xidonas et al. (2009) + Emamat et al. (2022) frente al ETF optimizer

Fecha: 2026-06-09

PDFs locales:

- `docs/research/xidonas_et_al_2009b_multicriteria_equity_selection_using_financial_analysis.pdf`
- `docs/research/using_electre_tri_flowsort_stock_portfolio_selection_emamat_2022.pdf`

## Decisión ejecutiva

No debemos limitarnos al paper griego. **Xidonas et al. (2009)** justifica que ELECTRE Tri es apropiado para selección financiera multicriterio, pero no debe dictar toda la metodología ETF. **Emamat et al. (2022)** agrega más valor operativo porque compara ELECTRE-TRI y FlowSort, usa BWM para pesos, evalúa variantes con/sin veto y pesimista/optimista, y valida las clasificaciones con retorno futuro.

La lectura conjunta sugiere que el proyecto debe modelarse así:

```text
universo PIT auditable
→ criterios ETF adecuados y conocidos al rebalance
→ sorting multicriterio: ELECTRE Tri y/o FlowSort
→ selección de clase superior
→ asignación de pesos separada: equal-weight / min-var / robust optimizer / multiobjetivo
→ walk-forward con costos, turnover y benchmarks
→ validación de clasificación + validación de portafolio
```

Punto clave: **FlowSort no es una técnica de rebalanceo**. Es un método de sorting/clasificación de la familia PROMETHEE. Su valor para nuestro proyecto es servir como comparador o alternativa de selección frente a ELECTRE Tri, no como política de rebalanceo.

## Paper 1: Xidonas, Mavrotas & Psarras (2009)

Referencia: Xidonas, P., Mavrotas, G., & Psarras, J. (2009). *A multicriteria methodology for equity selection using financial analysis*. Computers & Operations Research, 36, 3187–3203. DOI `10.1016/j.cor.2009.02.009`.

### Qué hace metodológicamente

1. Plantea la selección de activos como una etapa previa a la construcción del portafolio.
2. Usa ELECTRE Tri para clasificar acciones según desempeño financiero corporativo.
3. Separa firmas por industria/supersector antes de comparar, para evitar comparaciones incoherentes entre bancos, aseguradoras, industriales, etc.
4. Usa criterios de análisis financiero/fundamental por tipo de empresa, no una misma matriz para todos.
5. Define tres categorías:
   - `C3`: desempeño financiero excelente / elegibles;
   - `C2`: desempeño medio / estudiar más;
   - `C1`: desempeño malo / no elegibles.
6. Usa tanto asignación pesimista como optimista y toma el **overlap**; si una acción no cae consistentemente en `C3` en ambas, no se selecciona.
7. Integra persistencia temporal: exige que la acción aparezca en `C3` en al menos dos de tres años.
8. Los pesos, perfiles y umbrales se determinan con expertos, usando `resistance to change grid`.
9. Valida con expertos y con retorno/riesgo posterior: retorno de capital y desviación estándar de retorno.

### Qué nos enseña

- ELECTRE Tri es defendible como **clasificador no compensatorio** para seleccionar candidatos financieros.
- La selección debe ser interpretada como **security analysis**, no como asignación final de pesos.
- La robustez del sorting importa más que una sola corrida.
- La consistencia entre asignación pesimista/optimista y estabilidad temporal es central.
- No todos los criterios deben aplicarse igual a todos los activos: en ETFs esto se traduce en usar criterios adaptados por tipo de ETF o por bucket: equity, fixed income, commodities, leveraged/inverse, thematic, etc.

## Paper 2: Emamat et al. (2022)

Referencia: Emamat, M. S. M. M., Mota, C. M. de M., Mehregan, M. R., Sadeghi Moghadam, M. R., & Nemery, P. (2022). *Using ELECTRE-TRI and FlowSort methods in a stock portfolio selection context*. Financial Innovation, 8:11. DOI `10.1186/s40854-021-00318-1`.

### Qué hace metodológicamente

1. Compara dos métodos de sorting:
   - ELECTRE-TRI;
   - FlowSort.
2. Usa BWM (Best–Worst Method) para derivar pesos de criterios.
3. Considera **4 enfoques ELECTRE-TRI**:
   - pesimista con veto;
   - pesimista sin veto;
   - optimista con veto;
   - optimista sin veto.
4. Considera **15 enfoques FlowSort**:
   - 5 funciones de preferencia;
   - 3 flujos de asignación: leaving `Φ+`, entering `Φ-`, net `Φ`.
5. Usa criterios financieros como retorno, beta, margen neto, ROA, ROE, EPS, P/E y P/BV.
6. Define dos perfiles límite para tres clases ordenadas.
7. Valida con retorno real en el periodo siguiente, usando un índice `F`: porcentaje de acciones seleccionadas con retorno superior al promedio.
8. Hace sensibilidad extensa sobre pesos, perfiles, umbrales de preferencia/indiferencia y nivel de corte `λ`.

### Hallazgos importantes para nosotros

- En su caso, ELECTRE-TRI **pesimista sin veto** fue el mejor enfoque ELECTRE inicial.
- FlowSort con función V-shape y leaving flow tuvo mejor `F` inicial que ELECTRE.
- Los autores concluyen que usar veto en ELECTRE-TRI no produjo buen resultado para ese problema de stock selection y sugieren no usar veto en problemas similares.
- Si el resultado pesimista y optimista diverge mucho, hay incomparabilidad: falta información, criterios o precisión.
- El estudio enfatiza que el framework es para **selección de acciones**, no para asset allocation. Para asignar pesos se necesitan modelos multiobjetivo o goal programming.
- Los parámetros mal definidos reducen la potencia del modelo; la sensibilidad no es opcional.

## Qué estamos haciendo actualmente

Según el código actual:

- `src/etf_optimizer/selection/electre_tri.py` implementa ELECTRE Tri con:
  - criterios `q`, `p`, `v`;
  - perfiles ordenados;
  - `lambda_cut`;
  - asignación pesimista/optimista;
  - modo con/sin veto;
  - backend opcional `pyDecision`.
- `scripts/run_sprint_experiment.py` define criterios actuales:
  - `cagr` peso 0.35;
  - `volatility` peso 0.25;
  - `sharpe` peso 0.25;
  - `sortino` peso 0.15.
- Perfiles actuales:
  - `minimum`: CAGR 3%, volatilidad 25%, Sharpe 0.3, Sortino 0.4;
  - `preferred`: CAGR 10%, volatilidad 18%, Sharpe 0.8, Sortino 1.0.
- El pipeline selecciona activos cuya categoría empieza por `above_`.
- Si no hay seleccionados, el pipeline cae a un fallback de los top 5 por credibilidad para que la corrida no falle.
- El modelo principal normalmente usa selección ELECTRE + `MaxSharpe` para pesos.
- Se agregó recategorización `every_period`, eventos por `category_change`, threshold rebalance y controles de exposición.

## Desviaciones metodológicas detectadas

| Tema | Papers | Implementación actual | Evaluación |
|---|---|---|---|
| Fuente base | Xidonas/Emamat usan acciones con datos fundamentales | ETFs con OHLCV público | Adaptación razonable, pero criterios insuficientes para ETFs |
| Universo | Universo observable del mercado estudiado | Universo current/public no PIT en varias corridas | Falla metodológica mayor para tesis histórica |
| Pesos | Expertos + resistance-to-change o BWM | Pesos manuales | Débil académicamente; debe pasar a BWM/AHP/sensibilidad formal |
| Criterios | Fundamentales + riesgo/retorno posterior | CAGR, volatilidad, Sharpe, Sortino | Demasiado dependiente de performance pasada; faltan expense ratio, AUM/liquidez, tracking error, beta, drawdown, categoría |
| Categorías | Tres clases ordenadas y selección clase superior | Tres clases vía dos perfiles, selecciona `above_preferred` | Parcialmente alineado |
| Pesimista/optimista | Comparan/usan overlap o interpretan divergencias | Se puede elegir un modo, pero producción suele usar uno | Falta diagnosticar divergencia e incomparabilidad por fold |
| Veto | Xidonas lo incluye; Emamat encuentra peor performance con veto | Tenemos con/sin veto; candidato reciente usa sin veto | Bien encaminado; debe justificarse con sensibilidad |
| FlowSort | Comparador de sorting | No implementado | Oportunidad fuerte; no es rebalanceo |
| Validación de clasificación | Retorno futuro / índice F / sensibilidad | Validación principal es performance de portafolio | Falta separar calidad de clasificación de calidad de asignación |
| Asset allocation | Papers dicen que selección no determina pesos | Usamos MaxSharpe tras selección | Correcto como extensión, pero MaxSharpe puede ser fuente principal del fallo |
| Estabilidad temporal | Xidonas exige consistencia 2 de 3 años | Recategorización y confirmación reciente, no paper-style stability table | Se debe formalizar selección persistente y Jaccard/category transitions |
| Sector comparability | Xidonas clasifica por sector | ETFs se clasifican con buckets heurísticos solo para exposure cap | Falta sorting por familias ETF o perfiles por tipo de ETF |

## Por qué ocurrió la desviación

1. **Limitación de datos**: no teníamos fundamentales ETF completos, expense ratios, AUM, spreads, tracking error, holdings o datos PIT. Por eso se usaron criterios derivados de OHLCV: CAGR, volatilidad, Sharpe, Sortino.
2. **Necesidad de MVP ejecutable**: para tener un pipeline funcional se priorizó `features → ELECTRE → optimizer → backtest`, aunque los pesos/perfiles fueran manuales.
3. **Confusión entre metodología de selección y estrategia de inversión**: la literatura usa ELECTRE/FlowSort para seleccionar candidatos; el proyecto necesitaba performance de portafolio y se añadió MaxSharpe. Esto es válido como extensión, pero introduce otra fuente de error.
4. **Optimización por resultado piloto**: el piloto favorable llevó a añadir controles de rebalanceo/exposición para mejorar performance, antes de cerrar la fidelidad metodológica y el universo PIT.
5. **Falta de validación de clasificación separada**: se evaluó el portafolio final, no si las clases ELECTRE predicen mejor retorno/riesgo futuro que alternativas.

## ¿Hay fallas metodológicas?

Sí, pero no todas son fatales.

### Fallas críticas

1. **Universo no point-in-time** para corridas históricas: esto impide claim thesis-grade.
2. **Pesos y perfiles manuales** sin BWM/AHP/expert elicitation ni calibración documentada.
3. **Criterios ETF incompletos**: falta expense ratio, AUM, spread, tracking error, beta, drawdown como criterio ELECTRE, liquidez real y clasificación por tipo de ETF.
4. **No separar selección de asignación**: el mal resultado puede venir de MaxSharpe, no de ELECTRE.
5. **No implementar FlowSort** como comparador cuando Emamat lo muestra metodológicamente valioso.

### Aspectos defendibles

1. ELECTRE Tri sí es un método adecuado para sorting financiero.
2. La arquitectura en dos etapas `selection → allocation` es coherente, siempre que se declare como extensión.
3. Usar pesimista sin veto tiene respaldo en Emamat para stock selection.
4. La validación walk-forward larga es correcta y el resultado negativo debe preservarse.

## Cómo deberíamos programarlo después de esta auditoría

### 1. Modelo de selección

Implementar una interfaz común:

```python
class SortingModel:
    def assign(features, profiles, criteria, parameters) -> pd.DataFrame:
        ...
```

Backends:

- `electre_tri_internal`
- `electre_tri_pydecision`
- `flowsort_promethee`
- eventualmente `topsis` / `promethee` como benchmarks MCDA

### 2. Modos paper-style obligatorios

Para ELECTRE:

- `pessimistic_with_veto`
- `pessimistic_without_veto`
- `optimistic_with_veto`
- `optimistic_without_veto`
- `overlap_pessimistic_optimistic`: seleccionar solo si ambos asignan clase superior
- `incomparability_report`: divergencia entre pesimista y optimista

Para FlowSort:

- funciones: usual, U-shape, V-shape, V-shape with indifference, level
- flujos: leaving `Φ+`, entering `Φ-`, net `Φ`
- selección por clase superior

### 3. Pesos

Mantener pesos manuales solo como baseline. Añadir:

- BWM documentado;
- AHP opcional;
- sensibilidad sistemática;
- pesos por perfil ETF o por objetivo de inversor.

### 4. Criterios ETF recomendados

Mínimo público inicial:

- retorno/CAGR trailing;
- volatilidad;
- max drawdown;
- Sharpe/Sortino;
- beta vs SPY o benchmark de bucket;
- tracking error vs benchmark de bucket;
- avg dollar volume;
- edad del fondo;
- proxy de concentración/categoría si hay metadata.

Con fuente mejor:

- expense ratio;
- AUM;
- spread;
- distributions/total return;
- holdings overlap;
- issuer/category/fund type.

### 5. Validaciones separadas

Además del backtest de portafolio:

- `classification_effectiveness.csv`: porcentaje de clase superior que supera promedio futuro por fold, análogo a `F`.
- `category_forward_return.csv`: retorno futuro promedio por categoría.
- `pessimistic_optimistic_divergence.csv`.
- `selection_jaccard_by_fold.csv`.
- `category_transition_matrix.csv`.
- `ablation_strategy_comparison.csv`: ELECTRE+EW, ELECTRE+MinVar, ELECTRE+MaxSharpe, FlowSort+EW, FlowSort+MinVar, raw MaxSharpe, EqualWeight.

## Próximo paso correcto

No programar aún. Primero crear una matriz de rediseño:

```text
paper_requirement,current_implementation,gap,severity,fix,artifact,validation
```

Luego implementar por orden:

1. auditoría paper→código;
2. ablation sin tocar metodología nueva;
3. BWM/pesos y diagnostics de incomparabilidad;
4. FlowSort como comparador de selección;
5. criterios ETF ampliados;
6. universo PIT;
7. solo entonces nuevos experimentos de performance.
