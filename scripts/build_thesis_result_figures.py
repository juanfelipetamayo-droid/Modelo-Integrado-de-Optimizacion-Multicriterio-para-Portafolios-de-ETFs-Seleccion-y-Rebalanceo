from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_PRIMARY = Path("results/thesis_primary_2021_2025_run_no_cap")
DEFAULT_EXTENDED = Path("results/thesis_extended_2015_2025_run_no_cap")
DEFAULT_OUT = Path("docs/figures/thesis_results")

CORE_STRATEGIES = [
    "ELECTRE_EqualWeight_walk_forward",
    "ELECTRE_MinVariance_walk_forward",
    "SPY_buy_hold",
    "60/40_SPY_BND_fixed_weight",
    "Universe_EqualWeight_walk_forward",
]

STRATEGY_LABELS = {
    "ELECTRE_EqualWeight_walk_forward": "ELECTRE + EqualWeight",
    "ELECTRE_MinVariance_walk_forward": "ELECTRE + MinVariance",
    "ELECTRE_MaxSharpe_walk_forward": "ELECTRE + MaxSharpe",
    "SPY_buy_hold": "SPY buy & hold",
    "60/40_SPY_BND_fixed_weight": "60/40 SPY/BND",
    "Universe_EqualWeight_walk_forward": "Universe EqualWeight",
    "MinVariance_walk_forward": "Universe MinVariance",
    "MaxSharpe_walk_forward": "Universe MaxSharpe",
}

COLORS = {
    "ELECTRE_EqualWeight_walk_forward": "#1f77b4",
    "ELECTRE_MinVariance_walk_forward": "#0f5b78",
    "ELECTRE_MaxSharpe_walk_forward": "#5dade2",
    "SPY_buy_hold": "#d62728",
    "60/40_SPY_BND_fixed_weight": "#2ca02c",
    "Universe_EqualWeight_walk_forward": "#9467bd",
    "MinVariance_walk_forward": "#8c564b",
    "MaxSharpe_walk_forward": "#ff7f0e",
}

CATEGORY_ORDER = ["below_minimum", "between_minimum_preferred", "above_preferred"]
CATEGORY_LABELS = {
    "below_minimum": "Rechazados",
    "between_minimum_preferred": "Aceptables",
    "above_preferred": "Excelentes",
}


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def _read_csv(path: Path, *, date_col: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
    return df


def _save(fig: plt.Figure, out_dir: Path, name: str, created: list[Path]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for suffix in [".png", ".pdf"]:
        path = out_dir / f"{name}{suffix}"
        fig.savefig(path, bbox_inches="tight", facecolor="white")
        created.append(path)
    plt.close(fig)


def _pct_axis(ax: plt.Axes) -> None:
    ax.yaxis.set_major_formatter(lambda x, _pos: f"{x:.0%}")


def _available(columns: pd.Index, names: list[str]) -> list[str]:
    return [name for name in names if name in columns]


def plot_equity_curves(result_dir: Path, out_dir: Path, prefix: str, title: str, created: list[Path]) -> None:
    equity = _read_csv(result_dir / "equity_curves.csv", date_col="date")
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    for strategy in _available(equity.columns, CORE_STRATEGIES):
        ax.plot(
            equity["date"],
            equity[strategy],
            label=STRATEGY_LABELS.get(strategy, strategy),
            color=COLORS.get(strategy),
            linewidth=2.3 if strategy.startswith("ELECTRE") else 2.0,
        )
    ax.axhline(1.0, color="#444444", linewidth=0.8, alpha=0.6)
    ax.set_title(title)
    ax.set_ylabel("Crecimiento de 1 unidad monetaria")
    ax.set_xlabel("Fecha")
    ax.legend(loc="upper left", ncols=2, frameon=False)
    _save(fig, out_dir, f"{prefix}_01_equity_curves", created)


def plot_drawdowns(result_dir: Path, out_dir: Path, prefix: str, title: str, created: list[Path]) -> None:
    drawdowns = _read_csv(result_dir / "drawdowns.csv", date_col="date")
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    for strategy in _available(drawdowns.columns, CORE_STRATEGIES):
        ax.plot(
            drawdowns["date"],
            drawdowns[strategy],
            label=STRATEGY_LABELS.get(strategy, strategy),
            color=COLORS.get(strategy),
            linewidth=2.2 if strategy.startswith("ELECTRE") else 1.9,
        )
    ax.axhline(0.0, color="#444444", linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel("Drawdown")
    ax.set_xlabel("Fecha")
    _pct_axis(ax)
    ax.legend(loc="lower left", ncols=2, frameon=False)
    _save(fig, out_dir, f"{prefix}_02_drawdowns", created)


def plot_risk_return(result_dir: Path, out_dir: Path, prefix: str, title: str, created: list[Path]) -> None:
    comparison = _read_csv(result_dir / "strategy_comparison.csv")
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    sizes = 90 + 80 * comparison["sharpe"].clip(lower=0).fillna(0)
    for _, row in comparison.iterrows():
        strategy = str(row["strategy"])
        ax.scatter(
            row["volatility"],
            row["cagr"],
            s=sizes.loc[row.name],
            color=COLORS.get(strategy, "#666666"),
            alpha=0.82,
            edgecolor="white",
            linewidth=0.8,
        )
        ax.annotate(
            STRATEGY_LABELS.get(strategy, strategy),
            (row["volatility"], row["cagr"]),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=8.4,
        )
    ax.set_title(title)
    ax.set_xlabel("Volatilidad anualizada")
    ax.set_ylabel("CAGR")
    ax.xaxis.set_major_formatter(lambda x, _pos: f"{x:.0%}")
    _pct_axis(ax)
    ax.text(
        0.02,
        0.02,
        "Tamaño del punto ≈ Sharpe Ratio",
        transform=ax.transAxes,
        fontsize=9,
        color="#555555",
    )
    _save(fig, out_dir, f"{prefix}_03_risk_return_scatter", created)


def plot_metric_dashboard(result_dir: Path, out_dir: Path, prefix: str, title: str, created: list[Path]) -> None:
    comparison = _read_csv(result_dir / "strategy_comparison.csv")
    selected = comparison[comparison["strategy"].isin(CORE_STRATEGIES)].copy()
    selected["label"] = selected["strategy"].map(STRATEGY_LABELS)
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.2))
    metrics = [("cagr", "CAGR", True), ("sharpe", "Sharpe Ratio", False), ("max_drawdown", "Max drawdown", True)]
    for ax, (metric, label, pct) in zip(axes, metrics, strict=False):
        values = selected[metric]
        colors = [COLORS.get(strategy, "#666666") for strategy in selected["strategy"]]
        ax.barh(selected["label"], values, color=colors, alpha=0.88)
        ax.set_title(label)
        if pct:
            ax.xaxis.set_major_formatter(lambda x, _pos: f"{x:.0%}")
        if metric == "max_drawdown":
            ax.axvline(0, color="#333333", linewidth=0.8)
    fig.suptitle(title, y=1.03, fontsize=14)
    fig.tight_layout()
    _save(fig, out_dir, f"{prefix}_04_metric_dashboard", created)


def plot_selection_cardinality(result_dir: Path, out_dir: Path, prefix: str, title: str, created: list[Path]) -> None:
    selection = _read_csv(result_dir / "electre_selection_by_rebalance.csv", date_col="rebalance_date")
    counts = selection.loc[selection["selected"].astype(bool)].groupby("rebalance_date")["ticker"].nunique()
    all_dates = pd.Index(sorted(selection["rebalance_date"].dropna().unique()))
    counts = counts.reindex(all_dates, fill_value=0)
    fig, ax = plt.subplots(figsize=(10.5, 5.3))
    ax.fill_between(counts.index, 10, 25, color="#2ca02c", alpha=0.12, label="Rango objetivo 10–25")
    ax.plot(counts.index, counts.values, marker="o", color="#1f77b4", linewidth=2.2, label="ETFs seleccionados")
    ax.axhline(10, color="#2ca02c", linewidth=1, linestyle="--")
    ax.axhline(25, color="#2ca02c", linewidth=1, linestyle="--")
    ax.set_title(title)
    ax.set_ylabel("Número de ETFs seleccionados")
    ax.set_xlabel("Rebalanceo")
    ax.legend(frameon=False)
    _save(fig, out_dir, f"{prefix}_05_selection_cardinality", created)


def plot_classification_effectiveness(primary: Path, extended: Path, out_dir: Path, created: list[Path]) -> None:
    frames = []
    for label, result_dir in [("Principal 2021–2025", primary), ("Extendida 2015–2025", extended)]:
        path = result_dir / "electre_classification_diagnostics" / "classification_effectiveness.csv"
        df = _read_csv(path)
        df["run"] = label
        df["category_label"] = df["category"].map(CATEGORY_LABELS)
        df["category"] = pd.Categorical(df["category"], categories=CATEGORY_ORDER, ordered=True)
        frames.append(df.sort_values("category"))
    data = pd.concat(frames, ignore_index=True)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), sharex=True)
    for ax, metric, label in [
        (axes[0], "mean_forward_sharpe", "Sharpe forward promedio"),
        (axes[1], "mean_forward_cumulative_return", "Retorno forward acumulado promedio"),
    ]:
        pivot = data.pivot(index="category_label", columns="run", values=metric).reindex(
            [CATEGORY_LABELS[c] for c in CATEGORY_ORDER]
        )
        pivot.plot(kind="bar", ax=ax, color=["#1f77b4", "#9467bd"], alpha=0.88)
        ax.set_title(label)
        ax.set_xlabel("Categoría ELECTRE")
        ax.legend(frameon=False)
        if "return" in metric:
            ax.yaxis.set_major_formatter(lambda x, _pos: f"{x:.1%}")
    fig.suptitle("Efectividad ordinal de la clasificación ELECTRE", y=1.03, fontsize=14)
    fig.tight_layout()
    _save(fig, out_dir, "combined_06_classification_effectiveness", created)


def plot_compliance_status(primary: Path, extended: Path, out_dir: Path, created: list[Path]) -> None:
    status_rank = {
        "fulfilled": 3,
        "complete": 3,
        "thesis_aligned_principal": 3,
        "extended_robustness_not_replacement": 2,
        "near-fulfilled": 2,
        "partial": 1,
        "not fulfilled operationally": 0,
        "not empirically validated": 0,
    }
    labels = {
        "general": "Obj. general",
        "specific_1": "Obj. 1",
        "specific_2": "Obj. 2",
        "specific_3": "Obj. 3",
        "temporal_protocol": "Protocolo",
        "benchmark_set": "Benchmarks",
    }
    frames = []
    for run, result_dir in [("Principal", primary), ("Extendida", extended)]:
        df = _read_csv(result_dir / "objective_compliance_summary.csv")
        df["run"] = run
        df["score"] = df["status"].map(status_rank).fillna(1)
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    pivot = data.pivot(index="objective", columns="run", values="score").reindex(labels.keys())
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    image = ax.imshow(pivot.values, cmap=plt.get_cmap("RdYlGn"), vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), [labels.get(idx, idx) for idx in pivot.index])
    for i, objective in enumerate(pivot.index):
        for j, run in enumerate(pivot.columns):
            status = data.loc[(data["objective"] == objective) & (data["run"] == run), "status"].iloc[0]
            ax.text(j, i, status, ha="center", va="center", fontsize=8, color="#111111")
    ax.set_title("Estado de cumplimiento por objetivo")
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_ticks([0, 1, 2, 3], labels=["No", "Parcial", "Robustez/Casi", "Cumple"])
    _save(fig, out_dir, "combined_07_objective_compliance", created)


def build_figures(primary: Path, extended: Path, out_dir: Path) -> list[Path]:
    _setup_style()
    created: list[Path] = []
    plot_equity_curves(primary, out_dir, "primary", "Protocolo principal 2021–2025: curvas de capital", created)
    plot_drawdowns(primary, out_dir, "primary", "Protocolo principal 2021–2025: drawdowns", created)
    plot_risk_return(primary, out_dir, "primary", "Protocolo principal 2021–2025: mapa riesgo–retorno", created)
    plot_metric_dashboard(primary, out_dir, "primary", "Protocolo principal 2021–2025: métricas clave", created)
    plot_selection_cardinality(primary, out_dir, "primary", "Protocolo principal: cardinalidad de selección ELECTRE", created)

    plot_equity_curves(extended, out_dir, "extended", "Validación extendida 2015–2025: curvas de capital", created)
    plot_drawdowns(extended, out_dir, "extended", "Validación extendida 2015–2025: drawdowns", created)
    plot_risk_return(extended, out_dir, "extended", "Validación extendida 2015–2025: mapa riesgo–retorno", created)
    plot_metric_dashboard(extended, out_dir, "extended", "Validación extendida 2015–2025: métricas clave", created)
    plot_selection_cardinality(extended, out_dir, "extended", "Validación extendida: cardinalidad de selección ELECTRE", created)

    plot_classification_effectiveness(primary, extended, out_dir, created)
    plot_compliance_status(primary, extended, out_dir, created)
    write_index(out_dir, created)
    return created


def write_index(out_dir: Path, created: list[Path]) -> None:
    pngs = [path for path in created if path.suffix == ".png"]
    lines = [
        "# Figuras de resultados de tesis",
        "",
        "Estas figuras se generan con `scripts/build_thesis_result_figures.py` a partir de los resultados principal y extendido.",
        "",
        "## Figuras generadas",
        "",
    ]
    for path in sorted(pngs):
        lines.append(f"- `{path.name}`")
    lines.extend(
        [
            "",
            "## Uso recomendado en el documento",
            "",
            "- Curvas de capital: desempeño acumulado y comparación visual contra benchmarks.",
            "- Drawdowns: control de pérdidas y riesgo de caída.",
            "- Riesgo–retorno: síntesis de CAGR, volatilidad y Sharpe.",
            "- Métricas clave: comparación directa de CAGR, Sharpe y max drawdown.",
            "- Cardinalidad: cumplimiento del rango objetivo 10–25 activos.",
            "- Efectividad ELECTRE: validación ordinal de categorías.",
            "- Cumplimiento por objetivo: síntesis metodológica para conclusiones.",
            "",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build thesis-ready result figures.")
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--extended", type=Path, default=DEFAULT_EXTENDED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    created = build_figures(args.primary, args.extended, args.out)
    print(f"Generated {len(created)} figure files in {args.out}")
    for path in created:
        print(path)


if __name__ == "__main__":
    main()
