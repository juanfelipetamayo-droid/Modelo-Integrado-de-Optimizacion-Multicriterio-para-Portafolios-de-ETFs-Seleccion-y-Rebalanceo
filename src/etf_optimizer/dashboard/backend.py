from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from etf_optimizer.portfolio.composer import TargetPortfolio, compose_target_portfolio

CSV_ARTIFACTS = (
    "strategy_comparison.csv",
    "equity_curves.csv",
    "drawdowns.csv",
    "eligible_universe.csv",
    "filter_funnel.csv",
    "electre_selection.csv",
    "electre_selection_by_rebalance.csv",
    "electre_weights.csv",
    "coverage_report.csv",
    "bootstrap_metric_intervals.csv",
    "cost_sensitivity.csv",
    "electre_sensitivity.csv",
    "fold_diagnostics.csv",
)
TEXT_ARTIFACTS = (
    "methodology_report.md",
    "run_manifest.json",
    "provenance.json",
    "fold_diagnostics.json",
    "data_quality_verdict.json",
)
REQUIRED_ARTIFACTS = ("strategy_comparison.csv", "filter_funnel.csv", "run_manifest.json")


@dataclass(frozen=True)
class ArtifactStatus:
    name: str
    path: Path
    exists: bool
    size_bytes: int


@dataclass(frozen=True)
class CommandSpec:
    label: str
    argv: list[str]
    cwd: Path = Path(".")

    @property
    def preview(self) -> str:
        return " ".join(self.argv)


@dataclass(frozen=True)
class CommandResult:
    spec: CommandSpec
    returncode: int
    output: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class DashboardState:
    results_dir: Path
    artifacts: dict[str, ArtifactStatus]
    tables: dict[str, pd.DataFrame]
    manifest: dict[str, Any]
    provenance: dict[str, Any]
    data_quality: dict[str, Any]
    methodology: str
    metrics: dict[str, Any]

    @property
    def is_ready(self) -> bool:
        return all(self.artifacts[name].exists for name in REQUIRED_ARTIFACTS)


def artifact_status(results_dir: Path) -> dict[str, ArtifactStatus]:
    statuses: dict[str, ArtifactStatus] = {}
    for name in (*CSV_ARTIFACTS, *TEXT_ARTIFACTS):
        path = results_dir / name
        statuses[name] = ArtifactStatus(
            name=name,
            path=path,
            exists=path.exists(),
            size_bytes=path.stat().st_size if path.exists() else 0,
        )
    return statuses


def _read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _table_key(path_name: str) -> str:
    return Path(path_name).stem


def _metrics_from_tables(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    comparison = tables.get("strategy_comparison", pd.DataFrame())
    funnel = tables.get("filter_funnel", pd.DataFrame())
    selection_trace = tables.get("electre_selection_by_rebalance", pd.DataFrame())

    strategies = len(comparison)
    best_strategy = "not available"
    if not comparison.empty and {"strategy", "sharpe"}.issubset(comparison.columns):
        best_idx = comparison["sharpe"].astype(float).idxmax()
        best_strategy = str(comparison.loc[best_idx, "strategy"])

    final_eligible = 0
    if not funnel.empty and {"stage", "count"}.issubset(funnel.columns):
        final_rows = funnel.loc[funnel["stage"] == "final_eligible", "count"]
        final_eligible = int(final_rows.iloc[0]) if not final_rows.empty else 0

    rebalance_windows = 0
    if not selection_trace.empty and "rebalance_date" in selection_trace.columns:
        rebalance_windows = int(selection_trace["rebalance_date"].nunique())

    return {
        "strategies": strategies,
        "best_strategy": best_strategy,
        "final_eligible": final_eligible,
        "rebalance_windows": rebalance_windows,
        "artifacts_loaded": len(tables),
    }


def load_dashboard_state(results_dir: Path | str) -> DashboardState:
    resolved = Path(results_dir)
    artifacts = artifact_status(resolved)
    tables: dict[str, pd.DataFrame] = {}
    for name in CSV_ARTIFACTS:
        table = _read_csv(resolved / name)
        if table is not None:
            tables[_table_key(name)] = table

    manifest = _read_json(resolved / "run_manifest.json")
    provenance = _read_json(resolved / "provenance.json")
    data_quality = _read_json(resolved / "data_quality_verdict.json")
    methodology = _read_text(resolved / "methodology_report.md")
    metrics = _metrics_from_tables(tables)

    return DashboardState(
        results_dir=resolved,
        artifacts=artifacts,
        tables=tables,
        manifest=manifest,
        provenance=provenance,
        data_quality=data_quality,
        methodology=methodology,
        metrics=metrics,
    )


def build_target_portfolio_from_state(
    state: DashboardState,
    *,
    capital: float,
    risk_profile: str,
    max_positions: int | None = None,
) -> TargetPortfolio | None:
    weights = state.tables.get("electre_weights")
    universe = state.tables.get("eligible_universe")
    if weights is None or universe is None or weights.empty or universe.empty:
        return None
    prepared_weights = weights.copy()
    if "date" in prepared_weights.columns:
        prepared_weights = prepared_weights.set_index("date")
    unnamed_columns = [col for col in prepared_weights.columns if str(col).startswith("Unnamed:")]
    if unnamed_columns:
        prepared_weights = prepared_weights.set_index(unnamed_columns[0])
    return compose_target_portfolio(
        prepared_weights,
        universe,
        capital=capital,
        risk_profile=risk_profile,
        max_positions=max_positions,
    )


def build_universe_command(out: Path | str) -> CommandSpec:
    return CommandSpec(
        label="Build ETF universe",
        argv=["uv", "run", "python", "scripts/build_universe.py", "--out", str(out)],
    )


def build_download_command(
    *,
    universe: Path | str,
    start: str,
    end: str,
    out: Path | str,
    batch_size: int,
    max_retries: int,
    limit: int | None,
) -> CommandSpec:
    argv = [
        "uv",
        "run",
        "python",
        "scripts/download_data.py",
        "--universe",
        str(universe),
        "--start",
        start,
        "--end",
        end,
        "--out",
        str(out),
        "--batch-size",
        str(batch_size),
        "--max-retries",
        str(max_retries),
    ]
    if limit is not None:
        argv.extend(["--limit", str(limit)])
    return CommandSpec(label="Download Yahoo Finance data", argv=argv)


def build_pipeline_command(*, prices: Path | str, volume: Path | str | None, out: Path | str) -> CommandSpec:
    argv = ["uv", "run", "python", "scripts/run_pipeline.py", "--prices", str(prices)]
    if volume is not None:
        argv.extend(["--volume", str(volume)])
    argv.extend(["--out", str(out)])
    return CommandSpec(label="Run MVP pipeline", argv=argv)


def build_sprint_command(
    *,
    universe: Path | str,
    prices: Path | str | None,
    volume: Path | str | None,
    start: str,
    end: str,
    rebalance: str,
    cost_bps: float,
    out: Path | str,
    min_coverage_pct: float,
    min_avg_dollar_volume: float,
) -> CommandSpec:
    argv = [
        "uv",
        "run",
        "python",
        "scripts/run_sprint_experiment.py",
        "--universe",
        str(universe),
        "--start",
        start,
        "--end",
        end,
        "--rebalance",
        rebalance,
        "--cost-bps",
        str(cost_bps),
        "--out",
        str(out),
        "--min-coverage-pct",
        str(min_coverage_pct),
        "--min-avg-dollar-volume",
        str(min_avg_dollar_volume),
    ]
    if prices is not None:
        argv.extend(["--prices", str(prices)])
    if volume is not None:
        argv.extend(["--volume", str(volume)])
    return CommandSpec(label="Run sprint experiment", argv=argv)


def run_command(spec: CommandSpec, *, timeout_seconds: int = 3600) -> CommandResult:
    completed = subprocess.run(
        spec.argv,
        cwd=spec.cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_seconds,
        check=False,
    )
    return CommandResult(spec=spec, returncode=completed.returncode, output=completed.stdout)
