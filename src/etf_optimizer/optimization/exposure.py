from __future__ import annotations

import re

import pandas as pd


_BUCKET_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "commodities",
        (
            "commodity",
            "commodities",
            "corn",
            "sugar",
            "oil",
            "natural gas",
            "gold",
            "silver",
            "wheat",
            "soybean",
            "copper",
            "metals",
        ),
    ),
    ("greater_china", ("china", "chinese", "chinext", "hong kong", "taiwan", "msci china")),
    ("natural_resources", ("water", "resources", "miners", "mining", "energy", "timber")),
    ("thematic", ("future", "vehicles", "technology", "robotics", "innovation", "thematic", "solar", "clean")),
    ("fixed_income", ("bond", "treasury", "income", "aggregate", "municipal", "corporate bond")),
    ("broad_equity", ("s&p 500", "total stock", "large cap", "large-cap", "broad market", "russell 3000")),
)


def classify_etf_risk_bucket(ticker: str, name: str | None = None, category: str | None = None) -> str:
    """Classify an ETF into a transparent risk bucket from public metadata text.

    The classifier is deliberately rule-based so the thesis appendix can audit each
    assignment without relying on a black-box commercial taxonomy.
    """
    text = " ".join(part for part in [ticker, name or "", category or ""] if part).lower()
    text = re.sub(r"\s+", " ", text)
    for bucket, keywords in _BUCKET_RULES:
        if any(keyword in text for keyword in keywords):
            return bucket
    return "other"


def _metadata_buckets(metadata: pd.DataFrame, tickers: pd.Index) -> pd.Series:
    if "ticker" not in metadata.columns:
        raise ValueError("metadata must include a ticker column")
    meta = metadata.drop_duplicates("ticker").set_index("ticker")
    rows: dict[str, str] = {}
    for ticker in tickers:
        if ticker in meta.index:
            row = meta.loc[ticker]
            name = str(row.get("name", "")) if "name" in meta.columns else ""
            category = str(row.get("category", "")) if "category" in meta.columns else ""
        else:
            name = ""
            category = ""
        rows[str(ticker)] = classify_etf_risk_bucket(str(ticker), name, category)
    return pd.Series(rows, name="risk_bucket")


def apply_group_exposure_cap(weights: pd.Series, metadata: pd.DataFrame, *, cap: float | None) -> pd.Series:
    """Cap exposure to any rule-based risk bucket and redistribute excess pro-rata.

    This is a post-optimization portfolio hygiene control. It does not alter the
    ELECTRE classification itself; it only prevents the optimizer from translating a
    valid MCDA selection into an impractical thematic/commodity concentration.
    """
    weights = weights.astype(float).clip(lower=0.0)
    if weights.sum() <= 0:
        raise ValueError("weights must have positive gross exposure")
    weights = weights / weights.sum()
    if cap is None:
        return weights
    if not 0.0 < cap <= 1.0:
        raise ValueError("cap must be in (0, 1]")

    buckets = _metadata_buckets(metadata, weights.index)
    active_groups = buckets[weights > 0.0].unique().tolist()
    if cap * len(active_groups) < 1.0 - 1e-12:
        raise ValueError("infeasible group exposure cap for the active category count")

    capped = weights.copy()
    for _ in range(100):
        exposures = capped.groupby(buckets).sum()
        over = exposures[exposures > cap + 1e-12]
        if over.empty:
            break
        excess = 0.0
        for group, exposure in over.items():
            group_assets = buckets[buckets == group].index
            group_weight = capped.loc[group_assets].sum()
            if group_weight <= 0:
                continue
            scale = cap / group_weight
            excess += float(capped.loc[group_assets].sum() - capped.loc[group_assets].sum() * scale)
            capped.loc[group_assets] = capped.loc[group_assets] * scale
        under_groups = capped.groupby(buckets).sum()
        eligible_groups = under_groups[under_groups < cap - 1e-12].index
        eligible_assets = buckets[buckets.isin(eligible_groups)].index
        if excess <= 1e-12 or len(eligible_assets) == 0:
            break
        capacity = cap - under_groups.loc[eligible_groups]
        capacity_by_asset = buckets.loc[eligible_assets].map(capacity).astype(float)
        # Redistribute first to existing non-capped weights; if all zero, use capacity.
        base = capped.loc[eligible_assets].clip(lower=0.0)
        if base.sum() <= 1e-12:
            base = capacity_by_asset
        allocation = base / base.sum() * excess
        allocation = pd.concat([allocation, capacity_by_asset], axis=1).min(axis=1)
        capped.loc[eligible_assets] += allocation
        leftover = 1.0 - capped.sum()
        if abs(leftover) > 1e-10 and capacity_by_asset.sum() > 0:
            capped.loc[eligible_assets] += capacity_by_asset / capacity_by_asset.sum() * leftover
    capped = capped.clip(lower=0.0)
    capped = capped / capped.sum()
    final_exposures = capped.groupby(buckets).sum()
    if (final_exposures > cap + 1e-8).any():
        raise RuntimeError("failed to satisfy group exposure cap")
    return capped


def category_exposure_table(weights: pd.Series | pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    """Return risk-bucket exposure table for one weight vector or a weight time series."""
    if isinstance(weights, pd.Series):
        vector = weights.astype(float)
        buckets = _metadata_buckets(metadata, vector.index)
        table = vector.groupby(buckets).sum().rename("weight").reset_index()
        return table.sort_values("weight", ascending=False).reset_index(drop=True)

    rows: list[dict[str, object]] = []
    buckets = _metadata_buckets(metadata, weights.columns)
    for date, row in weights.iterrows():
        exposures = row.astype(float).groupby(buckets).sum()
        for bucket, weight in exposures.items():
            rows.append({"date": date, "risk_bucket": bucket, "weight": float(weight)})
    return pd.DataFrame(rows).sort_values(["date", "weight"], ascending=[True, False]).reset_index(drop=True)
