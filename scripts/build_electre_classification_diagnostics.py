from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from etf_optimizer.reporting.classification_diagnostics import write_classification_diagnostics


def _pct(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{x:.2%}"


def _num(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{x:.3f}"


def _markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sin datos._"
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df[columns].iterrows():
        rows.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(rows)


def _monotonic(effectiveness: pd.DataFrame, metric: str, higher_is_better: bool = True) -> bool:
    ordered = effectiveness.sort_values("category_rank")[metric].dropna().tolist()
    if len(ordered) < 2:
        return False
    if higher_is_better:
        return all(right >= left for left, right in zip(ordered, ordered[1:], strict=False))
    return all(right <= left for left, right in zip(ordered, ordered[1:], strict=False))


def build_report(output_dir: Path, docs_path: Path) -> None:
    effectiveness = pd.read_csv(output_dir / "classification_effectiveness.csv")
    divergence = pd.read_csv(output_dir / "pessimistic_optimistic_divergence.csv")
    transitions = pd.read_csv(output_dir / "category_transition_matrix.csv")
    jaccard = pd.read_csv(output_dir / "selection_jaccard_by_fold.csv")

    display = effectiveness.copy()
    for col in [
        "mean_forward_cumulative_return",
        "median_forward_cumulative_return",
        "mean_forward_cagr",
        "mean_forward_max_drawdown",
        "pct_positive_forward_return",
        "selected_rate",
    ]:
        display[col] = display[col].map(_pct)
    display["mean_forward_sharpe"] = display["mean_forward_sharpe"].map(_num)

    mono_return = _monotonic(effectiveness, "mean_forward_cumulative_return", True)
    mono_cagr = _monotonic(effectiveness, "mean_forward_cagr", True)
    mono_sharpe = _monotonic(effectiveness, "mean_forward_sharpe", True)
    mono_drawdown = _monotonic(effectiveness, "mean_forward_max_drawdown", True)  # less negative is better

    by_comparison = (
        divergence.groupby("comparison")
        .agg(
            folds=("fold", "nunique"),
            mean_category_agreement=("category_agreement_rate", "mean"),
            mean_selected_jaccard=("selected_jaccard", "mean"),
            mean_rank_change=("mean_rank_change_right_minus_left", "mean"),
            total_downgrades=("downgrade_count", "sum"),
            total_upgrades=("upgrade_count", "sum"),
        )
        .reset_index()
    )
    divergence_display = by_comparison.copy()
    divergence_display["mean_category_agreement"] = divergence_display["mean_category_agreement"].map(_pct)
    divergence_display["mean_selected_jaccard"] = divergence_display["mean_selected_jaccard"].map(_pct)
    divergence_display["mean_rank_change"] = divergence_display["mean_rank_change"].map(_num)

    stability = {
        "mean_selected_jaccard": float(jaccard["selected_jaccard"].mean()) if not jaccard.empty else float("nan"),
        "min_selected_jaccard": float(jaccard["selected_jaccard"].min()) if not jaccard.empty else float("nan"),
        "mean_candidate_jaccard": float(jaccard["candidate_jaccard"].mean()) if not jaccard.empty else float("nan"),
    }

    top_transition = transitions.sort_values("transition_count", ascending=False).head(12).copy()
    if not top_transition.empty:
        top_transition["transition_probability"] = top_transition["transition_probability"].map(_pct)

    cats = effectiveness.set_index("category")
    excellent = cats.loc["above_preferred"] if "above_preferred" in cats.index else None
    acceptable = cats.loc["between_minimum_preferred"] if "between_minimum_preferred" in cats.index else None

    def compare(metric: str, higher: bool = True) -> str:
        if excellent is None or acceptable is None:
            return "No evaluable: faltan categorías excelente o aceptable."
        ex = float(excellent[metric])
        ac = float(acceptable[metric])
        better = ex > ac if higher else ex < ac
        return "Sí" if better else "No"

    veto = by_comparison[by_comparison["comparison"].str.startswith("veto_effect")].copy()
    veto_agreement = float(veto["mean_category_agreement"].mean()) if not veto.empty else float("nan")
    veto_rank_change = float(veto["mean_rank_change"].mean()) if not veto.empty else float("nan")
    veto_answer = (
        "El veto casi no cambia las clasificaciones" if veto_agreement >= 0.95 else "El veto cambia materialmente las clasificaciones"
    )
    if veto_rank_change < -0.10:
        veto_answer += " y tiende a degradarlas."
    elif veto_rank_change > 0.10:
        veto_answer += " y tiende a elevarlas."
    else:
        veto_answer += " sin sesgo fuerte de upgrade/downgrade."

    report = f"""# Diagnóstico de clasificación MCDM / ELECTRE Tri

**Objetivo:** evaluar si ELECTRE clasifica bien antes de decidir si el portafolio gana. Este reporte usa los artefactos fold-level del baseline `public_approximate_pit` y mide retornos forward por categoría, estabilidad temporal, divergencia pesimista/optimista y efecto del veto.

## Artefactos generados

- `results/electre_classification_diagnostics/classification_effectiveness.csv`
- `results/electre_classification_diagnostics/category_forward_returns.csv`
- `results/electre_classification_diagnostics/category_forward_sharpe.csv`
- `results/electre_classification_diagnostics/category_forward_drawdown.csv`
- `results/electre_classification_diagnostics/pessimistic_optimistic_divergence.csv`
- `results/electre_classification_diagnostics/category_transition_matrix.csv`
- `results/electre_classification_diagnostics/selection_jaccard_by_fold.csv`

## Efectividad por categoría

{_markdown_table(display, ["category", "observations", "folds", "unique_etfs", "mean_forward_cumulative_return", "median_forward_cumulative_return", "mean_forward_cagr", "mean_forward_sharpe", "mean_forward_max_drawdown", "pct_positive_forward_return"])}

## Respuestas directas

| Pregunta | Respuesta |
|---|---|
| ¿Los ETFs excelentes tienen mejor retorno forward que los aceptables? | {compare("mean_forward_cumulative_return", True)} |
| ¿Tienen menor drawdown? | {compare("mean_forward_max_drawdown", True)} |
| ¿Tienen mejor Sharpe forward? | {compare("mean_forward_sharpe", True)} |
| ¿La relación excelente > aceptable > rechazado es monotónica en retorno? | {'Sí' if mono_return else 'No'} |
| ¿La relación es monotónica en CAGR? | {'Sí' if mono_cagr else 'No'} |
| ¿La relación es monotónica en Sharpe? | {'Sí' if mono_sharpe else 'No'} |
| ¿La relación es monotónica en drawdown, donde menos negativo es mejor? | {'Sí' if mono_drawdown else 'No'} |
| ¿La clasificación es estable en el tiempo? | Jaccard medio de seleccionados: {_pct(stability['mean_selected_jaccard'])}; mínimo: {_pct(stability['min_selected_jaccard'])}; universo candidato Jaccard medio: {_pct(stability['mean_candidate_jaccard'])}. |
| ¿Pesimista y optimista divergen demasiado? | Ver tabla de divergencia; si el acuerdo de categoría es bajo o el Jaccard de seleccionados cae, la clasificación no es robusta al modo de asignación. |
| ¿El veto ayuda o destruye clasificaciones? | {veto_answer} |

## Divergencia pesimista/optimista y efecto del veto

{_markdown_table(divergence_display, ["comparison", "folds", "mean_category_agreement", "mean_selected_jaccard", "mean_rank_change", "total_downgrades", "total_upgrades"])}

## Estabilidad temporal

- Jaccard medio de seleccionados entre folds consecutivos: **{_pct(stability['mean_selected_jaccard'])}**.
- Jaccard mínimo de seleccionados: **{_pct(stability['min_selected_jaccard'])}**.
- Jaccard medio del universo candidato: **{_pct(stability['mean_candidate_jaccard'])}**.

Un Jaccard de seleccionados bajo indica que la etapa ELECTRE está rotando demasiado los ETFs clasificados como excelentes; eso puede dañar el portafolio aun si cada clasificación individual parece razonable.

## Transiciones de categoría más frecuentes

{_markdown_table(top_transition, ["from_category", "to_category", "transition_count", "transition_probability"])}

## Interpretación para la tesis

1. Este diagnóstico separa la tesis metodológica en dos capas: **calidad de clasificación MCDM** y **performance del portafolio**.
2. Si `above_preferred` no domina a `between_minimum_preferred` en retorno/Sharpe/drawdown forward, el blocker principal está antes de la optimización: criterios, perfiles, pesos, umbrales o modo ELECTRE.
3. Si la clasificación sí es monotónica pero el portafolio pierde, el blocker está más probablemente en asignación de pesos, concentración, rebalanceo o costos.
4. La evidencia sigue siendo `public_approximate_pit`, no PIT comercial survivorship-bias-free; por tanto es útil para diagnóstico de tesis, pero no para una claim final de performance institucional.
"""
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ELECTRE classification diagnostics from fold-level artifacts.")
    parser.add_argument("--results-dir", type=Path, default=Path("results/pit_integration_baseline/new_public_approximate_pit_universe"))
    parser.add_argument("--prices", type=Path, default=Path("data/raw/yfinance_pilot_2015_2025/close.parquet"))
    parser.add_argument("--out", type=Path, default=Path("results/electre_classification_diagnostics"))
    parser.add_argument("--report", type=Path, default=Path("docs/results/electre_classification_diagnostics.md"))
    parser.add_argument("--lambda-cut", type=float, default=0.75)
    args = parser.parse_args()

    write_classification_diagnostics(args.results_dir, args.prices, args.out, lambda_cut=args.lambda_cut)
    build_report(args.out, args.report)
    print(f"Wrote classification diagnostics to {args.out}")
    print(f"Wrote report to {args.report}")


if __name__ == "__main__":
    main()
