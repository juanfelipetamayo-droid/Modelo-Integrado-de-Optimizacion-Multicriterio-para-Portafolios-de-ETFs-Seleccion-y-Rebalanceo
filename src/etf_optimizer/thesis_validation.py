from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from etf_optimizer.thesis_alignment import THESIS_REQUIRED_CRITERIA

ORIGINAL_OBJECTIVE_GENERAL = (
    "Desarrollar un modelo de optimización de portafolios de inversión basado en ETFs mediante análisis multicriterio, "
    "considerando rendimiento, volatilidad, Sharpe Ratio, liquidez, tracking error y expense ratio, que sirva como herramienta "
    "de toma de decisiones de inversión."
)
ORIGINAL_OBJECTIVE_1 = "Diseñar e implementar un sistema de clasificación multicriterio que reduzca el universo del mercado estadounidense a un conjunto de 10-25 activos sobre datos del 2021-2024."
ORIGINAL_OBJECTIVE_2 = "Analizar el desempeño histórico de los ETFs clasificados como elegibles durante 2021-2024 para caracterizar riesgo-retorno y validar la consistencia de la selección multicriterio."
ORIGINAL_OBJECTIVE_3 = "Desarrollar e implementar un modelo de optimización de portafolios que maximice la rentabilidad ajustada por riesgo y validar que el enfoque multicriterio genera mejores rentabilidades ajustadas por riesgo comparado con estrategias tradicionales."
OPERATIONAL_OBJECTIVE_3 = "Desarrollar e implementar un modelo de optimización de portafolios que busque mejorar la rentabilidad ajustada por riesgo y controlar la exposición al riesgo, con el propósito de construir portafolios eficientes y evaluar empíricamente si el enfoque multicriterio ofrece ventajas frente a estrategias de inversión tradicionales."


@dataclass(frozen=True)
class ObjectiveStatus:
    objective: str
    status: str
    evidence: str
    blocking_gaps: str


def thesis_objective_registry() -> pd.DataFrame:
    """Return accepted thesis objectives plus operational validation wording."""
    return pd.DataFrame(
        [
            {
                "objective": "general",
                "accepted_wording": ORIGINAL_OBJECTIVE_GENERAL,
                "operational_wording": ORIGINAL_OBJECTIVE_GENERAL,
                "traceability_note": "Accepted objective preserved.",
            },
            {
                "objective": "specific_1",
                "accepted_wording": ORIGINAL_OBJECTIVE_1,
                "operational_wording": ORIGINAL_OBJECTIVE_1,
                "traceability_note": "Accepted objective preserved; validation requires 10-25 selected ETFs per rebalance.",
            },
            {
                "objective": "specific_2",
                "accepted_wording": ORIGINAL_OBJECTIVE_2,
                "operational_wording": ORIGINAL_OBJECTIVE_2,
                "traceability_note": "Accepted objective preserved; diagnostics define consistency evidence.",
            },
            {
                "objective": "specific_3",
                "accepted_wording": ORIGINAL_OBJECTIVE_3,
                "operational_wording": OPERATIONAL_OBJECTIVE_3,
                "traceability_note": "Operational reformulation preserves infinitive verbs and evaluates outperformance empirically rather than assuming it.",
            },
        ]
    )


def objective_traceability_matrix(criteria_coverage: pd.DataFrame | None = None) -> pd.DataFrame:
    """Map each thesis objective to data requirements, sources, fallbacks and evidence."""
    status_by_criterion = {}
    if criteria_coverage is not None and not criteria_coverage.empty and {"criterion", "status"}.issubset(criteria_coverage.columns):
        status_by_criterion = criteria_coverage.set_index("criterion")["status"].astype(str).to_dict()
    rows = [
        ("general", "return", "public adjusted prices", "trailing/OOS returns", "cross-source price check", "medium", status_by_criterion.get("cagr", "unknown")),
        ("general", "volatility", "public adjusted prices", "annualized volatility", "cross-source price check", "medium", status_by_criterion.get("volatility", "unknown")),
        ("general", "Sharpe Ratio", "prices + risk-free/proxy", "excess return / volatility", "documented zero/T-bill proxy", "medium", status_by_criterion.get("sharpe", "unknown")),
        ("general", "liquidity", "OHLCV public prices", "ADV / dollar volume", "secondary OHLCV source", "medium", status_by_criterion.get("liquidity", "unknown")),
        ("general", "tracking error", "benchmark_map + prices", "std ETF minus benchmark returns", "proxy benchmark", "medium", status_by_criterion.get("tracking_error", "unknown")),
        ("general", "expense ratio", "issuer/prospectus/SEC", "net/gross expense ratio", "issuer factsheet or missing flag", "medium_high", status_by_criterion.get("expense_ratio", "unknown")),
        ("specific_1", "active ETF universe", "SEC EDGAR/N-CEN/N-PORT", "ETF flag + identifiers", "issuer/OpenFIGI/prices", "medium_high", "requires_run"),
        ("specific_1", "10-25 selection", "ELECTRE + final cardinality rule", "selected count per rebalance", "ranked score fallback", "high", "requires_run"),
        ("specific_2", "classification consistency", "ELECTRE diagnostics", "forward performance / monotonicity / Jaccard", "sensitivity diagnostics", "high", "requires_run"),
        ("specific_3", "benchmark evaluation", "SPY, 60/40, same-universe baselines", "CAGR/Sharpe/Sortino/MDD", "documented benchmark substitutes", "high", "requires_run"),
    ]
    return pd.DataFrame(
        rows,
        columns=["objective", "criterion", "primary_source", "field_or_derivation", "fallback", "confidence", "coverage_status"],
    )


def validate_objective_general(criteria_coverage: pd.DataFrame) -> dict[str, object]:
    """Validate objective general against the six accepted criteria."""
    statuses = criteria_coverage.set_index("criterion")["status"].astype(str).to_dict() if not criteria_coverage.empty else {}
    missing = [criterion for criterion in THESIS_REQUIRED_CRITERIA if statuses.get(criterion) not in {"complete", "proxy"}]
    status = "fulfilled" if not missing and all(statuses.get(c) == "complete" for c in THESIS_REQUIRED_CRITERIA) else "near-fulfilled" if not missing else "partial"
    return {"objective": "general", "status": status, "missing_or_partial_criteria": missing}


def validate_objective1_cardinality(selection_by_rebalance: pd.DataFrame, *, min_assets: int = 10, max_assets: int = 25) -> dict[str, object]:
    """Validate 10-25 selected ETF cardinality per rebalance."""
    if selection_by_rebalance.empty:
        return {"objective": "specific_1", "status": "not fulfilled operationally", "violating_dates": [], "counts_by_rebalance": {}}
    selected = selection_by_rebalance.loc[selection_by_rebalance["selected"].astype(bool)]
    counts = selected.groupby("rebalance_date")["ticker"].nunique().to_dict()
    all_dates = sorted(selection_by_rebalance["rebalance_date"].dropna().astype(str).unique())
    counts = {date: int(counts.get(date, 0)) for date in all_dates}
    violating = [date for date, count in counts.items() if count < min_assets or count > max_assets]
    return {
        "objective": "specific_1",
        "status": "fulfilled" if not violating and counts else "not fulfilled operationally",
        "violating_dates": violating,
        "counts_by_rebalance": counts,
        "aggregate_unique_selected": int(selected["ticker"].nunique()) if not selected.empty else 0,
    }


def validate_temporal_protocol(*, start: str, end: str) -> dict[str, object]:
    """Classify principal 2021-2024/2025 versus extended robustness protocols."""
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if start_ts.year == 2021 and end_ts.year in {2024, 2025}:
        role = "thesis_aligned_principal"
    elif start_ts.year <= 2015 and end_ts.year >= 2025:
        role = "extended_robustness_not_replacement"
    else:
        role = "nonstandard_protocol"
    return {"start": str(start_ts.date()), "end": str(end_ts.date()), "validation_role": role}


def validate_objective2_classification(diagnostics: pd.DataFrame) -> dict[str, object]:
    """Validate ELECTRE consistency from monotonicity/stability diagnostic columns when present."""
    if diagnostics.empty:
        return {"objective": "specific_2", "status": "partial", "evidence": "missing diagnostics"}
    monotonic_cols = [col for col in diagnostics.columns if "monotonic" in col]
    jaccard_cols = [col for col in diagnostics.columns if "jaccard" in col.lower()]
    monotonic_ok = bool(diagnostics[monotonic_cols].astype(bool).all().all()) if monotonic_cols else False
    stable_ok = bool((diagnostics[jaccard_cols].apply(pd.to_numeric, errors="coerce") >= 0.25).all().all()) if jaccard_cols else False
    status = "fulfilled" if monotonic_ok and stable_ok else "partial"
    return {"objective": "specific_2", "status": status, "monotonic_ok": monotonic_ok, "stable_ok": stable_ok}


def validate_objective3_benchmarks(
    strategy_metrics: dict[str, float] | pd.Series,
    benchmark_metrics: pd.DataFrame,
    *,
    strategy_name: str = "thesis_strategy",
) -> dict[str, object]:
    """Evaluate objective 3 without assuming benchmark outperformance."""
    strategy_raw = pd.Series(strategy_metrics)
    strategy = pd.to_numeric(strategy_raw, errors="coerce")
    required_metrics = [
        metric
        for metric in ["sharpe", "sortino", "max_drawdown", "cagr", "volatility"]
        if metric in strategy.index and pd.notna(strategy[metric])
    ]
    if benchmark_metrics.empty or not required_metrics:
        return {"objective": "specific_3", "status": "partial", "evidence": "missing benchmark metrics"}
    comparisons: dict[str, bool] = {}
    for metric in required_metrics:
        values = pd.to_numeric(benchmark_metrics[metric], errors="coerce") if metric in benchmark_metrics.columns else pd.Series(dtype="float64")
        if values.empty:
            continue
        if metric in {"max_drawdown", "volatility"}:
            comparisons[metric] = bool(strategy[metric] >= values.max()) if metric == "max_drawdown" else bool(strategy[metric] <= values.min())
        else:
            comparisons[metric] = bool(strategy[metric] >= values.max())
    risk_control = comparisons.get("max_drawdown", False) or comparisons.get("volatility", False)
    risk_adjusted = comparisons.get("sharpe", False) or comparisons.get("sortino", False)
    if risk_adjusted:
        status = "empirically supported"
    elif risk_control:
        status = "partially supported for risk control"
    else:
        status = "not empirically validated"
    return {"objective": "specific_3", "strategy": strategy_name, "status": status, "metric_comparisons": comparisons}


def benchmark_set_completeness(benchmark_names: Iterable[str]) -> dict[str, object]:
    """Check benchmark set completeness for thesis reporting."""
    names = set(benchmark_names)
    required = {"SPY_buy_hold", "60/40_SPY_BND_fixed_weight", "Universe_EqualWeight_walk_forward"}
    missing = sorted(required - names)
    return {"status": "complete" if not missing else "partial", "missing_benchmarks": missing}


def compliance_summary(statuses: Iterable[dict[str, object]], evidence_paths: dict[str, str] | None = None) -> pd.DataFrame:
    """Build final objective compliance table with evidence paths and gaps."""
    evidence_paths = evidence_paths or {}
    rows = []
    for status in statuses:
        objective = str(status.get("objective"))
        gaps = status.get("missing_or_partial_criteria") or status.get("violating_dates") or status.get("evidence") or ""
        rows.append(
            ObjectiveStatus(
                objective=objective,
                status=str(status.get("status", "partial")),
                evidence=evidence_paths.get(objective, ""),
                blocking_gaps=";".join(map(str, gaps)) if isinstance(gaps, list) else str(gaps),
            ).__dict__
        )
    return pd.DataFrame(rows, columns=["objective", "status", "evidence", "blocking_gaps"])
