from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from etf_optimizer.selection.electre_tri import Criterion, Profile


@dataclass(frozen=True)
class MethodologyReportConfig:
    universe_path: Path
    prices_path: Path | None
    volume_path: Path | None
    start: str
    end: str
    rebalance: str
    train_size: int
    test_size: int
    step_size: int
    cost_bps: float
    min_coverage_pct: float
    min_avg_dollar_volume: float
    price_source: str
    universe_snapshot_date: str
    fold_diagnostics: dict[str, Any] | None = None
    data_quality: dict[str, Any] | None = None
    universe_mode: str = "unspecified"
    validation_role: str = "primary"


def _format_sources(universe: pd.DataFrame) -> str:
    if "source" not in universe.columns:
        return "unspecified"
    sources = sorted({str(source) for source in universe["source"].dropna().unique()})
    return ", ".join(sources) if sources else "unspecified"


def _format_source_urls(universe: pd.DataFrame) -> str:
    if "source_url" not in universe.columns:
        return "unspecified"
    urls = sorted({str(url) for url in universe["source_url"].dropna().unique()})
    return ", ".join(urls) if urls else "unspecified"


def _format_path(path: Path | None) -> str:
    return str(path) if path is not None else "synthetic structural test data"


def _criteria_table(criteria: list[Criterion]) -> str:
    lines = ["| criterion | weight | direction | q | p | v |", "| --- | ---: | --- | ---: | ---: | ---: |"]
    lines.extend(
        f"| {criterion.name} | {criterion.weight} | {criterion.preference_direction} | "
        f"{criterion.q} | {criterion.p} | {criterion.v} |"
        for criterion in criteria
    )
    return "\n".join(lines)


def _profile_table(profiles: list[Profile]) -> str:
    lines = ["| profile | thresholds |", "| --- | --- |"]
    for profile in profiles:
        thresholds = ", ".join(f"{name}={value}" for name, value in profile.values.items())
        lines.append(f"| {profile.name} | {thresholds} |")
    return "\n".join(lines)


def _funnel_table(filter_funnel: pd.DataFrame) -> str:
    lines = ["| stage | count | pct_of_requested |", "| --- | ---: | ---: |"]
    for row in filter_funnel.to_dict("records"):
        lines.append(f"| {row['stage']} | {row['count']} | {row['pct_of_requested']} |")
    return "\n".join(lines)


def _limitations_text(price_source: str) -> str:
    if price_source == "regulatory_enriched_public":
        return """Este experimento usa un universo ETF público/regulatorio enriquecido con fuentes SEC/EDGAR, identificadores externos y precios públicos. La evidencia puede reducir lookahead bias mediante fechas de disponibilidad, pero no debe describirse como universo institucional fully point-in-time ni survivor-bias-free salvo que se demuestre cobertura completa de cierres/delistings.

Las fuentes públicas pueden tener rezagos de publicación, benchmarks aproximados, metadatos incompletos, restatements y restricciones de uso. Los reportes deben distinguir datos primarios, fallbacks, proxies y criterios faltantes."""
    if price_source == "yfinance":
        return """Este experimento usa un universo amplio de ETFs activos actuales obtenido de Nasdaq y precios públicos vía yfinance. No elimina completamente survivorship bias; lo documenta y lo mitiga parcialmente mediante reportes de cobertura y filtros de disponibilidad histórica. Para afirmaciones survivorship-bias-free se requiere CRSP, Morningstar Direct, Lipper, Bloomberg o equivalente institucional.

yfinance is a public API / unofficial Yahoo Finance data access layer. It is useful for reproducible prototypes, but it can have ticker-level gaps, adjusted-price differences, rate limits, delistings not represented in an active-current universe, and vendor revisions. Results should therefore be treated as research diagnostics, not institutional-grade survivorship-bias-free performance evidence."""
    return """Este experimento usa un universo amplio de ETFs activos actuales obtenido de Nasdaq. No elimina completamente survivorship bias; lo documenta y lo mitiga parcialmente mediante reportes de cobertura y filtros de disponibilidad histórica. Para afirmaciones survivorship-bias-free se requiere CRSP, Morningstar Direct, Lipper, Bloomberg o equivalente institucional.

Synthetic data limitation: this no-price run uses deterministic structural test data for pipeline validation only. It is not market data, must not be interpreted as ETF performance evidence, and does not exercise yfinance download quality or vendor coverage limitations."""


def _fold_diagnostics_section(diagnostics: dict[str, Any] | None) -> str:
    if not diagnostics:
        return ""
    warning = diagnostics.get("warning") or "None"
    return f"""
## Out-of-sample sufficiency

- Walk-forward folds: {diagnostics.get("walk_forward_folds")}
- OOS periods: {diagnostics.get("oos_periods")}
- Sufficiency label: {diagnostics.get("sufficiency_label")}
- Thesis-grade OOS: {diagnostics.get("thesis_grade_oos")}
- Warning: {warning}
"""


def _data_quality_section(data_quality: dict[str, Any] | None) -> str:
    if not data_quality:
        return ""
    return f"""
## Data-quality verdict

- Verdict: {data_quality.get("verdict")}
- Survivorship-bias-free: {data_quality.get("survivorship_bias_free")}
- Universe mode: {data_quality.get("universe_mode", "unspecified")}
- Price source role: {data_quality.get("price_source_role", "price/volume source, not universe authority")}
- Missing or partial criteria: {data_quality.get("missing_or_partial_criteria", [])}
- Allowed claims: {data_quality.get("allowed_claims")}
- Prohibited claims: {data_quality.get("prohibited_claims", [])}
- Public-data limitations: {data_quality.get("public_data_limitations", [])}
- Fallback usage: {data_quality.get("fallback_usage", [])}
"""



def build_methodology_report(
    config: MethodologyReportConfig,
    *,
    universe: pd.DataFrame,
    filter_funnel: pd.DataFrame,
    criteria: list[Criterion],
    profiles: list[Profile],
) -> str:
    """Build a reproducible markdown methodology report for a sprint run."""
    universe_source = _format_sources(universe)
    universe_source_urls = _format_source_urls(universe)
    universe_rows = len(universe)
    limitations = _limitations_text(config.price_source)
    fold_section = _fold_diagnostics_section(config.fold_diagnostics)
    data_quality_section = _data_quality_section(config.data_quality)

    return f"""# Methodology Report

## Data sources

- Universe source: {universe_source}
- Universe source URL: {universe_source_urls}
- Universe path: {config.universe_path}
- Universe mode: {config.universe_mode}
- Snapshot date: {config.universe_snapshot_date}
- Universe rows: {universe_rows}
- Price source: {config.price_source} (prices/volume only unless explicitly documented as universe authority)
- Prices path: {_format_path(config.prices_path)}
- Volume path: {_format_path(config.volume_path)}
- Temporal range: {config.start} to {config.end}
- Validation role: {config.validation_role}

## Walk-forward configuration

- Walk-forward windows: train={config.train_size}, test={config.test_size}, step={config.step_size}, rebalance={config.rebalance}
- Transaction costs: {config.cost_bps} bps
- Evidence separation: selection, allocation, rebalancing and evaluation must be interpreted separately.

## ELECTRE Tri configuration

### Criteria

{_criteria_table(criteria)}

### Profiles and thresholds

{_profile_table(profiles)}

## Eligibility filters

- Coverage filter: minimum observed price coverage {config.min_coverage_pct:.2%}
- History filter: first valid price must be on or before the experiment start when real prices are used.
- Liquidity filter: minimum average daily dollar volume {config.min_avg_dollar_volume}
- Missing data policy: missing ETF prices are not converted to zero returns for eligibility or performance claims.

## Filter funnel

{_funnel_table(filter_funnel)}

## Methodological limitations

{limitations}
{fold_section}{data_quality_section}"""


def write_methodology_report(
    path: Path,
    config: MethodologyReportConfig,
    *,
    universe: pd.DataFrame,
    filter_funnel: pd.DataFrame,
    criteria: list[Criterion],
    profiles: list[Profile],
) -> Path:
    """Write a markdown methodology report and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = build_methodology_report(
        config,
        universe=universe,
        filter_funnel=filter_funnel,
        criteria=criteria,
        profiles=profiles,
    )
    path.write_text(text, encoding="utf-8")
    return path
