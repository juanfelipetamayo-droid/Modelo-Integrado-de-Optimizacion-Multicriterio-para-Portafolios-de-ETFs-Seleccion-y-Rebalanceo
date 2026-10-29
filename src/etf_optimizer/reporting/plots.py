from __future__ import annotations

from pathlib import Path

import pandas as pd


def plot_equity_curves(
    equity_curves: pd.DataFrame,
    title: str = "Equity Curves",
    out_path: str | Path | None = None,
) -> str:
    """Generate an equity curves plot (placeholder that returns summary stats).
    
    Full plotting (matplotlib/plotly) will be added in a future sprint.
    """
    if equity_curves.empty:
        return "No data to plot."

    summary: list[str] = [f"=== {title} ==="]
    for col in equity_curves.columns:
        series = equity_curves[col].dropna()
        if not series.empty:
            summary.append(f"{col}: start={series.iloc[0]:.4f}, end={series.iloc[-1]:.4f}, "
                           f"max={series.max():.4f}, min={series.min():.4f}")

    text = "\n".join(summary)
    if out_path:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    return text


def coverage_plot_summary(
    coverage_report: pd.DataFrame,
    out_path: str | Path | None = None,
) -> str:
    """Generate a text summary of coverage (placeholder for future plots)."""
    if coverage_report.empty:
        return "No coverage data."

    text = coverage_report.to_string(index=False)
    if out_path:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    return text
