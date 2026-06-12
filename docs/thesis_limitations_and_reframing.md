# Limitaciones y reencuadre de tesis

## Limitaciones actuales

1. **Universo no point-in-time**
   - El universo current-active introduce survivorship/lookahead bias.
   - No se puede afirmar que los resultados 2015–2025 son survivorship-bias-free.

2. **Acceso CRSP/WRDS negado**
   - La fuente académica ideal no está disponible.
   - Se requiere alternativa: Norgate+SEC o SEC-only.

3. **Performance OOS insuficiente**
   - La corrida larga reporta 2.47% CAGR y Sharpe 0.247, inferior a SPY y 60/40.
   - Con el objetivo >10%, la estrategia actual falla empíricamente.

4. **Total return/delisting treatment pendiente**
   - Sin base comercial validada, los retornos de ETFs desaparecidos y liquidaciones pueden faltar.

5. **Riesgo de múltiples pruebas**
   - Cada ajuste posterior aumenta riesgo de backtest overfitting si no hay preregistro y holdout disciplinado.

## Reencuadre recomendado

### Título/claim fuerte pero honesto

“Modelo reproducible de selección multicriterio ELECTRE Tri y optimización walk-forward para portafolios de ETFs con control explícito de sesgo de universo y diagnóstico de generalización”.

### Contribución principal

No vender la tesis como “estrategia que vence a SPY”, sino como:

- integración metodológica ELECTRE Tri + optimización + backtesting walk-forward;
- arquitectura de datos PIT pública/comercial auditable;
- evidencia empírica de que pilotos cortos pueden fallar al extender OOS;
- marco de diagnóstico de concentración, rotación, drawdown y sesgo de universo.

### Claims permitidos por ruta

| Ruta | Claim permitido |
|---|---|
| Universo actual + yfinance | Evidencia piloto / desarrollo; no survivor-bias-free |
| SEC-only + precios públicos | Aproximación pública point-in-time con cobertura y limitaciones reportadas |
| Norgate+SEC | Backtest comercial PIT validado con fuente oficial, si la cobertura de ETF/ETN delisted y ajustes se verifican |
| Institutional vendor + SEC | Evidencia más fuerte si licencia académica permite live+dead funds y publicación metodológica |

## Recomendación para defensa

Decir explícitamente:

> “El piloto corto tuvo desempeño alto, pero la validación extendida 2015–2025 mostró que la configuración no generaliza. Por eso la tesis se reorienta a resolver el sesgo de universo y a producir una evaluación robusta, no a maximizar una métrica puntual sobre un universo current-active.”

Esto es académicamente más defendible que optimizar hasta recuperar 18% CAGR.
