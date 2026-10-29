from __future__ import annotations

import numpy as np
import pandas as pd

from etf_optimizer.features import annualized_return, annualized_volatility, max_drawdown, sharpe_ratio, sortino_ratio


def calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    dd = abs(max_drawdown(returns))
    if np.isclose(dd, 0.0):
        return np.nan
    return float(annualized_return(returns, periods_per_year) / dd)


def performance_summary(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> dict[str, float]:
    """Core performance metrics used in academic portfolio evaluation."""
    r = pd.Series(returns).dropna()
    return {
        "cagr": annualized_return(r, periods_per_year),
        "volatility": annualized_volatility(r, periods_per_year),
        "sharpe": sharpe_ratio(r, risk_free_rate, periods_per_year),
        "sortino": sortino_ratio(r, risk_free_rate, periods_per_year),
        "max_drawdown": max_drawdown(r),
        "calmar": calmar_ratio(r, periods_per_year),
    }
