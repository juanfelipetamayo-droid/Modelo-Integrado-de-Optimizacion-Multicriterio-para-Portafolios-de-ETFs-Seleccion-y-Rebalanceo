from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.backtesting.metrics import performance_summary


def build_strategy_comparison(
    portfolio_returns: dict[str, pd.Series],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Build a comparison table of performance metrics across strategies."""
    rows: list[dict[str, float]] = []
    for name, returns in portfolio_returns.items():
        if returns.dropna().empty:
            continue
        metrics = performance_summary(returns, risk_free_rate, periods_per_year)
        metrics["strategy"] = name
        rows.append(metrics)

    return pd.DataFrame(rows).set_index("strategy") if rows else pd.DataFrame()


def build_equity_curves(
    portfolio_returns: dict[str, pd.Series],
    initial_capital: float = 1.0,
) -> pd.DataFrame:
    """Build equity curves from return series."""
    curves: dict[str, pd.Series] = {}
    for name, returns in portfolio_returns.items():
        if returns.dropna().empty:
            continue
        curves[name] = (1.0 + returns).cumprod() * initial_capital
    return pd.DataFrame(curves)


def build_drawdowns(
    portfolio_returns: dict[str, pd.Series],
) -> pd.DataFrame:
    """Build drawdown series from return series."""
    curves = build_equity_curves(portfolio_returns)
    running_max = curves.cummax()
    return curves / running_max - 1.0


def write_comparison_tables(
    strategy_comparison: pd.DataFrame,
    equity_curves: pd.DataFrame,
    drawdowns: pd.DataFrame,
    out_dir: str | Path,
) -> dict[str, Path]:
    """Write comparison tables to CSV files."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "strategy_comparison": out / "strategy_comparison.csv",
        "equity_curves": out / "equity_curves.csv",
        "drawdowns": out / "drawdowns.csv",
    }
    strategy_comparison.to_csv(paths["strategy_comparison"])
    equity_curves.to_csv(paths["equity_curves"])
    drawdowns.to_csv(paths["drawdowns"])
    return paths
