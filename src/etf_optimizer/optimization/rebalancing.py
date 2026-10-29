from __future__ import annotations

import pandas as pd


def compute_turnover(old_weights: pd.Series, new_weights: pd.Series) -> float:
    """One-way portfolio turnover: 0.5 * sum(abs(delta weights))."""
    aligned_old, aligned_new = old_weights.align(new_weights, join="outer", fill_value=0.0)
    return float(0.5 * (aligned_new - aligned_old).abs().sum())


def apply_transaction_cost(gross_return: float, turnover: float, cost_bps: float) -> float:
    """Subtract proportional transaction costs from a gross period return."""
    return float(gross_return - turnover * cost_bps / 10_000.0)
