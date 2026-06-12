from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

import numpy as np
import pandas as pd

from etf_optimizer.selection.electre_tri import AssignmentMode, Criterion, ElectreTri, Profile, SelectionBackend

THESIS_REQUIRED_CRITERIA: tuple[str, ...] = (
    "cagr",
    "volatility",
    "sharpe",
    "liquidity",
    "tracking_error",
    "expense_ratio",
)

THESIS_CATEGORY_MAP = {
    "above_preferred": "excelentes",
    "above_minimum": "excelentes",
    "between_minimum_preferred": "aceptables",
    "below_minimum": "rechazados",
}

PeerGroup = Literal[
    "equity_broad",
    "equity_sector",
    "equity_international",
    "fixed_income",
    "commodities",
    "real_assets_alternatives",
    "thematic",
    "leveraged_inverse_special",
    "other",
]


@dataclass(frozen=True)
class CriterionCoverage:
    criterion: str
    present: bool
    non_null_count: int
    coverage_pct: float
    status: str


def thesis_category(category: str) -> str:
    """Map internal ELECTRE categories to thesis-facing labels."""
    normalized = str(category)
    if normalized in THESIS_CATEGORY_MAP:
        return THESIS_CATEGORY_MAP[normalized]
    if normalized.startswith("above_"):
        return "excelentes"
    if normalized.startswith("between_"):
        return "aceptables"
    return "rechazados"


def infer_etf_peer_group(
    ticker: str,
    name: str | None = None,
    category: str | None = None,
    asset_class: str | None = None,
) -> PeerGroup:
    """Rule-based ETF peer group taxonomy for adapting Xidonas sector classes."""
    text = " ".join(part for part in [ticker, name or "", category or "", asset_class or ""] if part).lower()
    text = re.sub(r"\s+", " ", text)
    if any(token in text for token in ("3x", "2x", "leveraged", "ultra", "inverse", "short ", "bear")):
        return "leveraged_inverse_special"
    if any(token in text for token in ("bond", "treasury", "income", "municipal", "aggregate", "corporate", "tips")):
        return "fixed_income"
    if any(token in text for token in ("gold", "silver", "commodity", "commodities", "oil", "natural gas", "copper", "wheat")):
        return "commodities"
    if any(token in text for token in ("reit", "real estate", "infrastructure", "mlp", "alternatives")):
        return "real_assets_alternatives"
    if any(token in text for token in ("robotics", "innovation", "thematic", "clean energy", "solar", "cyber", "ai ")):
        return "thematic"
    if any(token in text for token in ("international", "emerging", "developed", "ex-us", "global", "china", "europe", "japan")):
        return "equity_international"
    if any(token in text for token in ("sector", "technology", "health", "energy", "financial", "industrial", "utilities")):
        return "equity_sector"
    if any(token in text for token in ("s&p 500", "total stock", "broad", "large cap", "russell", "market")):
        return "equity_broad"
    return "other"


def peer_group_lookup(metadata: pd.DataFrame | None, tickers: list[str] | pd.Index) -> pd.Series:
    """Return peer groups indexed by ticker, using explicit metadata when present."""
    tickers = pd.Index([str(ticker) for ticker in tickers])
    if metadata is None or metadata.empty or "ticker" not in metadata.columns:
        return pd.Series({ticker: infer_etf_peer_group(ticker) for ticker in tickers}, name="peer_group")
    meta = metadata.drop_duplicates("ticker").set_index("ticker")
    rows: dict[str, str] = {}
    for ticker in tickers:
        if ticker in meta.index:
            row = meta.loc[ticker]
            explicit = row.get("peer_group") if "peer_group" in meta.columns else None
            if explicit is not None and not pd.isna(explicit):
                rows[ticker] = str(explicit)
                continue
            rows[ticker] = infer_etf_peer_group(
                ticker,
                name=str(row.get("name", "")) if "name" in meta.columns else "",
                category=str(row.get("category", "")) if "category" in meta.columns else "",
                asset_class=str(row.get("asset_class", "")) if "asset_class" in meta.columns else "",
            )
        else:
            rows[ticker] = infer_etf_peer_group(ticker)
    return pd.Series(rows, name="peer_group")


def criterion_coverage(features: pd.DataFrame, required: tuple[str, ...] = THESIS_REQUIRED_CRITERIA) -> pd.DataFrame:
    """Coverage audit for thesis-required criteria."""
    rows: list[CriterionCoverage] = []
    total = len(features)
    for criterion in required:
        present = criterion in features.columns
        non_null = int(features[criterion].notna().sum()) if present else 0
        coverage = float(non_null / total) if total else 0.0
        rows.append(
            CriterionCoverage(
                criterion=criterion,
                present=present,
                non_null_count=non_null,
                coverage_pct=coverage,
                status="complete" if present and coverage >= 1.0 else "partial" if present and non_null else "missing",
            )
        )
    return pd.DataFrame([row.__dict__ for row in rows])


def _quality_quantile(values: pd.Series, criterion: Criterion, quality: float) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return np.nan
    quantile = quality if criterion.preference_direction == "max" else 1.0 - quality
    return float(clean.quantile(quantile))


def derive_peer_group_profiles(
    criteria_matrix: pd.DataFrame,
    criteria: list[Criterion],
    *,
    minimum_quality: float = 0.40,
    preferred_quality: float = 0.70,
) -> list[Profile]:
    """Derive ELECTRE profiles from train-only peer-group quantiles."""
    minimum = {criterion.name: _quality_quantile(criteria_matrix[criterion.name], criterion, minimum_quality) for criterion in criteria}
    preferred = {criterion.name: _quality_quantile(criteria_matrix[criterion.name], criterion, preferred_quality) for criterion in criteria}
    return [Profile("minimum", minimum), Profile("preferred", preferred)]


def assign_electre_by_peer_group(
    criteria_matrix: pd.DataFrame,
    criteria: list[Criterion],
    global_profiles: list[Profile],
    *,
    metadata: pd.DataFrame | None,
    lambda_cut: float,
    assignment: AssignmentMode,
    use_veto: bool,
    backend: SelectionBackend,
    min_group_size: int = 5,
) -> pd.DataFrame:
    """Assign ELECTRE categories inside ETF peer groups with global fallback."""
    groups = peer_group_lookup(metadata, criteria_matrix.index)
    frames: list[pd.DataFrame] = []
    for group_name, group_index in groups.groupby(groups).groups.items():
        group_matrix = criteria_matrix.loc[list(group_index)]
        if len(group_matrix) >= min_group_size:
            profiles = derive_peer_group_profiles(group_matrix, criteria)
            profile_scope = "peer_group"
        else:
            profiles = global_profiles
            profile_scope = "global_fallback"
        assignments = ElectreTri(
            criteria,
            profiles,
            lambda_cut,
            assignment=assignment,
            use_veto=use_veto,
            backend=backend,
        ).assign(group_matrix)
        assignments["peer_group"] = str(group_name)
        assignments["profile_scope"] = profile_scope
        frames.append(assignments)
    if not frames:
        return pd.DataFrame(index=criteria_matrix.index)
    return pd.concat(frames).loc[criteria_matrix.index]


def _selection_score(selection: pd.DataFrame) -> pd.Series:
    credibility_cols = [col for col in selection.columns if col.startswith("credibility_")]
    if credibility_cols:
        return selection[credibility_cols].max(axis=1)
    return pd.Series(0.0, index=selection.index)


def finalize_thesis_selection(
    selection: pd.DataFrame,
    *,
    min_assets: int = 10,
    max_assets: int = 25,
) -> list[str]:
    """Return a thesis cardinality-compliant 10-25 ETF candidate set when possible."""
    if min_assets <= 0 or max_assets < min_assets:
        raise ValueError("expected 0 < min_assets <= max_assets")
    ranked = selection.copy()
    ranked["thesis_category"] = ranked["category"].map(thesis_category)
    ranked["selection_score"] = _selection_score(ranked)
    category_rank = {"excelentes": 0, "aceptables": 1, "rechazados": 2}
    ranked["_category_rank"] = ranked["thesis_category"].map(category_rank).fillna(3)
    ranked = ranked.sort_values(["_category_rank", "selection_score"], ascending=[True, False])
    selected = ranked.index.astype(str).tolist()[:max_assets]
    if len(selected) < min_assets:
        return selected
    return selected


def thesis_data_quality_verdict(
    *,
    universe_mode: str,
    price_source: str,
    criteria_coverage_table: pd.DataFrame,
    pit_controls_passed: bool | None = None,
    identifier_ambiguities: int = 0,
    benchmark_mapping_quality: str = "partial",
) -> dict[str, object]:
    """Classify whether a run satisfies thesis-aligned data requirements."""
    acceptable_statuses = {"complete", "proxy"}
    missing = criteria_coverage_table.loc[
        ~criteria_coverage_table["status"].astype(str).isin(acceptable_statuses), "criterion"
    ].astype(str).tolist()
    normalized_universe = universe_mode.lower()
    regulatory_mode = "regulatory" in normalized_universe
    pit_ok = True if pit_controls_passed is None else bool(pit_controls_passed)
    verdict = "thesis_aligned" if not missing and "static_current" not in normalized_universe else "partial_thesis_alignment"
    if regulatory_mode and not missing and pit_ok and identifier_ambiguities == 0:
        verdict = "thesis_aligned_public_regulatory_pit"
    elif regulatory_mode:
        verdict = "partial_regulatory_alignment"
    if "extended" in normalized_universe or "2015" in normalized_universe:
        verdict = "extended_robustness_public_data_limited" if not regulatory_mode or missing else verdict
    if "static_current" in normalized_universe:
        verdict = "pilot_static_current_not_primary"
    if verdict == "thesis_aligned_public_regulatory_pit":
        allowed_claims = "Public/regulatory enriched thesis evidence with approximate PIT controls; disclose public-data limitations."
    elif verdict == "thesis_aligned":
        allowed_claims = "Thesis-aligned evidence."
    else:
        allowed_claims = "Partial evidence; disclose gaps before thesis claims."
    return {
        "verdict": verdict,
        "price_source": price_source,
        "universe_mode": universe_mode,
        "missing_or_partial_criteria": missing,
        "criteria_complete": not missing,
        "pit_controls_passed": pit_ok,
        "identifier_ambiguities": int(identifier_ambiguities),
        "benchmark_mapping_quality": benchmark_mapping_quality,
        "allowed_claims": allowed_claims,
        "prohibited_claims": [
            "fully point-in-time",
            "institutional survivorship-bias-free",
            "complete US ETF universe",
            "guaranteed benchmark outperformance",
        ],
    }
