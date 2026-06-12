from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from etf_optimizer.reporting.selection_allocation_ablation import (
    run_selection_allocation_ablation,
    write_selection_allocation_ablation,
)


def _pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.2%}"


def _num(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.3f}"


def _markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sin datos._"
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df[columns].iterrows():
        rows.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(rows)


def build_report(output_dir: Path, report_path: Path) -> None:
    grid = pd.read_csv(output_dir / "ablation_grid.csv")
    display = grid.copy()
    for col in ["cagr", "volatility", "max_drawdown", "avg_turnover"]:
        if col in display.columns:
            display[col] = display[col].map(_pct)
    for col in ["sharpe", "sortino", "calmar"]:
        if col in display.columns:
            display[col] = display[col].map(_num)

    core_order = [
        "Universe_EqualWeight_walk_forward",
        "Universe_MinVariance_walk_forward",
        "Universe_MaxSharpe_walk_forward",
        "ELECTRE_pessimistic_no_veto_EqualWeight_walk_forward",
        "ELECTRE_pessimistic_no_veto_InverseVol_walk_forward",
        "ELECTRE_pessimistic_no_veto_MinVariance_walk_forward",
        "ELECTRE_pessimistic_no_veto_MaxSharpe_walk_forward",
    ]
    core = display[display["strategy"].isin(core_order)].copy()
    core["_order"] = core["strategy"].map({name: idx for idx, name in enumerate(core_order)})
    core = core.sort_values("_order").drop(columns=["_order"])

    variant = display[(display["selection"] == "electre") & (display["allocation"] == "equal_weight")].copy()
    variant = variant.sort_values(["assignment", "use_veto"])

    raw = grid.set_index("strategy")
    def metric(strategy: str, col: str) -> float:
        return float(raw.loc[strategy, col]) if strategy in raw.index and col in raw.columns else float("nan")

    universe_eq = "Universe_EqualWeight_walk_forward"
    universe_max = "Universe_MaxSharpe_walk_forward"
    electre_eq = "ELECTRE_pessimistic_no_veto_EqualWeight_walk_forward"
    electre_max = "ELECTRE_pessimistic_no_veto_MaxSharpe_walk_forward"
    selection_delta = metric(electre_eq, "cagr") - metric(universe_eq, "cagr")
    maxsharpe_delta = metric(electre_max, "cagr") - metric(electre_eq, "cagr")
    universe_max_delta = metric(universe_max, "cagr") - metric(universe_eq, "cagr")

    if selection_delta > 0:
        selection_answer = "ELECTRE EqualWeight mejora vs Universe EqualWeight: la selección agrega valor en este baseline."
    else:
        selection_answer = "ELECTRE EqualWeight pierde contra Universe EqualWeight: la clasificación no está agregando valor neto."
    if metric(electre_eq, "cagr") > 0 and maxsharpe_delta < 0:
        allocation_answer = "ELECTRE EqualWeight es positivo, pero ELECTRE MaxSharpe cae: MaxSharpe destruye parte de la selección."
    elif maxsharpe_delta < 0:
        allocation_answer = "ELECTRE MaxSharpe es peor que ELECTRE EqualWeight: la asignación MaxSharpe empeora la selección."
    else:
        allocation_answer = "ELECTRE MaxSharpe no empeora a ELECTRE EqualWeight en CAGR."
    if universe_max_delta < 0:
        optimizer_answer = "Universe MaxSharpe también cae vs Universe EqualWeight: hay evidencia de problema de optimización/estimación de retornos."
    else:
        optimizer_answer = "Universe MaxSharpe no cae vs Universe EqualWeight: el daño parece más ligado a selección o interacción selección-asignación."

    best = grid.sort_values("cagr", ascending=False).head(5).copy()
    best_display = best.copy()
    for col in ["cagr", "volatility", "max_drawdown", "avg_turnover"]:
        if col in best_display.columns:
            best_display[col] = best_display[col].map(_pct)
    for col in ["sharpe", "sortino", "calmar"]:
        if col in best_display.columns:
            best_display[col] = best_display[col].map(_num)

    report = f"""# Ablation tests: selección ELECTRE vs asignación de pesos

**Objetivo:** responder si el problema viene de la selección ELECTRE o de la asignación MaxSharpe. La corrida usa el baseline `public_approximate_pit`, ventana 2015–2025, folds trimestrales 36/3/3, `buy_and_hold`, costo 10 bps y los mismos fold-stage artifacts generados previamente.

## Artefactos

- `results/ablation_selection_allocation/strategy_comparison.csv`
- `results/ablation_selection_allocation/ablation_grid.csv`
- `results/ablation_selection_allocation/strategy_returns.csv`
- `results/ablation_selection_allocation/equity_curves.csv`
- `results/ablation_selection_allocation/drawdowns.csv`
- `results/ablation_selection_allocation/turnover_summary.csv`

## Experimentos mínimos selección/asignación

{_markdown_table(core, ["strategy", "selection", "allocation", "assignment", "use_veto", "cagr", "sharpe", "max_drawdown", "avg_turnover"])}

## Modos ELECTRE pesimista/optimista con/sin veto — asignación EqualWeight

{_markdown_table(variant, ["strategy", "assignment", "use_veto", "cagr", "sharpe", "max_drawdown", "avg_turnover"])}

## Mejores 5 variantes por CAGR

{_markdown_table(best_display, ["strategy", "selection", "allocation", "assignment", "use_veto", "cagr", "sharpe", "max_drawdown"])}

## Interpretación según reglas del GOAL 9

| Regla | Resultado |
|---|---|
| Si ELECTRE EqualWeight mejora vs Universe EqualWeight, la selección tiene valor. | {selection_answer} Delta CAGR: {_pct(selection_delta)}. |
| Si ELECTRE EqualWeight funciona, pero ELECTRE MaxSharpe cae, MaxSharpe destruye la selección. | {allocation_answer} Delta CAGR MaxSharpe - EqualWeight: {_pct(maxsharpe_delta)}. |
| Si ELECTRE EqualWeight pierde contra Universe EqualWeight, la clasificación no agrega valor. | {'Aplica.' if selection_delta < 0 else 'No aplica.'} |
| Si Universe MaxSharpe también cae, el problema está en optimización/estimación de retornos. | {optimizer_answer} Delta CAGR Universe MaxSharpe - Universe EqualWeight: {_pct(universe_max_delta)}. |

## Conclusión

La lectura prioritaria debe separar tres capas:

1. **Selección:** comparación `ELECTRE_pessimistic_no_veto_EqualWeight` vs `Universe_EqualWeight`.
2. **Asignación:** comparación de `EqualWeight`, `InverseVol`, `MinVariance` y `MaxSharpe` manteniendo la misma selección ELECTRE.
3. **Modo ELECTRE:** comparación pesimista/optimista y veto/no-veto manteniendo EqualWeight para no mezclar la prueba de clasificación con ruido de optimización.

Si la clasificación no mejora al universo en EqualWeight, el siguiente hito debe rediseñar criterios/perfiles/umbrales antes de volver a optimizar pesos. Si sí mejora pero MaxSharpe deteriora, el siguiente hito debe reemplazar MaxSharpe por asignadores robustos o regularizados.

**Caveat:** la evidencia usa universo `public_approximate_pit` y precios públicos; es diagnóstico de tesis, no claim institucional survivorship-bias-free.
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run selection-vs-allocation ablations for ELECTRE ETF strategy.")
    parser.add_argument("--prices", type=Path, default=Path("data/raw/yfinance_pilot_2015_2025/close.parquet"))
    parser.add_argument("--baseline-results-dir", type=Path, default=Path("results/pit_integration_baseline/new_public_approximate_pit_universe"))
    parser.add_argument("--out", type=Path, default=Path("results/ablation_selection_allocation"))
    parser.add_argument("--report", type=Path, default=Path("docs/results/selection_vs_allocation_ablation.md"))
    args = parser.parse_args()

    result = run_selection_allocation_ablation(args.prices, args.baseline_results_dir)
    write_selection_allocation_ablation(result, args.out)
    build_report(args.out, args.report)
    print(f"Wrote ablation results to {args.out}")
    print(f"Wrote report to {args.report}")


if __name__ == "__main__":
    main()
