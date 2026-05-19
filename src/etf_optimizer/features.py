from __future__ import annotations

import numpy as np
import pandas as pd


def returns_from_prices(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Compute simple returns from adjusted prices."""
    return prices.sort_index().pct_change().dropna(how="all")


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Geometric annualized return/CAGR from periodic returns.

    Based on the standard compound-return convention used in portfolio evaluation.
    """
    r = pd.Series(returns).dropna()
    if r.empty:
        return np.nan
    growth = float((1.0 + r).prod())
    years = len(r) / periods_per_year
    if years <= 0 or growth <= 0:
        return np.nan
    return growth ** (1.0 / years) - 1.0


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Annualized standard deviation of periodic returns."""
    r = pd.Series(returns).dropna()
    if len(r) < 2:
        return 0.0
    return float(r.std(ddof=1) * np.sqrt(periods_per_year))


def downside_deviation(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    """Annualized downside deviation used by the Sortino ratio."""
    r = pd.Series(returns).dropna()
    mar = risk_free_rate / periods_per_year
    downside = np.minimum(r - mar, 0.0)
    if len(downside) == 0:
        return np.nan
    return float(np.sqrt(np.mean(np.square(downside))) * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    """Annualized Sharpe ratio, following Sharpe's reward-to-variability measure."""
    r = pd.Series(returns).dropna()
    if r.empty:
        return np.nan
    excess = r - risk_free_rate / periods_per_year
    vol = annualized_volatility(excess, periods_per_year)
    if np.isclose(vol, 0.0):
        return np.nan
    return float(excess.mean() * periods_per_year / vol)


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    """Sortino ratio using downside deviation rather than total volatility."""
    r = pd.Series(returns).dropna()
    if r.empty:
        return np.nan
    dd = downside_deviation(r, risk_free_rate, periods_per_year)
    if np.isclose(dd, 0.0):
        return np.nan
    return float((r.mean() * periods_per_year - risk_free_rate) / dd)


def max_drawdown(returns: pd.Series) -> float:
    """Maximum peak-to-trough loss of a return series."""
    r = pd.Series(returns).dropna()
    if r.empty:
        return np.nan
    wealth = (1.0 + r).cumprod()
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1.0
    return float(drawdown.min())


def compute_feature_table(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None = None,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Create ETF-level feature table from adjusted prices and optional volume.

    Result columns: cagr, volatility, sharpe, sortino, max_drawdown and
    (when volume is provided) avg_dollar_volume.

    Tracking error and expense ratio are not computed here — tracking error
    needs a benchmark series and expense ratio requires external fund data.
    These can be added as separate columns before passing to ElectreTri.

    ELECTRE criteria later declares whether each column is benefit (max) or cost (min).
    """
    returns = returns_from_prices(prices)
    rows: dict[str, dict[str, float]] = {}
    for ticker in prices.columns:
        r = returns[ticker].dropna()
        rows[ticker] = {
            "cagr": annualized_return(r, periods_per_year),
            "volatility": annualized_volatility(r, periods_per_year),
            "sharpe": sharpe_ratio(r, risk_free_rate, periods_per_year),
            "sortino": sortino_ratio(r, risk_free_rate, periods_per_year),
            "max_drawdown": max_drawdown(r),
        }
        if volume is not None and ticker in volume:
            aligned_price = prices[ticker].reindex(volume.index)
            rows[ticker]["avg_dollar_volume"] = float((aligned_price * volume[ticker]).dropna().mean())
    return pd.DataFrame.from_dict(rows, orient="index")
