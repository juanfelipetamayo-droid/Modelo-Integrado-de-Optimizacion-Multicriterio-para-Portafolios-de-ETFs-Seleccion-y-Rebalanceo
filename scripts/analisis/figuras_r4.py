"""Figuras de resultados para R4 (especificación principal: universo completo, tope de 25 ETFs).

Uso: uv run python data/rerun/figuras_r4.py <carpeta_salida>
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RUNS = {
    "principal": "results_rerun/tope25_primary_2021_2025",
    "ampliada": "results_rerun/tope25_extended_2015_2025",
    "2026": "results_rerun/tope25_oos2026",
}
SERIES = {
    "ELECTRE_EqualWeight_walk_forward": ("ELECTRE equiponderado", "#1f77b4", 2.4),
    "ELECTRE_MinVariance_walk_forward": ("ELECTRE mínima varianza", "#0b4f6c", 2.4),
    "SPY_buy_hold": ("SPY comprar y mantener", "#d62728", 2.0),
    "60/40_SPY_BND_fixed_weight": ("Cartera 60/40 SPY-BND", "#2ca02c", 2.0),
    "Universe_EqualWeight_walk_forward": ("Universo equiponderado", "#9467bd", 2.0),
}
TITLES = {"principal": "Prueba principal 2021–2025", "ampliada": "Evaluación ampliada 2015–2025", "2026": "Prueba fuera de muestra 2026"}
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def line_figure(run: str, csv: str, ylabel: str, name: str, title_suffix: str, baseline: float) -> None:
    data = pd.read_csv(Path(RUNS[run], csv), index_col=0, parse_dates=True)
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=200)
    for column, (label, color, width) in SERIES.items():
        ax.plot(data.index, data[column], label=label, color=color, linewidth=width)
    ax.axhline(baseline, color="grey", linewidth=0.8)
    ax.set_title(f"{TITLES[run]}: {title_suffix}")
    ax.set_xlabel("Fecha")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3, linestyle="--")
    ax.legend(frameon=False, ncol=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / name)
    plt.close(fig)


line_figure("principal", "equity_curves.csv", "Crecimiento de 1 unidad monetaria", "r4_capital_principal.png", "curvas de capital", 1.0)
line_figure("ampliada", "equity_curves.csv", "Crecimiento de 1 unidad monetaria", "r4_capital_ampliada.png", "curvas de capital", 1.0)
line_figure("ampliada", "drawdowns.csv", "Caída desde el máximo previo", "r4_caidas_ampliada.png", "caídas acumuladas", 0.0)
line_figure("2026", "equity_curves.csv", "Crecimiento de 1 unidad monetaria", "r4_capital_2026.png", "curvas de capital", 1.0)

# Controles aleatorios: distribución del Sharpe en exceso sobre BIL de 100 selecciones aleatorias.
close = pd.read_parquet("data/raw/yfinance_universo_completo_2015_2026/close.parquet", columns=["BIL"])
bil = close["BIL"].resample("ME").last().pct_change()


def sharpe_bil(x: pd.Series) -> float:
    excess = x - bil.reindex(x.index)
    return float(excess.mean() / excess.std() * np.sqrt(12))


def reference_sharpe(run: str, column: str) -> float:
    equity = pd.read_csv(Path(RUNS[run], "equity_curves.csv"), index_col=0, parse_dates=True)[column]
    returns = equity.pct_change()
    returns.iloc[0] = equity.iloc[0] - 1.0
    return sharpe_bil(returns)


files = {"principal": "primary", "ampliada": "extended", "2026": "oos2026"}
fig, axes = plt.subplots(2, 3, figsize=(12, 6.6), dpi=200)
for col, run in enumerate(RUNS):
    returns = pd.read_csv(f"results_rerun/controles_seleccion_{files[run]}_retornos_10pb.csv", index_col=0, parse_dates=True)
    spy = reference_sharpe(run, "SPY_buy_hold")
    for row, (allocation, label) in enumerate([("equal_weight", "equiponderada"), ("min_variance", "mínima varianza")]):
        ax = axes[row, col]
        random = returns[[c for c in returns.columns if c.startswith("aleatoria") and c.endswith(allocation)]].apply(sharpe_bil)
        electre = sharpe_bil(returns[f"electre|{allocation}"])
        pct = (random < electre).mean() * 100
        ax.hist(random, bins=18, color="#bbbbbb", edgecolor="white")
        ax.axvline(electre, color="#1f77b4", linewidth=2.2, label=f"ELECTRE (percentil {pct:.0f})")
        ax.axvline(spy, color="#d62728", linewidth=1.8, linestyle="--", label="SPY")
        ax.set_title(f"{TITLES[run]}\nasignación {label}", fontsize=9.5)
        ax.legend(frameon=False, fontsize=7.5, loc="best")
        if col == 0:
            ax.set_ylabel("Selecciones aleatorias", fontsize=9)
        if row == 1:
            ax.set_xlabel("Sharpe en exceso sobre BIL", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "r4_controles_aleatorios.png")
plt.close(fig)
print("ok")
