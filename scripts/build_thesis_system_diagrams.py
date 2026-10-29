"""Generate system design diagrams for the thesis document.

The diagrams are intentionally simple and thesis-friendly: they avoid
tool-specific UML rendering dependencies and export both PNG and PDF files.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path("docs/figures/thesis_system")


def _box(ax, xy: tuple[float, float], text: str, width: float = 2.4, height: float = 0.75) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.035,rounding_size=0.04",
        linewidth=1.25,
        edgecolor="#1f3a5f",
        facecolor="#e9f1fb",
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=8.8)


def _arrow(ax, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.1,
            color="#30475e",
            shrinkA=4,
            shrinkB=4,
        )
    )


def _save(fig, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{name}.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)


def component_diagram() -> None:
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.set_title("Arquitectura por componentes del sistema", fontsize=13, weight="bold", pad=12)
    labels = [
        "Datos históricos\nprecios y volumen",
        "Preparación\nde paneles",
        "Cálculo de\ncriterios",
        "Clasificación\nELECTRE Tri",
        "Optimización\ny rebalanceo",
        "Backtesting y\nbenchmarks",
        "Reportes y\nfiguras",
    ]
    xs = [0.2, 2.2, 4.2, 6.2, 8.2, 10.2, 12.0]
    for x, label in zip(xs, labels, strict=True):
        _box(ax, (x, 1.75), label, width=1.75, height=0.9)
    for x in xs[:-1]:
        _arrow(ax, (x + 1.75, 2.2), (x + 2.0, 2.2))
    _save(fig, "system_11_component_diagram")


def use_case_diagram() -> None:
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Casos de uso principales", fontsize=13, weight="bold", pad=12)
    _box(ax, (4.0, 2.4), "Sistema ETF\nOptimizer", width=2.0, height=1.1)
    actors = {
        "Investigador / autor": (0.45, 4.5),
        "Evaluador académico": (0.45, 0.8),
        "Usuario técnico": (7.4, 2.6),
    }
    for label, pos in actors.items():
        _box(ax, pos, label, width=2.0, height=0.75)
    uses = [
        ("Configurar\nexperimento", (3.65, 4.7)),
        ("Ejecutar\nbacktesting", (6.1, 4.7)),
        ("Revisar\ncumplimiento", (3.65, 0.65)),
        ("Reproducir o\nextender modelo", (6.1, 0.65)),
    ]
    for label, pos in uses:
        _box(ax, pos, label, width=1.75, height=0.72)
    _arrow(ax, (2.45, 4.86), (3.65, 5.05))
    _arrow(ax, (2.45, 4.86), (6.1, 5.05))
    _arrow(ax, (2.45, 1.18), (3.65, 1.0))
    _arrow(ax, (7.4, 2.98), (6.95, 1.38))
    _arrow(ax, (4.52, 4.7), (4.92, 3.5))
    _arrow(ax, (6.98, 4.7), (5.5, 3.5))
    _arrow(ax, (4.52, 1.37), (4.85, 2.4))
    _arrow(ax, (6.95, 1.37), (5.55, 2.4))
    _save(fig, "system_12_use_cases")


def activity_diagram() -> None:
    fig, ax = plt.subplots(figsize=(8.8, 8.2))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title("Flujo principal de actividades", fontsize=13, weight="bold", pad=12)
    steps = [
        "Cargar datos históricos",
        "Aplicar filtros de cobertura y liquidez",
        "Calcular criterios financieros",
        "Clasificar ETFs con ELECTRE Tri",
        "Seleccionar activos elegibles",
        "Calcular pesos del portafolio",
        "Simular periodo out-of-sample",
        "Comparar contra benchmarks",
        "Generar reportes y evaluar objetivos",
    ]
    y = 8.9
    for idx, step in enumerate(steps):
        _box(ax, (2.35, y), step, width=3.3, height=0.58)
        if idx < len(steps) - 1:
            _arrow(ax, (4.0, y), (4.0, y - 0.48))
        y -= 0.95
    _save(fig, "system_13_activity_flow")


def main() -> None:
    component_diagram()
    use_case_diagram()
    activity_diagram()
    files = sorted(OUT_DIR.glob("*"))
    print(f"Generated {len(files)} diagram files in {OUT_DIR}")
    for file in files:
        print(file)


if __name__ == "__main__":
    main()
