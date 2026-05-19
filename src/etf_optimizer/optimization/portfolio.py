from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def equal_weight(assets: list[str] | pd.Index) -> pd.Series:
    assets = list(assets)
    if not assets:
        raise ValueError("assets cannot be empty")
    return pd.Series(np.repeat(1.0 / len(assets), len(assets)), index=assets, dtype=float)


def _bounds(n: int, max_weight: float | None) -> list[tuple[float, float]]:
    """Long-only bounds; relax max_weight when it would make full investment infeasible."""
    upper = 1.0 if max_weight is None or max_weight * n < 1.0 else max_weight
    return [(0.0, upper) for _ in range(n)]


def _validate_covariance(cov: pd.DataFrame) -> pd.DataFrame:
    if cov.shape[0] != cov.shape[1]:
        raise ValueError("covariance matrix must be square")
    return cov.astype(float)


def min_variance_weights(cov: pd.DataFrame, max_weight: float | None = None) -> pd.Series:
    """Long-only global minimum variance portfolio.

    Markowitz (1952) frames portfolio selection as balancing expected return and
    variance; this routine implements the minimum-variance corner under practical
    long-only/full-investment constraints.
    """
    cov = _validate_covariance(cov)
    assets = cov.index
    n = len(assets)
    x0 = np.repeat(1.0 / n, n)
    matrix = cov.to_numpy()

    def objective(w: np.ndarray) -> float:
        return float(w @ matrix @ w)

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=_bounds(n, max_weight),
        constraints=[{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}],
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(f"min variance optimization failed: {result.message}")
    weights = np.clip(result.x, 0, 1)
    weights = weights / weights.sum()
    return pd.Series(weights, index=assets)


def max_sharpe_weights(
    expected_returns: pd.Series,
    cov: pd.DataFrame,
    risk_free_rate: float = 0.0,
    max_weight: float | None = None,
) -> pd.Series:
    """Long-only tangency portfolio maximizing the Sharpe ratio."""
    cov = _validate_covariance(cov).loc[expected_returns.index, expected_returns.index]
    assets = expected_returns.index
    n = len(assets)
    x0 = np.repeat(1.0 / n, n)
    mu = expected_returns.to_numpy(dtype=float)
    matrix = cov.to_numpy(dtype=float)

    def neg_sharpe(w: np.ndarray) -> float:
        ret = float(w @ mu - risk_free_rate)
        vol = float(np.sqrt(w @ matrix @ w))
        if np.isclose(vol, 0.0):
            return 1e6
        return -ret / vol

    result = minimize(
        neg_sharpe,
        x0,
        method="SLSQP",
        bounds=_bounds(n, max_weight),
        constraints=[{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}],
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(f"max Sharpe optimization failed: {result.message}")
    weights = np.clip(result.x, 0, 1)
    weights = weights / weights.sum()
    return pd.Series(weights, index=assets)


def sample_covariance(returns: pd.DataFrame, periods_per_year: int = 252) -> pd.DataFrame:
    return returns.cov() * periods_per_year


def ledoit_wolf_covariance(returns: pd.DataFrame, periods_per_year: int = 252) -> pd.DataFrame:
    """Ledoit-Wolf shrinkage covariance estimator.

    Ledoit and Wolf (2004) propose shrinkage to improve covariance conditioning for
    portfolio optimization with many noisy assets.
    """
    from sklearn.covariance import LedoitWolf

    clean = returns.dropna(axis=0, how="any")
    estimator = LedoitWolf().fit(clean.to_numpy())
    return pd.DataFrame(
        estimator.covariance_ * periods_per_year,
        index=returns.columns,
        columns=returns.columns,
    )
