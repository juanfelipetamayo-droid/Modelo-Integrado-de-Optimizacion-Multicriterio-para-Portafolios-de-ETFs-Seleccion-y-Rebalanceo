from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from etf_optimizer.criteria_config import load_criteria_config

DEFAULT_MANUAL_WEIGHTS: dict[str, float] = {
    "momentum_12_1": 0.12,
    "volatility_annualized": 0.11,
    "rolling_max_drawdown": 0.14,
    "rolling_sortino": 0.12,
    "avg_dollar_volume": 0.08,
    "expense_ratio": 0.08,
    "tracking_error_vs_category_benchmark": 0.10,
    "beta_vs_category_benchmark": 0.08,
    "marginal_correlation_to_selected_universe": 0.10,
    "fund_age_months": 0.03,
    "aum_usd": 0.04,
}

DEFAULT_BWM_BEST = "rolling_max_drawdown"
DEFAULT_BWM_WORST = "fund_age_months"
DEFAULT_BWM_BEST_TO_OTHERS: dict[str, int] = {
    "momentum_12_1": 2,
    "volatility_annualized": 2,
    "rolling_max_drawdown": 1,
    "rolling_sortino": 2,
    "avg_dollar_volume": 3,
    "expense_ratio": 3,
    "tracking_error_vs_category_benchmark": 2,
    "beta_vs_category_benchmark": 3,
    "marginal_correlation_to_selected_universe": 2,
    "fund_age_months": 7,
    "aum_usd": 5,
}
DEFAULT_BWM_OTHERS_TO_WORST: dict[str, int] = {
    "momentum_12_1": 5,
    "volatility_annualized": 5,
    "rolling_max_drawdown": 7,
    "rolling_sortino": 5,
    "avg_dollar_volume": 4,
    "expense_ratio": 4,
    "tracking_error_vs_category_benchmark": 5,
    "beta_vs_category_benchmark": 4,
    "marginal_correlation_to_selected_universe": 5,
    "fund_age_months": 1,
    "aum_usd": 2,
}

RATIONALES: dict[str, str] = {
    "momentum_12_1": "Captura persistencia intermedia sin usar CAGR histórico dominante.",
    "volatility_annualized": "Controla riesgo total ex ante dentro de la clasificación MCDM.",
    "rolling_max_drawdown": "Prioridad principal BWM: limita fragilidad de cola observada en OOS largo.",
    "rolling_sortino": "Premia retorno ajustado por downside sin depender de CAGR puro.",
    "avg_dollar_volume": "Asegura liquidez operable después de filtros duros.",
    "expense_ratio": "Penaliza fricción estructural del ETF.",
    "tracking_error_vs_category_benchmark": "Favorece eficiencia de implementación frente al benchmark correcto.",
    "beta_vs_category_benchmark": "Controla sensibilidad sistemática por categoría.",
    "marginal_correlation_to_selected_universe": "Introduce beneficio de diversificación marginal.",
    "fund_age_months": "Criterio secundario; estabilidad operativa, no driver principal.",
    "aum_usd": "Proxy de escala/viabilidad, subordinado a riesgo y calidad de seguimiento.",
}


@dataclass(frozen=True)
class BWMResult:
    weights: dict[str, float]
    consistency_xi: float
    max_abs_residual: float
    best_criterion: str
    worst_criterion: str


def load_mcdm_criterion_names(criteria_config_path: str | Path) -> list[str]:
    return [spec.criterion_name for spec in load_criteria_config(criteria_config_path) if not spec.is_hard_filter]


def _normalize(weights: Mapping[str, float], criteria: list[str]) -> dict[str, float]:
    missing = set(criteria) - set(weights)
    if missing:
        raise ValueError(f"missing weights for criteria: {sorted(missing)}")
    selected = {criterion: float(weights[criterion]) for criterion in criteria}
    total = sum(selected.values())
    if total <= 0:
        raise ValueError("weights must sum to a positive value")
    return {criterion: value / total for criterion, value in selected.items()}


def bwm_weights(
    criteria: list[str],
    *,
    best_criterion: str,
    worst_criterion: str,
    best_to_others: Mapping[str, int | float],
    others_to_worst: Mapping[str, int | float],
) -> BWMResult:
    """Solve the linear Best-Worst Method min-xi formulation.

    Constraints follow Rezaei's common BWM model:
    ``|w_best - a_Bj w_j| <= xi`` and ``|w_j - a_jW w_worst| <= xi``.
    """

    if best_criterion not in criteria or worst_criterion not in criteria:
        raise ValueError("best and worst criteria must be present in criteria")
    if set(best_to_others) != set(criteria) or set(others_to_worst) != set(criteria):
        raise ValueError("BWM comparison dictionaries must include exactly all criteria")

    n_criteria = len(criteria)
    xi_index = n_criteria
    best_index = criteria.index(best_criterion)
    worst_index = criteria.index(worst_criterion)

    objective = np.zeros(n_criteria + 1)
    objective[xi_index] = 1.0
    a_ub: list[list[float]] = []
    b_ub: list[float] = []

    for criterion in criteria:
        criterion_index = criteria.index(criterion)
        best_preference = float(best_to_others[criterion])
        worst_preference = float(others_to_worst[criterion])

        row = np.zeros(n_criteria + 1)
        row[best_index] = 1.0
        row[criterion_index] -= best_preference
        row[xi_index] = -1.0
        a_ub.append(row.tolist())
        b_ub.append(0.0)

        row = np.zeros(n_criteria + 1)
        row[best_index] = -1.0
        row[criterion_index] += best_preference
        row[xi_index] = -1.0
        a_ub.append(row.tolist())
        b_ub.append(0.0)

        row = np.zeros(n_criteria + 1)
        row[criterion_index] = 1.0
        row[worst_index] -= worst_preference
        row[xi_index] = -1.0
        a_ub.append(row.tolist())
        b_ub.append(0.0)

        row = np.zeros(n_criteria + 1)
        row[criterion_index] = -1.0
        row[worst_index] += worst_preference
        row[xi_index] = -1.0
        a_ub.append(row.tolist())
        b_ub.append(0.0)

    a_eq = np.zeros((1, n_criteria + 1))
    a_eq[0, :n_criteria] = 1.0
    bounds = [(0.0, 1.0) for _ in criteria] + [(0.0, None)]
    result = linprog(
        objective,
        A_ub=np.array(a_ub),
        b_ub=np.array(b_ub),
        A_eq=a_eq,
        b_eq=np.array([1.0]),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise ValueError(f"BWM optimization failed: {result.message}")

    weights = {criterion: float(result.x[index]) for index, criterion in enumerate(criteria)}
    residuals: list[float] = []
    for criterion in criteria:
        residuals.append(abs(weights[best_criterion] - float(best_to_others[criterion]) * weights[criterion]))
        residuals.append(abs(weights[criterion] - float(others_to_worst[criterion]) * weights[worst_criterion]))

    return BWMResult(
        weights=weights,
        consistency_xi=float(result.x[xi_index]),
        max_abs_residual=float(max(residuals)),
        best_criterion=best_criterion,
        worst_criterion=worst_criterion,
    )


def _weights_frame(
    weights: Mapping[str, float],
    *,
    criteria: list[str],
    method: str,
    elicitation_source: str,
) -> pd.DataFrame:
    normalized = _normalize(weights, criteria)
    return pd.DataFrame(
        [
            {
                "criterion_name": criterion,
                "weight": normalized[criterion],
                "method": method,
                "elicitation_source": elicitation_source,
                "rationale": RATIONALES.get(criterion, "Documento de criterios ETF GOAL 4."),
            }
            for criterion in criteria
        ]
    )


def _sensitivity_samples(
    base_weights: Mapping[str, float],
    *,
    criteria: list[str],
    n_samples: int,
    random_seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    base = np.array([base_weights[criterion] for criterion in criteria], dtype=float)
    alpha = np.maximum(base * 60.0, 0.5)
    rows: list[dict[str, float | int | str]] = []
    for sample_id, sample in enumerate(rng.dirichlet(alpha, size=n_samples), start=1):
        for criterion, weight in zip(criteria, sample, strict=True):
            rows.append(
                {
                    "sample_id": sample_id,
                    "criterion_name": criterion,
                    "weight": float(weight),
                    "method": "random_weight_sensitivity",
                    "elicitation_source": "Dirichlet perturbation centered on BWM_weights_main; no performance tuning.",
                }
            )
    return pd.DataFrame(rows)


def _consistency_report(
    *,
    criteria: list[str],
    bwm_result: BWMResult,
    n_sensitivity_samples: int,
) -> str:
    weights_table = "\n".join(
        f"| {criterion} | {bwm_result.weights[criterion]:.6f} | {RATIONALES.get(criterion, '')} |"
        for criterion in criteria
    )
    return f"""# Weight consistency report — GOAL 11

## Alcance

Este reporte formaliza pesos para los criterios MCDM de ETFs definidos en `configs/criteria_config.yaml`.
Los pesos manuales se conservan solo como baseline; el método principal documentado es BWM por requerir menos comparaciones que AHP para muchos criterios financieros.

## Mini-elicitation documentada

| Rol | Estado | Uso en este hito |
|---|---|---|
| experto 1: investigador/Hermes | Disponible | `BWM_weights_main` |
| experto 2: director/profesor | Pendiente de elicitation humana | No se inventan preferencias; registrar cuando esté disponible |
| experto 3: literatura/criterio institucional | Aproximado documentalmente | Usado en racionales y estructura de criterios; no sustituye experto humano |

## Rutas de pesos generadas

- `manual_weights_baseline`: baseline documentado, no método principal.
- `BWM_weights_main`: método principal provisional para tesis hasta recibir experto 2.
- `equal_weights_baseline`: control neutro.
- `random_weight_sensitivity`: {n_sensitivity_samples} muestras aleatorias centradas en BWM para robustez.

## Consistencia BWM

- Mejor criterio: `{bwm_result.best_criterion}`.
- Peor criterio: `{bwm_result.worst_criterion}`.
- Xi óptimo: `{bwm_result.consistency_xi:.6f}`.
- Máximo residuo absoluto: `{bwm_result.max_abs_residual:.6f}`.
- Interpretación: menor Xi implica comparaciones más consistentes; este reporte debe actualizarse si el director/profesor entrega juicios distintos.

## Pesos BWM researcher

| Criterio | Peso | Racional |
|---|---:|---|
{weights_table}

## Regla académica

No usar pesos manuales como resultado principal. La tesis debe reportar BWM como especificación primaria, equal-weight como baseline y random-weight sensitivity como robustez. Si experto 2 no está disponible, declarar explícitamente `director/profesor pendiente` y no presentarlo como juicio observado.
"""


def _methodology_document(
    *,
    criteria: list[str],
    bwm_result: BWMResult,
    n_sensitivity_samples: int,
) -> str:
    criteria_lines = "\n".join(
        f"- `{criterion}`: peso BWM `{bwm_result.weights[criterion]:.6f}`."
        for criterion in criteria
    )
    return f"""# GOAL 11 — Elicitación defendible de pesos: BWM/AHP + sensibilidad

## Objetivo

Los pesos manuales dejan de ser la metodología principal. Se conservan únicamente como baseline auditable para comparar contra métodos defendibles de decisión multicriterio.

## Ruta recomendada y estado implementado

| Ruta | Rol metodológico | Estado |
|---|---|---|
| `manual_weights_baseline` | Comparador histórico; no es especificación principal. | Generado en `weights_manual.csv`. |
| `equal_weights_baseline` | Control neutro para detectar dependencia excesiva de pesos expertos. | Generado en `weights_equal.csv`. |
| `BWM_weights_main` | Especificación principal provisional porque BWM requiere menos comparaciones pareadas que AHP cuando hay muchos criterios. | Generado en `weights_bwm.csv`. |
| `random_weight_sensitivity` | Robustez: perturbaciones aleatorias Dirichlet centradas en BWM, sin tuning de performance. | {n_sensitivity_samples} muestras en `weights_sensitivity_samples.csv`. |

## Por qué BWM es la ruta principal

BWM pide seleccionar el mejor y el peor criterio y luego compara el mejor contra los demás y los demás contra el peor. Para un conjunto amplio de criterios ETF es más manejable que AHP completo, que exige muchas comparaciones pareadas y puede volverse costoso de mantener. AHP queda como alternativa posible si el director/profesor entrega una matriz de comparaciones consistente, pero no se inventan juicios humanos.

## Juicios BWM documentados

- Mejor criterio: `{bwm_result.best_criterion}`.
- Peor criterio: `{bwm_result.worst_criterion}`.
- Xi óptimo de consistencia: `{bwm_result.consistency_xi:.6f}`.
- Máximo residuo absoluto: `{bwm_result.max_abs_residual:.6f}`.

## Pesos principales BWM

{criteria_lines}

## Regla de tesis

En resultados principales usar `BWM_weights_main`. Reportar `manual_weights_baseline` y `equal_weights_baseline` como controles, y `random_weight_sensitivity` como sensibilidad. Si no existe elicitation humana del director/profesor, declararlo explícitamente como pendiente.
"""


def generate_weight_artifacts(
    *,
    criteria_config_path: str | Path = "configs/criteria_config.yaml",
    output_dir: str | Path = "configs/weights",
    n_sensitivity_samples: int = 500,
    random_seed: int = 42,
    methodology_doc_path: str | Path | None = None,
) -> list[Path]:
    criteria = load_mcdm_criterion_names(criteria_config_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    manual = _weights_frame(
        DEFAULT_MANUAL_WEIGHTS,
        criteria=criteria,
        method="manual_weights_baseline",
        elicitation_source="Researcher baseline retained only for comparison; not primary thesis specification.",
    )
    equal = _weights_frame(
        {criterion: 1.0 for criterion in criteria},
        criteria=criteria,
        method="equal_weights_baseline",
        elicitation_source="Neutral baseline: every MCDM criterion receives identical weight.",
    )
    bwm_result = bwm_weights(
        criteria,
        best_criterion=DEFAULT_BWM_BEST,
        worst_criterion=DEFAULT_BWM_WORST,
        best_to_others=DEFAULT_BWM_BEST_TO_OTHERS,
        others_to_worst=DEFAULT_BWM_OTHERS_TO_WORST,
    )
    bwm = _weights_frame(
        bwm_result.weights,
        criteria=criteria,
        method="BWM_weights_main",
        elicitation_source="Expert 1 researcher/Hermes mini-elicitation; expert 2 director/profesor pending.",
    )
    sensitivity = _sensitivity_samples(
        bwm_result.weights,
        criteria=criteria,
        n_samples=n_sensitivity_samples,
        random_seed=random_seed,
    )

    methodology_path = Path(methodology_doc_path) if methodology_doc_path else output_path / "weight_elicitation.md"
    methodology_path.parent.mkdir(parents=True, exist_ok=True)
    paths = [
        output_path / "weights_manual.csv",
        output_path / "weights_bwm.csv",
        output_path / "weights_equal.csv",
        output_path / "weights_sensitivity_samples.csv",
        output_path / "weight_consistency_report.md",
        methodology_path,
    ]
    manual.to_csv(paths[0], index=False)
    bwm.to_csv(paths[1], index=False)
    equal.to_csv(paths[2], index=False)
    sensitivity.to_csv(paths[3], index=False)
    paths[4].write_text(
        _consistency_report(
            criteria=criteria,
            bwm_result=bwm_result,
            n_sensitivity_samples=n_sensitivity_samples,
        ),
        encoding="utf-8",
    )
    paths[5].write_text(
        _methodology_document(
            criteria=criteria,
            bwm_result=bwm_result,
            n_sensitivity_samples=n_sensitivity_samples,
        ),
        encoding="utf-8",
    )
    return paths
