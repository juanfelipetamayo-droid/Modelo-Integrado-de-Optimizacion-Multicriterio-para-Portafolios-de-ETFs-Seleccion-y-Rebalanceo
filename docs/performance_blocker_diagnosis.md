# Diagnóstico del bloqueador de performance

## Hecho empírico central

El piloto corto 2021–2025 reportó métricas atractivas: **18.08% CAGR, Sharpe 2.588, MDD -2.40%**. Al extender la validación a 2015–2025 con **93 meses OOS / 31 folds**, el modelo cae a **CAGR 2.47%, Sharpe 0.247, MDD -24.01%**, contra **SPY 13.58%** y **60/40 9.00%**.

Este resultado no se debe maquillar: con el umbral del proyecto (>10% anualizado), la configuración actual **falla empíricamente** en el periodo largo.

## Diagnóstico probable

### 1. Sobreajuste de ventana/regímenes

El piloto 2021–2025 captura una ventana corta y posiblemente favorable a ciertos estilos/sectores. La extensión 2015–2025 incluye regímenes más diversos: expansión 2016–2019, crisis COVID, inflación/tasas 2022, concentración tecnológica 2023–2024. Un ELECTRE+MaxSharpe puede seleccionar estilos que no generalizan.

### 2. Universo current-active sesgado

El universo actual no es PIT. Esto contamina ambos resultados, pero de forma difícil de predecir: puede excluir ETFs muertos débiles y también excluir fondos que existieron en la época pero no sobreviven. Por tanto, la caída de performance **no queda explicada ni resuelta** hasta usar un universo PIT.

### 3. Optimización MaxSharpe inestable

MaxSharpe en ventanas históricas pequeñas puede concentrarse en activos con retornos pasados altos y covarianzas subestimadas. Esto genera rotación/concentración y mala respuesta a cambio de régimen.

### 4. Criterios ELECTRE pueden estar seleccionando “calidad histórica” no robusta

Si los criterios derivan de retorno/volatilidad/drawdown pasados, ELECTRE puede reforzar momentum/low-vol ex post sin controlar exposición macro, duración, commodities, USD, beta, concentración temática o correlación con benchmark.

### 5. Falta de controles de exposición y atribución por fold

El MDD -24% sugiere exposición concentrada o fragilidad de régimen. Antes de tunear pesos, se debe mirar `fold_performance.csv`, `fold_holdings_attribution.csv`, turnover y category exposures.

## Qué NO hacer

- No volver a optimizar hiperparámetros hasta recuperar CAGR >10% sin resolver data PIT.
- No declarar “thesis-grade” por tener 93 meses OOS si el universo sigue current-active.
- No ocultar el resultado largo; es la evidencia más honesta contra overfitting.

## Qué hacer

1. Corregir primero el universo PIT.
2. Mantener el resultado 2015–2025 como baseline negativo congelado.
3. Ejecutar diagnósticos por fold y holdings: ¿pocos folds explican la caída o hay underperformance persistente?
4. Comparar estrategias simples en el mismo universo PIT: equal-weight, min-var, max-Sharpe sin ELECTRE, SPY, 60/40.
5. Probar mejoras solo preregistradas: límites de exposición, turnover penalty, robust covariance, target volatility, drawdown veto, benchmark-aware constraints.

## Interpretación de tesis

Una tesis defendible no necesita prometer que la estrategia vence a SPY en todos los periodos. Puede contribuir con:

- una arquitectura reproducible ELECTRE Tri + optimización + walk-forward;
- un tratamiento explícito de universe bias;
- evidencia de que un piloto favorable no generaliza al periodo largo;
- diagnóstico de por qué falla y cómo controlar riesgos.

Pero si la estrategia final sigue en 2.47% CAGR, la contribución debe ser metodológica/diagnóstica, no “modelo ganador”.
