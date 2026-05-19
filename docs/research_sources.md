# Research sources and formulas

This project is intentionally tied to academic and methodological sources so the implementation can be defended in a thesis.

## Portfolio selection and optimization

- **Markowitz, H. (1952). _Portfolio Selection_. Journal of Finance, 7(1), 77–91.**  
  Source for mean-variance portfolio theory: maximize expected return for a chosen variance level or minimize variance under return/full-investment constraints.

- **Sharpe, W. F. (1966). _Mutual Fund Performance_. Journal of Business, 39(1), 119–138.**  
  Source for the reward-to-variability ratio implemented as the Sharpe ratio.

- **Ledoit, O. and Wolf, M. (2004). _A well-conditioned estimator for large-dimensional covariance matrices_. Journal of Multivariate Analysis, 88(2), 365–411.**  
  Source for shrinkage covariance estimation used to reduce optimizer instability.

- **DeMiguel, V., Garlappi, L. and Uppal, R. (2009). _Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?_ Review of Financial Studies, 22(5), 1915–1953.**  
  Justifies including equal-weight as a strong baseline/benchmark.

- **Sortino, F. A. and Price, L. N. (1994). _Performance Measurement in a Downside Risk Framework_. Journal of Investing, 3(3), 59–64.**  
  Source for downside-risk performance measurement.

## Multicriteria decision aiding and ELECTRE

- **Roy, B. (1991). _The outranking approach and the foundations of ELECTRE methods_. Theory and Decision, 31, 49–73.**  
  Conceptual basis for outranking, concordance and discordance.

- **Yu, W. (1992). _ELECTRE TRI: Aspects méthodologiques et manuel d'utilisation_. Université Paris-Dauphine.**  
  Foundational ELECTRE Tri sorting method for assigning alternatives to ordered categories.

- **Mousseau, V., Slowinski, R. and Zielniewicz, P. (2000). _A user-oriented implementation of the ELECTRE-TRI method integrating preference elicitation support_. Computers & Operations Research, 27(7–8), 757–777.**  
  Practical implementation details for ELECTRE Tri and preference elicitation.

- **Figueira, J., Greco, S. and Ehrgott, M. (eds.) (2005). _Multiple Criteria Decision Analysis: State of the Art Surveys_. Springer.**  
  Reference text for MCDA theory and robustness/sensitivity analysis.

## Financial MCDA applications

- **Xidonas, P., Mavrotas, G. and Psarras, J. (2009). _A multicriteria methodology for equity selection using financial analysis_. Computers & Operations Research, 36(12), 3187–3203.**  
  Directly relevant precedent for applying ELECTRE-style multicriteria methods to asset selection.

- **Spronk, J., Steuer, R. E. and Zopounidis, C. (2005). _Multicriteria decision aid/analysis in finance_. In Multiple Criteria Decision Analysis: State of the Art Surveys.**  
  General reference for MCDA in financial decision-making.

## Backtesting and validation

- **Bailey, D. H., Borwein, J., López de Prado, M. and Zhu, Q. J. (2014). _The Probability of Backtest Overfitting_. Journal of Computational Finance.**  
  Motivation for walk-forward validation, overfitting controls and caution around repeated strategy tuning.

- **López de Prado, M. (2018). _Advances in Financial Machine Learning_. Wiley.**  
  Practical source for avoiding leakage/look-ahead bias in financial backtests.

## Implemented formulas

### Simple return

```text
r_t = P_t / P_{t-1} - 1
```

### CAGR / annualized geometric return

```text
CAGR = Π(1 + r_t)^(periods_per_year / T) - 1
```

### Annualized volatility

```text
σ_ann = std(r_t) × sqrt(periods_per_year)
```

### Sharpe ratio

```text
Sharpe = mean(r_t - rf/periods_per_year) × periods_per_year / σ_ann
```

### Maximum drawdown

```text
wealth_t = Π(1 + r_t)
drawdown_t = wealth_t / max(wealth_0..wealth_t) - 1
MDD = min(drawdown_t)
```

### ELECTRE Tri credibility

For alternative `a`, profile `b`, criterion `j`:

```text
C(a,b) = Σ w_j c_j(a,b)
σ(a,b) = C(a,b) × Π_{j: d_j > C(a,b)} [(1 - d_j(a,b)) / (1 - C(a,b))]
```

where `c_j` is partial concordance and `d_j` is partial discordance/veto.

### Turnover and transaction cost

```text
turnover = 0.5 × Σ |w_new_i - w_old_i|
net_return = gross_return - turnover × cost_bps / 10000
```
