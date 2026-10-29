from __future__ import annotations

import pandas as pd


def _ticker_index(frame: pd.DataFrame) -> pd.Index:
    if "ticker" in frame.columns:
        return pd.Index(frame["ticker"], name="ticker")
    return pd.Index(frame.index, name=frame.index.name or "ticker")


def filter_by_history(
    coverage: pd.DataFrame,
    min_coverage_pct: float,
    min_first_valid: str | None = None,
) -> pd.Series:
    """Return tickers with enough non-missing historical price coverage.

    ``coverage`` is expected to be the per-ticker audit table produced by the downloader,
    including ``coverage_pct`` and optionally ``first_valid``. Missing first-valid dates are
    ineligible when a first-valid cutoff is required; they are never converted to zeros.
    """
    tickers = _ticker_index(coverage)
    coverage_pct = pd.to_numeric(coverage["coverage_pct"], errors="coerce")
    coverage_pct.index = tickers
    eligible = coverage_pct >= min_coverage_pct

    if min_first_valid is not None:
        first_valid = pd.to_datetime(coverage["first_valid"], errors="coerce")
        first_valid.index = tickers
        eligible &= first_valid.notna() & (first_valid <= pd.Timestamp(min_first_valid))

    eligible = eligible.fillna(False).astype(bool)
    eligible.name = "history_eligible"
    return eligible


def compute_avg_dollar_volume(prices: pd.DataFrame, volume: pd.DataFrame) -> pd.Series:
    """Compute per-ticker average price * volume on shared rows/columns.

    Prices and volumes are aligned by index and ticker. Missing values stay missing and are
    skipped by pandas' mean; this intentionally avoids ``fillna(0.0)`` because that would
    simulate tradability on dates without an observed price or volume.
    """
    common_index = prices.index.intersection(volume.index)
    common_columns = prices.columns.intersection(volume.columns)
    dollar_volume = prices.loc[common_index, common_columns] * volume.loc[
        common_index, common_columns
    ]
    avg_dollar_volume = dollar_volume.mean(axis=0, skipna=True)
    avg_dollar_volume.name = "avg_dollar_volume"
    return avg_dollar_volume


def filter_by_liquidity(
    avg_dollar_volume: pd.Series,
    min_avg_dollar_volume: float,
) -> pd.Series:
    """Return tickers whose average dollar volume meets the threshold."""
    eligible = avg_dollar_volume >= min_avg_dollar_volume
    eligible = eligible.fillna(False).astype(bool)
    eligible.name = "liquidity_eligible"
    return eligible
