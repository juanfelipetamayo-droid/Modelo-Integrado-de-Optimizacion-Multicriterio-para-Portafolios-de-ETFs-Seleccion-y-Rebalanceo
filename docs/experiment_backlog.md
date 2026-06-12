# Backlog de experimentos

## Prioridad A — desbloqueo de datos

1. **SEC annual snapshots 2015–2025**
   - Objetivo: reconstruir universo aproximado PIT.
   - Métrica: candidatos ETF por año, precisión manual, cobertura de precio.

2. **SEC vs Nasdaq current overlap**
   - Objetivo: medir cuánto del universo actual existía legalmente por año.
   - Métrica: Jaccard por año, tickers actuales no observables antes de fecha.

3. **N-PORT/N-CEN validation 2019Q4+**
   - Objetivo: validar existencia, series/class y datos reportados con lag.
   - Métrica: % de candidatos con filings trazables.

4. **Norgate coverage pilot (solo si se aprueba pago/trial)**
   - Objetivo: verificar ETFs/ETNs delisted, adjusted close, dividends/distributions.
   - Métrica: cobertura 2015–2025, dead ETF count, mapping SEC.

## Prioridad B — performance diagnosis

5. **Fold attribution**
   - Encontrar peores folds y top detractores.
   - Métrica: contribución por ETF/fold, worst-fold flag.

6. **Universe sensitivity**
   - Comparar `static_current`, `static_start`, `point_in_time_sec_public`, `point_in_time_norgate_sec`.
   - Métrica: CAGR/Sharpe/MDD y turnover por universo.

7. **Rebalance semantics**
   - Calendar vs threshold vs buy-and-hold drift.
   - Métrica: turnover, costs, event count, drawdown.

8. **Optimization stability**
   - MaxSharpe vs min-var vs equal-weight vs risk parity vs constrained MaxSharpe.
   - Métrica: fold-level Sharpe/MDD, concentration HHI.

## Prioridad C — robustez económica

9. **Category exposure caps**
   - Limitar commodities, thematic, regional, leveraged/inverse, duration.
   - Métrica: category exposure report, performance delta.

10. **Turnover/cost sensitivity**
    - 0/5/10/25/50 bps.
    - Métrica: net CAGR and drawdown.

11. **Robust covariance / shrinkage**
    - Ledoit-Wolf/OAS/hierarchical risk controls.
    - Métrica: stability of weights and OOS performance.

12. **Benchmark-aware constraints**
    - Beta cap, tracking-error cap, drawdown veto.
    - Métrica: downside capture and MDD.

## Prioridad D — tesis y validación estadística

13. **Paired bootstrap vs SPY/60-40**
    - Métrica: CI de diferencias CAGR/Sharpe/MDD.

14. **Preregistration log**
    - Registrar hipótesis antes de correr cada variante.

15. **Ablation study**
    - Sin ELECTRE, sin optimizer, sin category caps, sin recategorization.

16. **Claim boundary table**
    - Traducir cada resultado a claim permitido: pilot, public approximate PIT, commercial PIT.
