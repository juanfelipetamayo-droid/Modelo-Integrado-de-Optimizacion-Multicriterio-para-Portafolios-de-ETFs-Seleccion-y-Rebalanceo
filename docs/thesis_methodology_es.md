# Capítulo metodológico — Modelo integrado de selección y rebalanceo de portafolios ETF

> Estado: borrador académico consolidado para tesis.  
> Alcance empírico actual: evidencia piloto con datos públicos; no evidencia final survivorship-bias-free.

## 1. Planteamiento del problema

La industria global de ETFs ha crecido hasta convertirse en un universo de inversión de gran escala y alta heterogeneidad. Fuentes recientes basadas en ETFGI reportan aproximadamente USD 19.85 billones en activos globales de ETFs al cierre de 2025, USD 2.37 billones de flujos netos durante 2025 y más de 15,800 productos listados globalmente. Además, los ETFs activos alcanzaron aproximadamente USD 1.92 billones en activos y USD 637.47 mil millones de flujos netos durante 2025.

Este crecimiento crea un problema práctico y académico: la construcción de portafolios ETF ya no consiste únicamente en decidir pesos sobre un conjunto pequeño de índices tradicionales. Primero es necesario clasificar, filtrar y justificar qué ETFs son candidatos aceptables bajo criterios múltiples: rentabilidad, riesgo, liquidez, costes, tracking error, estabilidad y exposición. Luego, sobre el subconjunto elegido, debe definirse una asignación de capital y una política de rebalanceo que considere costes de transacción y drift de pesos.

## 2. Objetivo general

Diseñar, implementar y validar un modelo integrado de selección y rebalanceo de portafolios ETF mediante ELECTRE Tri, optimización cuantitativa y políticas de rebalanceo con costes, evaluado mediante backtesting walk-forward y comparado contra benchmarks tradicionales.

## 3. Hipótesis de investigación

Una arquitectura en dos etapas —clasificación multicriterio ELECTRE Tri seguida de optimización cuantitativa de pesos y rebalanceo controlado— puede producir portafolios ETF competitivos frente a benchmarks tradicionales, manteniendo interpretabilidad metodológica, control de riesgo y trazabilidad empírica.

La hipótesis se separa en tres niveles de validez:

1. **Validez metodológica:** el sistema implementa correctamente el modelo multicriterio y evita sesgos básicos de backtesting.
2. **Validez empírica:** el portafolio resultante obtiene métricas competitivas frente a benchmarks out-of-sample.
3. **Validez operativa:** el sistema produce artefactos auditables, pesos, eventos de rebalanceo y límites explícitos de uso.

## 4. Arquitectura metodológica

El modelo se compone de seis etapas:

1. construcción del universo ETF;
2. ingeniería de criterios financieros;
3. clasificación multicriterio con ELECTRE Tri;
4. optimización de pesos sobre ETFs seleccionados;
5. rebalanceo con costes y drift;
6. validación walk-forward y reporte reproducible.

La contribución principal no es reemplazar la optimización financiera clásica, sino integrarla con un filtro multicriterio interpretable. ELECTRE Tri actúa como mecanismo de selección y categorización; la optimización posterior asigna pesos.

## 5. Universo ETF y fuentes de datos

La implementación final pública usa un universo ETF público aproximado point-in-time (`public_approximate_pit`) construido a partir de fuentes regulatorias y de mercado. La regla central es que cada observación debe estar disponible para la fecha de decisión mediante `source_available_date <= rebalance_date`; de este modo se evitan violaciones explícitas de look-ahead causadas por usar información publicada después del rebalanceo.

Dado que no fue posible acceder a una base institucional survivor-bias-free como CRSP, se construyó un universo ETF público aproximado point-in-time a partir de fuentes regulatorias y de mercado, incorporando fechas de disponibilidad de información y etiquetas de calidad. Esta reconstrucción no elimina por completo el riesgo de sesgo de supervivencia, pero permite reducirlo y hacerlo explícito dentro del protocolo de backtesting.

La ruta institucional sigue siendo metodológicamente preferible: CRSP, Morningstar Direct, Lipper, Bloomberg o Refinitiv/LSEG permitirían una cobertura histórica más fuerte de ETFs liquidados, fusionados o deslistados. Por tanto, la ruta pública debe tratarse como reconstrucción parcial, con cobertura por año, etiquetas de calidad y límites de inferencia.

La matriz ampliada de fuentes y plan de adopción quedó documentada en `docs/research/etf_point_in_time_data_sources.md`. Las reglas de redacción defendible quedaron consolidadas en `docs/methodology/thesis_claims_guardrails.md`.

Por tanto, las corridas actuales se clasifican como:

```text
public_approximate_pit
```

y no deben describirse como:

```text
completamente survivor-bias-free
CRSP-grade
prueba concluyente de superioridad de mercado
```

## 6. Ingeniería de criterios

La etapa de feature engineering calcula criterios financieros desde precios ajustados y volumen. Los criterios implementados o contemplados se dividen en:

### Criterios de beneficio

- CAGR;
- Sharpe;
- Sortino;
- liquidez medida por volumen monetario promedio.

### Criterios de coste o riesgo

- volatilidad;
- max drawdown;
- tracking error;
- expense ratio;
- spread;
- beta o desviación respecto a benchmark.

En la versión pública actual, las métricas disponibles dependen de OHLCV. Variables como expense ratio, AUM, spread y tracking error completo requieren fuentes adicionales de datos de fondos o benchmarks específicos.

## 7. ELECTRE Tri como clasificador multicriterio

ELECTRE Tri se usa como método de sorting, no como ranking simple ni como optimizador de portafolios. Cada ETF se compara contra perfiles de referencia que separan categorías ordenadas. La salida de ELECTRE Tri define admisibilidad o categoría; la asignación de capital se realiza en una etapa posterior e independiente.

```text
below_minimum
between_minimum_preferred
above_preferred
```

La implementación actual soporta:

- asignación pesimista;
- asignación optimista;
- con veto;
- sin veto;
- múltiples perfiles;
- umbrales de indiferencia, preferencia y veto;
- backend interno;
- backend `pyDecision` ELECTRE Tri-B para comparación metodológica.

Esto permite replicar la forma metodológica del paper central de ELECTRE-TRI/FlowSort: comparar variantes pesimista/optimista y con/sin veto, en lugar de reducir el modelo a un filtro binario.

## 8. Optimización posterior de pesos

Después de la clasificación, los ETFs seleccionados pasan a una etapa cuantitativa de asignación de pesos. Las estrategias implementadas son:

- EqualWeight;
- MinVariance;
- MaxSharpe;
- covarianza muestral;
- covarianza Ledoit-Wolf;
- fallback de optimización hacia estrategias más robustas cuando MaxSharpe falla numéricamente.

La separación es metodológicamente importante:

```text
ELECTRE Tri decide qué activos son admisibles.
La optimización decide cuánto capital recibe cada activo.
```

## 9. Rebalanceo, costes y drift de pesos

El motor de backtesting distingue entre pesos objetivo y pesos efectivos. Esto permite modelar drift entre rebalanceos.

Modos principales:

```text
constant_mix
buy_and_hold
```

Políticas de rebalanceo:

```text
calendar
threshold
category_change / every_period recategorization
```

Estas políticas pertenecen al motor de backtesting y cartera. FlowSort y ELECTRE Tri clasifican o comparan alternativas; no ejecutan rebalanceos por sí mismos.

Controles adicionales:

- costes de transacción en basis points;
- turnover por evento;
- tolerancia máxima de drift;
- penalización de turnover;
- confirmación de categoría;
- filtro de materialidad mínima por score ELECTRE.

La evidencia piloto mostró que recategorizar sin control produce whipsaw. La confirmación de categoría durante dos períodos redujo eventos innecesarios y elevó el desempeño en modo every-period.

## 10. Validación walk-forward

La validación usa ventanas de entrenamiento y prueba. El optimizador solo recibe datos de la ventana de entrenamiento y aplica los pesos al período out-of-sample posterior. Esto reduce look-ahead bias.

Los benchmarks se separan por semántica:

- `SPY_buy_hold` como referencia fija;
- `60/40_SPY_BND_fixed_weight` como asignación fija;
- `EqualWeight_walk_forward`;
- `MinVariance_walk_forward`;
- `MaxSharpe_walk_forward`;
- `ELECTRE_MaxSharpe_walk_forward` como modelo principal.

La regla documental es que ningún benchmark optimizado in-sample debe mezclarse con conclusiones primarias out-of-sample.

## 11. Estado empírico actual

La corrida final congelada usa `configs/thesis_final.yaml` y reporta resultados en `results/thesis_final/`. Los modelos principales separan benchmarks fijos, benchmarks de universo, variantes ELECTRE y variantes FlowSort. MaxSharpe queda como diagnóstico o experimental, no como especificación principal de tesis.

Resultado final 2015-2025 con OOS suficiente:

| Estrategia | Rol | CAGR | Sharpe | Max DD | Nota estadística |
|---|---|---:|---:|---:|---|
| SPY_buy_hold | benchmark | 13.85% | 0.867 | -23.93% | benchmark de comparación |
| 60/40_SPY_AGG_fixed_weight | benchmark | 9.15% | 0.849 | -20.21% | menor CAGR que SPY en la muestra |
| ELECTRE_EqualWeight_walk_forward | final | 3.78% | 0.332 | -20.45% | no presenta evidencia robusta de superioridad frente a SPY |
| ELECTRE_MinVariance_walk_forward | final | 3.40% | 0.320 | -20.23% | no presenta evidencia robusta de superioridad frente a SPY |
| ELECTRE_InverseVol_walk_forward | final | 2.94% | 0.283 | -20.06% | no presenta evidencia robusta de superioridad frente a SPY |
| FlowSort_EqualWeight_walk_forward | final | 4.43% | 0.390 | -22.22% | no presenta evidencia robusta de superioridad frente a SPY |
| FlowSort_MinVariance_walk_forward | final | 3.42% | 0.328 | -21.88% | no presenta evidencia robusta de superioridad frente a SPY |
| FlowSort_InverseVol_walk_forward | final | 3.12% | 0.305 | -22.14% | no presenta evidencia robusta de superioridad frente a SPY |

Interpretación:

- La contribución defendible es metodológica: construcción de universo público aproximado PIT, trazabilidad, separación selección/asignación/rebalanceo, comparación ELECTRE Tri frente a FlowSort, clasificación previa al portafolio y ablations.
- La evidencia empírica actual no permite afirmar que el modelo vence al mercado.
- Las ventanas con CAGR alto, incluyendo resultados cercanos a 18% en experimentos piloto, se tratan como exploración y no como evidencia final.
- Las conclusiones principales deben apoyarse en intervalos de confianza, bootstrap por bloques, tests pareados, drawdown y sensibilidad.

## 12. Límites de la evidencia actual

Los diagnósticos de la ventana extendida indican:

```text
walk_forward_folds = 31
oos_periods = 93
sufficiency_label = thesis_grade_oos
```

Esto supera el umbral mínimo propuesto para suficiencia OOS:

```text
>= 5 folds
>= 60 meses OOS
```

Sin embargo, la fuente pública actual sigue sin ser survivorship-bias-free. Por ello, la redacción final debe usar lenguaje prudente:

```text
La arquitectura es metodológicamente válida; la configuración actual requiere rediseño porque no generaliza en la ventana OOS extendida.
```

No debe formularse una conclusión de victoria de mercado. La redacción correcta es que la evidencia pública actual no presenta superioridad robusta frente al benchmark.

## 13. Artefactos de reproducibilidad

Cada corrida robusta genera artefactos auditables:

- `strategy_comparison.csv`;
- `equity_curves.csv`;
- `drawdowns.csv`;
- `electre_selection.csv`;
- `electre_selection_by_rebalance.csv`;
- `electre_weights.csv`;
- `electre_effective_weights.csv`;
- `rebalance_events.csv`;
- `cost_sensitivity.csv`;
- `bootstrap_metric_intervals.csv`;
- `paired_benchmark_tests.csv`;
- `fold_performance.csv`;
- `fold_holdings_attribution.csv`;
- `electre_sensitivity.csv`;
- `fold_diagnostics.json`;
- `data_quality_verdict.json`;
- `run_manifest.json`;
- `provenance.json`;
- `methodology_report.md`.

Estos artefactos permiten auditar código, datos, parámetros, fuentes, limitaciones y resultados.

## 14. Contribuciones actuales

| Contribución | Implementación | Artefacto | Límite de claim |
|---|---|---|---|
| Universo ETF público aproximado PIT | `public_approximate_pit`, `source_available_date`, quality labels | universo investable / diagnostics | Reduce y explicita sesgos; no es completamente survivor-bias-free |
| Clasificación ETF multicriterio | ELECTRE Tri con perfiles, veto y variantes | `electre_selection.csv` | ELECTRE clasifica; no optimiza portafolios |
| Comparación MCDA | ELECTRE Tri frente a FlowSort | `electre_vs_flowsort/` | FlowSort clasifica/ordena; no rebalancea |
| Evaluación previa al portafolio | diagnósticos de clasificación antes de performance | classification diagnostics | Separa calidad de selección y retorno posterior |
| Asignación de pesos | EqualWeight, MinVariance, InverseVol; MaxSharpe experimental | `electre_weights.csv`, `final_strategy_comparison.csv` | La performance depende de asignación y rebalanceo, no solo de MCDA |
| Drift y rebalanceo | `buy_and_hold`, `constant_mix`, calendar/threshold | `electre_effective_weights.csv`, `rebalance_events.csv` | Política de cartera separada del clasificador |
| Ablations | selección vs asignación, variantes ELECTRE/FlowSort | `selection_allocation_ablation/` | Aíslan fuentes de desempeño sin claim causal absoluto |
| Inferencia estadística | block bootstrap, IC, tests pareados | `final_statistical_intervals.csv`, `final_return_difference_tests.csv` | Sin IC favorable no se afirma superioridad |

## 15. Trabajo pendiente para defensa final

Prioridades:

1. congelar una configuración candidata antes de más tuning;
2. separar muestra de calibración y muestra de validación;
3. extender historia hasta al menos 60 meses OOS;
4. conseguir o aproximar universo point-in-time con ETFs deslistados;
5. añadir pruebas pareadas contra SPY y 60/40;
6. incorporar criterios ETF-specific: expense ratio, AUM, spread, tracking error, beta;
7. justificar pesos de ELECTRE mediante BWM, AHP o sensibilidad sistemática;
8. documentar explícitamente limitaciones y no sobreafirmar resultados.

## 16. Conclusión metodológica

El proyecto ya cumple la arquitectura central de la tesis: universo público aproximado point-in-time, selección multicriterio interpretable, asignación posterior de pesos, rebalanceo con costes, validación reproducible, comparación ELECTRE Tri frente a FlowSort, ablations e inferencia estadística.

La conclusión actual debe formularse de manera acotada:

> La tesis construye y audita una metodología reproducible para selección y rebalanceo de portafolios ETF. La evidencia pública actual permite defender la arquitectura, la trazabilidad y los controles contra look-ahead, pero no permite afirmar que la base sea completamente survivor-bias-free ni que el modelo venza al mercado.
