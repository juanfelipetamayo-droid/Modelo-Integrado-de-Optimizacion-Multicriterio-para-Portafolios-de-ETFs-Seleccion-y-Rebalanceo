from __future__ import annotations

import numpy as np
import pandas as pd

from etf_optimizer.optimization.portfolio import (
    equal_weight,
    max_sharpe_weights,
    min_variance_weights,
)
from etf_optimizer.optimization.rebalancing import compute_turnover, apply_transaction_cost


def test_equal_weight_respects_full_investment():
    weights = equal_weight(["A", "B", "C"])
    assert np.isclose(weights.sum(), 1.0)
    assert all(weights == 1 / 3)


def test_min_variance_weights_sum_to_one_and_are_long_only():
    cov = pd.DataFrame([[0.04, 0.01], [0.01, 0.09]], index=["A", "B"], columns=["A", "B"])
    weights = min_variance_weights(cov)
    assert np.isclose(weights.sum(), 1.0, atol=1e-6)
    assert (weights >= -1e-8).all()


def test_max_sharpe_weights_prefer_higher_risk_adjusted_asset():
    expected_returns = pd.Series({"A": 0.12, "B": 0.04})
    cov = pd.DataFrame([[0.04, 0.0], [0.0, 0.04]], index=["A", "B"], columns=["A", "B"])
    weights = max_sharpe_weights(expected_returns, cov, risk_free_rate=0.0)
    assert np.isclose(weights.sum(), 1.0, atol=1e-6)
    assert weights["A"] > weights["B"]


def test_turnover_and_transaction_cost_reduce_returns():
    old = pd.Series({"A": 0.5, "B": 0.5})
    new = pd.Series({"A": 0.8, "B": 0.2})
    turnover = compute_turnover(old, new)
    assert np.isclose(turnover, 0.3)
    assert apply_transaction_cost(gross_return=0.02, turnover=turnover, cost_bps=10) < 0.02
