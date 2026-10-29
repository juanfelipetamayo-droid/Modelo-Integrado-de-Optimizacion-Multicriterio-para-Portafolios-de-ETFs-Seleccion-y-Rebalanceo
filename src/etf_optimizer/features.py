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


def tracking_error(
    returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """Annualized tracking error against an aligned benchmark return series."""
    aligned = pd.concat([pd.Series(returns), pd.Series(benchmark_returns)], axis=1).dropna()
    if aligned.shape[0] < 2:
        return np.nan
    active = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    return float(active.std(ddof=1) * np.sqrt(periods_per_year))


def _benchmark_for_ticker(
    ticker: str,
    benchmark_returns: pd.Series | pd.DataFrame | None,
    benchmark_map: dict[str, str] | None,
) -> pd.Series | None:
    if benchmark_returns is None:
        return None
    if isinstance(benchmark_returns, pd.Series):
        return benchmark_returns
    if benchmark_map and ticker in benchmark_map and benchmark_map[ticker] in benchmark_returns.columns:
        return benchmark_returns[benchmark_map[ticker]]
    if ticker in benchmark_returns.columns:
        return benchmark_returns[ticker]
    if benchmark_returns.shape[1] == 1:
        return benchmark_returns.iloc[:, 0]
    return None


def _expense_ratio_for_ticker(ticker: str, expense_ratios: pd.Series | dict[str, float] | pd.DataFrame | None) -> float:
    if expense_ratios is None:
        return np.nan
    if isinstance(expense_ratios, dict):
        return float(expense_ratios.get(ticker, np.nan))
    if isinstance(expense_ratios, pd.Series):
        return float(expense_ratios.get(ticker, np.nan))
    if "ticker" in expense_ratios.columns and "expense_ratio" in expense_ratios.columns:
        ratios = expense_ratios.drop_duplicates("ticker").set_index("ticker")["expense_ratio"]
        return float(ratios.get(ticker, np.nan))
    if ticker in expense_ratios.index and "expense_ratio" in expense_ratios.columns:
        return float(expense_ratios.loc[ticker, "expense_ratio"])
    return np.nan


def compute_feature_table(
    prices: pd.DataFrame,
    volume: pd.DataFrame | None = None,
    benchmark_returns: pd.Series | pd.DataFrame | None = None,
    benchmark_map: dict[str, str] | None = None,
    expense_ratios: pd.Series | dict[str, float] | pd.DataFrame | None = None,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Create ETF-level feature table from adjusted prices and optional volume.

    Result columns: cagr, volatility, sharpe, sortino, max_drawdown and
    (when volume is provided) avg_dollar_volume.

    Tracking error is computed when benchmark returns are supplied. Expense
    ratio is attached when external fund-level values are supplied.

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
            avg_dollar_volume = float((aligned_price * volume[ticker]).dropna().mean())
            rows[ticker]["avg_dollar_volume"] = avg_dollar_volume
            # Thesis wording uses "liquidez" as a criterion; the auditable
            # implementation proxy is average dollar volume.
            rows[ticker]["liquidity"] = avg_dollar_volume
        benchmark = _benchmark_for_ticker(ticker, benchmark_returns, benchmark_map)
        if benchmark is not None:
            rows[ticker]["tracking_error"] = tracking_error(r, benchmark, periods_per_year)
        if expense_ratios is not None:
            rows[ticker]["expense_ratio"] = _expense_ratio_for_ticker(ticker, expense_ratios)
    return pd.DataFrame.from_dict(rows, orient="index")
