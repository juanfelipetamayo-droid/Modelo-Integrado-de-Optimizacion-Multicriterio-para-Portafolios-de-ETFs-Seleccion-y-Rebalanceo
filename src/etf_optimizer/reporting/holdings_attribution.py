from __future__ import annotations

import pandas as pd


def _fold_slices(length: int, test_size: int) -> list[tuple[int, int]]:
    return [(start, min(start + test_size, length)) for start in range(0, length, test_size)]


def _metadata_by_ticker(metadata: pd.DataFrame | None) -> pd.DataFrame:
    if metadata is None or metadata.empty:
        return pd.DataFrame(index=pd.Index([], name="ticker"))
    frame = metadata.copy()
    if "ticker" not in frame.columns:
        frame = frame.reset_index().rename(columns={frame.index.name or "index": "ticker"})
    frame["ticker"] = frame["ticker"].astype(str)
    return frame.drop_duplicates("ticker").set_index("ticker")


def fold_holdings_attribution_table(
    returns: pd.DataFrame,
    effective_weights: pd.DataFrame,
    *,
    test_size: int,
    metadata: pd.DataFrame | None = None,
    min_abs_weight: float = 1e-8,
) -> pd.DataFrame:
    """Attribute OOS fold returns to weighted ETF holdings.

    Contribution is approximated as the sum of ``effective_weight[ticker] *
    return[ticker]`` across each OOS fold. This additive approximation is meant
    for diagnosis and ranking of damaging/beneficial holdings, not exact
    geometric performance decomposition.
    """
    if test_size <= 0:
        raise ValueError("test_size must be positive")
    if min_abs_weight < 0.0:
        raise ValueError("min_abs_weight must be nonnegative")

    common_index = returns.index.intersection(effective_weights.index)
    common_columns = returns.columns.intersection(effective_weights.columns)
    if len(common_index) == 0 or len(common_columns) == 0:
        return pd.DataFrame(
            columns=[
                "fold",
                "ticker",
                "start_date",
                "end_date",
                "n_observations",
                "avg_weight",
                "max_weight",
                "asset_cumulative_return",
                "total_contribution",
                "mean_monthly_contribution",
            ]
        )

    aligned_returns = returns.loc[common_index, common_columns].astype("float64")
    aligned_weights = effective_weights.loc[common_index, common_columns].astype("float64").fillna(0.0)
    meta = _metadata_by_ticker(metadata)
    rows: list[dict[str, float | int | str]] = []

    for fold_idx, (start, end) in enumerate(_fold_slices(len(common_index), test_size), start=1):
        fold_index = common_index[start:end]
        fold_returns = aligned_returns.loc[fold_index]
        fold_weights = aligned_weights.loc[fold_index]
        contributions = fold_weights * fold_returns
        for ticker in common_columns:
            weights = fold_weights[ticker]
            if float(weights.abs().max()) <= min_abs_weight:
                continue
            asset_returns = fold_returns[ticker].dropna()
            row: dict[str, float | int | str] = {
                "fold": int(fold_idx),
                "ticker": str(ticker),
                "start_date": fold_index[0].strftime("%Y-%m-%d"),
                "end_date": fold_index[-1].strftime("%Y-%m-%d"),
                "n_observations": int(len(fold_index)),
                "avg_weight": float(weights.mean()),
                "max_weight": float(weights.max()),
                "asset_cumulative_return": float((1.0 + asset_returns).prod() - 1.0),
                "total_contribution": float(contributions[ticker].sum()),
                "mean_monthly_contribution": float(contributions[ticker].mean()),
            }
            if ticker in meta.index:
                for col, value in meta.loc[ticker].items():
                    if col not in row:
                        row[col] = value
            rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(["fold", "total_contribution"], ascending=[True, True]).reset_index(drop=True)
