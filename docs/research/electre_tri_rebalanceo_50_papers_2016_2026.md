# Investigación extensa — ELECTRE Tri, MCDA y rebalanceo de portafolios (2016-2026)

**Fecha:** 2026-05-19  
**Alcance:** papers y trabajos académicos de los últimos 10 años relacionados con selección de portafolios por ELECTRE/MCDA, ETF/portafolios y metodologías de rebalanceo.  
**Fuentes consultadas:** OpenAlex, Semantic Scholar, arXiv/Crossref metadata y páginas editoriales accesibles públicamente.  
**Uso previsto:** orientar el roadmap del ETF optimizer y comparar nuestro modelo contra literatura reciente.

---

## Nota metodológica importante sobre el ranking de rentabilidad

El usuario pidió rankear los papers “desde más rentables a menos rentables”. En una revisión responsable, **no todos los papers reportan CAGR, retorno anualizado o Sharpe comparable**; muchos son teóricos, revisiones, metodologías de optimización, o reportan desempeño en mercados/horizontes distintos.

Por eso este documento usa dos niveles:

1. **Ranking de rentabilidad evidenciada/esperada**, basado en lo que el paper afirma o evalúa: outperformance, mejora de Sharpe, reducción de costes, control de drawdown, o advertencias contra rebalanceo mecánico.
2. **Bandera de comparabilidad:**
   - `Alta`: paper empírico con performance/backtest explícito.
   - `Media`: paper metodológico con evaluación empírica, pero no necesariamente comparable a ETF USA.
   - `Baja`: paper teórico, revisión o evidencia indirecta.

Este ranking **no debe citarse como meta-análisis numérico final** hasta extraer tablas completas de cada PDF y normalizar: universo, horizonte, costes, benchmark, frecuencia, CAGR, Sharpe, drawdown y turnover.

---

# Hallazgos globales

## 1. ELECTRE Tri / MCDA

- La literatura reciente usa ELECTRE Tri principalmente para **clasificar activos en grupos**, no para asignar pesos directamente.
- El paper central de Emamat et al. (2022) compara **ELECTRE-TRI y FlowSort**, con variantes pesimista/optimista y con/sin veto.
- La práctica defendible para nuestro proyecto es:  
  `ELECTRE Tri = selección/categorización` → `optimizador = asignación de pesos`.
- Los pesos de criterios suelen justificarse con experto, BWM, AHP o sensibilidad; los pesos manuales deben quedar como baseline, no como final.

## 2. Rebalanceo

- La literatura distingue claramente:
  - buy-and-hold;
  - constant-mix / fixed-weight;
  - calendar rebalancing;
  - tolerance-band / threshold rebalancing;
  - dynamic rebalancing;
  - transaction-cost-aware rebalancing;
  - reinforcement learning / model predictive control.
- Rebalancear más frecuentemente puede mejorar exposición/riesgo, pero aumenta costes y puede empeorar performance si el mercado tiene tendencia.
- Con costes, varios trabajos sugieren que **buy-and-hold o rebalanceo menos frecuente puede ganar** si la estrategia no compensa turnover.
- Para nuestro modelo, el motor debe comparar al menos:
  - calendario trimestral;
  - calendario anual;
  - buy-and-hold entre rebalanceos;
  - bandas de tolerancia;
  - recategorización mensual con operación solo si hay cambio relevante.

## 3. Implicación para nuestro modelo

La configuración preliminar más prometedora encontrada en el proyecto fue:

```text
ELECTRE Tri pesimista sin veto + rebalanceo trimestral + drift buy-and-hold
```

Esto coincide parcialmente con literatura que advierte que el veto puede excluir activos rentables y que el rebalanceo trimestral puede capturar mejor cambios sin llegar al coste de rotación mensual.

---

# Ranking de papers por rentabilidad evidenciada/esperada

> Ranking cualitativo basado en señal de rentabilidad, uso empírico y aplicabilidad al proyecto. Donde no hay CAGR comparable, se indica `N/D`.

| Rank | Paper / Año | Metodología | Hallazgo principal | Rentabilidad reportada comparable | Comparabilidad | Implicación para nuestro modelo |
|---:|---|---|---|---|---|---|
| 1 | **Smart Tangency Portfolio: Deep Reinforcement Learning for Dynamic Rebalancing and Risk–Return Trade-Off** (2025) | DRL + tangency portfolio + rebalanceo dinámico | Propone rebalanceo adaptativo para mejorar trade-off riesgo-retorno. | N/D en metadata; requiere PDF | Media | Comparar contra modo dinámico/RL como benchmark futuro, no reemplazar ELECTRE. |
| 2 | **Dynamic Black–Litterman Portfolios Incorporating Asymmetric Fractal Uncertainty** (2024) | Black–Litterman dinámico + RNN + ETFs | Predice precios ETF y ajusta portafolios dinámicamente buscando rentabilidad. | N/D en metadata; menciona profitability | Media | Añadir como baseline avanzado: BL dinámico trimestral/mensual. |
| 3 | **A Systematic Approach to Portfolio Optimization: A Comparative Study of Reinforcement Learning Agents, Market Signals, and Investment Horizons** (2024) | DQN/DDPG/PPO/SAC + horizontes | Compara agentes RL y señales de mercado para optimización de portafolio. | N/D en metadata | Media | Usar como benchmark de validación, especialmente para frecuencia de rebalanceo. |
| 4 | **Dynamic Portfolio Rebalancing: A Hybrid New Model Using GNNs and Pathfinding for Cost Efficiency** (2024) | GNN + pathfinding + costes | Busca rebalanceo dinámico eficiente en costes. | N/D en metadata | Media | Inspira política `hybrid`: rebalancear solo si coste-beneficio lo justifica. |
| 5 | **Constructing Cybersecurity Stocks Portfolio Using AI** (2024) | IA + selección temática + gestión dinámica | Construye portafolio temático con IA y backtesting 2018-2024. | N/D en metadata | Media | Útil como ejemplo de cartera temática y actualización dinámica. |
| 6 | **Unveiling Outperformance: A Portfolio Analysis of Top AI-Related Stocks against IT Indices and Robotics ETFs** (2024) | Análisis de outperformance vs índices/ETFs | Evalúa si acciones AI/robótica superan índices y ETFs. | N/D en metadata | Media | Benchmark sectorial: comparar ETF seleccionados contra índices temáticos. |
| 7 | **Sector ETF portfolio optimization using differential evolution** (2020) | Differential Evolution + sector ETFs | Busca asignación sectorial que supere índice amplio. | N/D en metadata | Alta si se extrae tesis/PDF | Baseline natural para nuestro optimizador ETF sectorial. |
| 8 | **Optimal portfolio selection with volatility information for a high frequency rebalancing algorithm** (2024) | Alta frecuencia + volatilidad | Usa información de volatilidad para reequilibrio frecuente. | N/D en metadata | Media | Comparar frecuencia alta solo con costes realistas. |
| 9 | **Constructing Optimal Portfolio Rebalancing Strategies with a Two-Stage Multiresolution-Grid Model** (2024) | Dos etapas + multiresolution grid | Optimiza cuándo/cómo rebalancear reduciendo tracking error y costes. | N/D en metadata | Alta | Directamente aplicable a política de rebalanceo por grid/tolerancia. |
| 10 | **Transaction cost optimization for online portfolio selection** (2017) | Online portfolio selection + TCO | Añade penalización L1 por cambios de pesos para reducir costes. | N/D; performance relativa | Alta | Implementar penalización de turnover en optimizador posterior. |
| 11 | **Multi-objective heuristic algorithms for practical portfolio optimization and rebalancing with transaction cost** (2017) | Multiobjetivo + costes + rebalanceo | Modela retorno, riesgo y costes en rebalanceo práctico. | N/D | Alta | Añadir objetivos: retorno, riesgo, turnover, coste. |
| 12 | **Dynamic Portfolio Choice with Linear Rebalancing Rules** (2017) | Reglas lineales dinámicas | Aproxima políticas dinámicas con reglas tratables bajo costes/restricciones. | N/D | Media | Diseñar reglas simples interpretables antes de RL. |
| 13 | **Rebalancing with transaction costs: theory, simulations, and actual data** (2022) | Teoría + simulación + datos reales | Con costes, buy-and-hold puede superar fixed-weight; rebalancing depende de autocorrelación y costes. | N/D; ejemplos teóricos | Alta | Mantener `buy_and_hold` como modo base y comparar costes. |
| 14 | **Strategic Rebalancing** (2020) | Rebalanceo estratégico | Advierte que rebalanceo mecánico vende ganadores y compra perdedores; puede dañar en crisis/tendencias. | N/D | Alta | Evitar rebalanceo mensual ciego; usar triggers. |
| 15 | **The Impact of Rebalancing Strategies on ETF Portfolio Performance** (2024) | ETFs + estrategias de rebalanceo | Evalúa rebalanceo sobre cartera diversificada de ETFs. | N/D en metadata; paper específico ETF | Alta | Referencia clave para justificar calendario vs bandas. |
| 16 | **A Comparison of Rebalanced and Buy and Hold Portfolios: Does Monetary Policy Matter?** (2015/2016 frontera) | Buy-and-hold vs rebalanceo ETF/index | Compara estrategias con índices rastreados por ETFs. | N/D | Alta | Justifica comparar buy-and-hold y rebalanceo. |
| 17 | **PEROLD-SHARPE REBALANCING STRATEGIES IN PRACTICE** (2016) | Buy-hold, constant weights, CPPI | Evalúa estrategias Perold-Sharpe en datos reales. | N/D | Alta | Implementar CPPI como benchmark futuro. |
| 18 | **The Unintended Consequences of Rebalancing** (2025) | Efectos de mercado del rebalanceo institucional | Rebalanceo calendarizado genera patrones predecibles e impacto de mercado. | N/D | Media | Advertir impacto de mercado si se escala; evitar calendario predecible. |
| 19 | **Technical Note—A Robust Perspective on Transaction Costs in Portfolio Optimization** (2018) | Costes = robust optimization/regularización | Demuestra equivalencia entre costes, robustez y regularización. | N/D teórico | Alta | Incorporar regularización/turnover penalty como fundamento académico. |
| 20 | **A Transaction-Cost Perspective on the Multitude of Firm Characteristics** (2019) | Costes y características | Costes cambian qué señales son útiles en portafolios óptimos. | N/D | Media | Penalizar señales que inducen alta rotación. |
| 21 | **The impact of transaction costs in portfolio optimization** (2018) | Costes en optimización | Muestra que costes alteran asignaciones y performance ex post. | N/D | Alta | Costes no pueden ser sensibilidad secundaria; deben entrar en optimización. |
| 22 | **Incorporating transaction costs, weighting management, and floating required return in robust portfolios** (2017) | Robust portfolios + costes + pesos mínimos | RRCVaR supera WCVaR según abstract; modela short sales/costes/thresholds. | N/D | Alta | Añadir umbral mínimo de trade y peso mínimo. |
| 23 | **Robust portfolio rebalancing with cardinality and diversification constraints** (2021) | Rebalanceo robusto + cardinalidad | Controla número de activos y diversificación. | N/D | Alta | Compatible con límite max ETFs y diversificación. |
| 24 | **Portfolio rebalancing under uncertainty using meta-heuristic algorithm** (2019) | Metaheurística bajo incertidumbre | Optimiza rebalanceo bajo incertidumbre. | N/D | Media | Baseline futuro si el problema se vuelve no convexo. |
| 25 | **Mean-variance portfolio selection with estimation risk and transaction costs** (2022) | MV + riesgo de estimación + costes | Integra incertidumbre paramétrica y costes. | N/D | Alta | Estimar incertidumbre de retornos/covarianza en walk-forward. |
| 26 | **High-dimensional index tracking based on the adaptive elastic net** (2020) | Index tracking + elastic net | Reduce posiciones pequeñas/ilíquidas y rebalanceo costoso. | N/D | Alta | Usar elastic-net/sparse weights para evitar microposiciones. |
| 27 | **Optimization Methods for Financial Index Tracking: From Theory to Practice** (2018) | Revisión index tracking | Explica tracking como problema de asignación sparse y costes. | N/D | Alta | Incorporar tracking error como criterio ETF. |
| 28 | **A systematic literature review on solution approaches for the index tracking problem** (2023) | Revisión sistemática | Resume métodos para index tracking y restricciones reales. | N/D | Alta | Base para tracking error y cardinalidad. |
| 29 | **Sparse Index Tracking: Simultaneous Asset Selection and Capital Allocation via ℓ0-Constrained Portfolio** (2024) | Sparse index tracking | Selección y pesos simultáneos con restricción L0. | N/D | Alta | Comparar ELECTRE selección + MaxSharpe vs optimización sparse integrada. |
| 30 | **Passive ESG Portfolio Management—The Benchmark Strategy for Socially Responsible Investors** (2021) | ESG passive strategies | Compara asignaciones ESG por desempeño financiero y ESG. | N/D | Media | Añadir criterios ESG solo si se defiende fuente y objetivo. |
| 31 | **Optimizing global risk-conscious portfolios: the strategic role of Sharia-compliant and ESG investments** (2025) | ESG/Sharia + rebalanceo dinámico | Integra activos ESG/Sharia en optimización global con rebalanceo. | N/D | Media | Útil si se expande a criterios no financieros. |
| 32 | **Sustainable Portfolio Rebalancing Under Uncertainty: A Multi-Objective Framework with Interval Analysis and Behavioral Strategies** (2025) | Multiobjetivo + intervalos + comportamiento | Rebalanceo sostenible bajo incertidumbre. | N/D | Media | Referencia para incertidumbre y preferencias del inversor. |
| 33 | **A neural network-particle swarm solver for sustainable portfolio optimization problems** (2025) | NN + PSO + sostenibilidad | Optimización de portafolios sostenibles. | N/D | Media | No prioritario para tesis actual salvo ESG. |
| 34 | **A constrained swarm optimization algorithm for large-scale long-run investments using Sharpe ratio-based performance measures** (2023) | Swarm optimization + Sharpe | Optimiza grandes portafolios con métricas Sharpe. | N/D | Media | Baseline heurístico para universo ETF grande. |
| 35 | **A hybrid level-based learning swarm algorithm with mutation operator for large-scale cardinality-constrained portfolio optimization problems** (2023) | LLSO + cardinalidad | Resuelve portafolios grandes con cardinalidad. | N/D | Media | Útil para restricciones `max_assets`. |
| 36 | **A level-based learning swarm optimizer with a hybrid constraint-handling technique for large-scale portfolio selection problems** (2022) | LLSO + restricciones | Manejo de restricciones en portafolios grandes. | N/D | Media | Menos prioritario que reglas simples. |
| 37 | **Deep Reinforcement Learning for Portfolio Optimization using Latent Feature State Space (LFSS) Module** (2021) | DRL + latent features | Usa estado latente para optimización de portafolio. | N/D | Media | Baseline académico, pero riesgo de overfitting alto. |
| 38 | **Deep Reinforcement Learning Task for Portfolio Construction** (2021) | DRL + entorno backtesting | Construye agente autónomo de portafolio con rewards. | N/D | Media | Útil para diseño de entorno, no tesis central. |
| 39 | **Machine Learning for Real-Time Portfolio Rebalancing: A Novel Approach to Financial Optimization** (2024) | ML + rebalanceo tiempo real | Propone rebalanceo en tiempo real. | N/D | Baja-media | Evitar si no hay datos intradía; útil como futuro. |
| 40 | **A machine learning approach to risk based asset allocation in portfolio optimization** (2025) | ML + asignación basada en riesgo | Asignación dinámica basada en riesgo. | N/D | Media | Baseline ML para perfiles de riesgo. |
| 41 | **Using ELECTRE-TRI and FlowSort methods in a stock portfolio selection context** (2022) | ELECTRE-TRI + FlowSort + BWM | Clasifica acciones en grupos; compara variantes con/sin veto y pesimista/optimista. | N/D comparable; retorno futuro del grupo | Alta metodológica | Paper central: replicar estructura de grupos y variantes. |
| 42 | **A python-based multicriteria portfolio selection DSS** (2020) | DSS multicriterio | Sistema integrado para preferencias del inversor y selección de portafolio. | N/D | Alta metodológica | Inspiración para dashboard y preferencias. |
| 43 | **Multicriteria Decision Aid Methods and portfolio selection: case study** (2021) | MCDA aplicado a bolsa | Caso de constitución de portafolio con métodos MCDA. | N/D | Media | Referencia para capítulo metodológico. |
| 44 | **Combinatorial portfolio selection with the ELECTRE III method: case study of the stock exchange of Thailand** (2017) | ELECTRE III + selección combinatoria | Ayuda a pequeños inversores con selección interpretable. | N/D | Media | ELECTRE III como comparación ranking, no Tri. |
| 45 | **Novel linear programming models based on distance measure of IFSs and modified TOPSIS method for portfolio selection** (2022) | TOPSIS modificado + programación lineal | Selección bajo incertidumbre cuando no hay series completas. | N/D | Media | Comparar TOPSIS como baseline MCDA. |
| 46 | **A Bhattacharyya Triangular intuitionistic fuzzy sets with OWA operator-based decision making for optimal portfolio selection in Saudi exchange** (2024) | Fuzzy sets + OWA + portfolio | Herramienta fuzzy para selección óptima en mercado saudí. | N/D | Media | Baseline fuzzy/OWA, pero menos directo para ETFs. |
| 47 | **Best-Worst Method / BWM in portfolio selection literature** (varios 2016-2026) | BWM para pesos | BWM reduce arbitrariedad de pesos con comparación experto. | N/D | Alta metodológica | Implementar BWM para pesos ELECTRE. |
| 48 | **MCDM portfolio selection with TOPSIS/VIKOR/PROMETHEE family** (varios 2016-2026) | MCDA ranking/sorting | Métodos MCDA usados para ranking, pero menos adecuados que Tri para categorías. | N/D | Media | Añadir TOPSIS/VIKOR como modo comparativo, no principal. |
| 49 | **The Effects of Portfolio Construction on the Performance of Style Factor ETFs** (2019) | Construcción de ETFs factor | Advierte que construcción heurística puede producir bets no deseados. | N/D | Alta para ETF | Añadir análisis de exposición/factor si hay datos. |
| 50 | **Determinants of tracking error in German ETFs – the role of market liquidity** (2016) | Tracking error + liquidez | Liquidez del subyacente afecta tracking error diario. | N/D | Alta ETF | Incorporar tracking error y liquidez como criterios ELECTRE. |

---

# Ranking práctico de metodologías para implementar en el proyecto

## Tier A — Prioridad inmediata

1. **ELECTRE Tri pesimista sin veto + grupos + BWM + rebalanceo trimestral buy-and-hold**  
   Motivo: ya dio >10% en piloto interno y está alineado con paper.
2. **ELECTRE Tri pesimista con veto + sensibilidad**  
   Motivo: variante estándar; mantiene trazabilidad del veto.
3. **Rebalanceo por bandas de tolerancia**  
   Motivo: literatura sugiere evitar calendario ciego y controlar costes.
4. **Penalización de turnover / transaction-cost-aware optimization**  
   Motivo: soporte teórico fuerte.

## Tier B — Baselines fuertes

5. **MinVariance con shrinkage + turnover penalty**
6. **MaxSharpe con fallback y costes**
7. **Sparse/index-tracking objective**
8. **TOPSIS/VIKOR/PROMETHEE como MCDA comparativos**

## Tier C — Investigación futura

9. **Black–Litterman dinámico**
10. **DRL / RL rebalancing**
11. **GNN/pathfinding cost-efficient rebalancing**
12. **CPPI / portfolio insurance**

---

# Cambios concretos recomendados al roadmap

## Para defender ELECTRE Tri

- Implementar BWM o AHP para pesos.
- Mantener las cuatro variantes: pesimista/optimista × con/sin veto.
- Reportar estabilidad de categoría, no solo performance.
- Construir cartera desde el mejor grupo y completar desde el segundo grupo solo si falta diversificación mínima.

## Para defender rebalanceo

- Comparar:
  - annual calendar;
  - quarterly calendar;
  - monthly calendar;
  - threshold/tolerance band;
  - category-change triggered;
  - hybrid calendar + threshold.
- Exportar:
  - `rebalance_events.csv`;
  - `turnover_by_event.csv`;
  - `effective_weights.csv`;
  - `category_events.csv`.

## Para defender rentabilidad >10%

- No basta con un piloto de 2021-2024.
- Necesitamos:
  - 10-15 años si los datos lo permiten;
  - >=5 folds;
  - >=60 meses OOS;
  - costes realistas;
  - bootstrap pareado vs SPY/60-40/EqualWeight/MinVariance/MaxSharpe.

---

# Lista corta de papers prioritarios para leer PDF completo

1. Emamat et al. (2022), ELECTRE-TRI and FlowSort.
2. The Impact of Rebalancing Strategies on ETF Portfolio Performance (2024).
3. Rebalancing with transaction costs: theory, simulations, and actual data (2022).
4. Strategic Rebalancing (2020).
5. Transaction cost optimization for online portfolio selection (2017).
6. Multi-objective heuristic algorithms for practical portfolio optimization and rebalancing with transaction cost (2017).
7. Dynamic Portfolio Choice with Linear Rebalancing Rules (2017).
8. Technical Note—A Robust Perspective on Transaction Costs in Portfolio Optimization (2018).
9. Robust portfolio rebalancing with cardinality and diversification constraints (2021).
10. Determinants of tracking error in German ETFs – the role of market liquidity (2016).

---

# Próximo paso responsable

Para convertir este ranking en una revisión académica final, crear una matriz CSV con estas columnas:

```text
paper_id,title,year,doi,methodology,asset_universe,rebalance_policy,cost_model,benchmark,cagr,sharpe,max_drawdown,turnover,main_finding,applicability_to_project
```

Luego extraer manualmente o con PDF parsing los valores numéricos de los 10 papers prioritarios antes de afirmar una jerarquía cuantitativa definitiva.
