from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class MilestoneSpec:
    milestone: str
    result_dir: Path
    notes: str = ""


def _read_parameters(result_dir: Path) -> dict[str, object]:
    manifest_path = result_dir / "run_manifest.json"
    if not manifest_path.exists():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return dict(manifest.get("parameters", {}))


def collect_milestone_metrics(specs: list[MilestoneSpec]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in specs:
        comparison_path = spec.result_dir / "strategy_comparison.csv"
        if not comparison_path.exists():
            raise FileNotFoundError(f"missing strategy comparison: {comparison_path}")
        comparison = pd.read_csv(comparison_path)
        electre = comparison[comparison["strategy"].str.contains("ELECTRE", regex=False)].head(1)
        if electre.empty:
            raise ValueError(f"no ELECTRE row in {comparison_path}")
        row = electre.iloc[0].to_dict()
        events_path = spec.result_dir / "rebalance_events.csv"
        event_counts: dict[str, int] = {}
        total_turnover = 0.0
        if events_path.exists():
            events = pd.read_csv(events_path)
            if "event_type" in events.columns:
                event_counts = events["event_type"].value_counts().to_dict()
            if "turnover" in events.columns:
                total_turnover = float(events["turnover"].sum())
        parameters = _read_parameters(spec.result_dir)
        rows.append(
            {
                "milestone": spec.milestone,
                "result_dir": str(spec.result_dir),
                "cagr": row.get("cagr"),
                "sharpe": row.get("sharpe"),
                "max_drawdown": row.get("max_drawdown"),
                "volatility": row.get("volatility"),
                "calmar": row.get("calmar"),
                "total_turnover": total_turnover,
                "calendar_events": event_counts.get("calendar", 0),
                "threshold_events": event_counts.get("threshold", 0),
                "category_change_events": event_counts.get("category_change", 0),
                "rebalance": parameters.get("rebalance", ""),
                "weight_drift": parameters.get("weight_drift", ""),
                "rebalance_policy": parameters.get("rebalance_policy", ""),
                "recategorization_policy": parameters.get("recategorization_policy", ""),
                "turnover_penalty": parameters.get("turnover_penalty", 0.0),
                "category_confirmation_periods": parameters.get("category_confirmation_periods", 1),
                "category_change_min_score_improvement": parameters.get("category_change_min_score_improvement", 0.0),
                "category_exposure_cap": parameters.get("category_exposure_cap", ""),
                "electre_assignment": parameters.get("electre_assignment", ""),
                "electre_use_veto": parameters.get("electre_use_veto", ""),
                "notes": spec.notes,
            }
        )
    history = pd.DataFrame(rows)
    metric_cols = ["cagr", "sharpe", "max_drawdown", "total_turnover"]
    for col in metric_cols:
        history[f"delta_{col}"] = pd.to_numeric(history[col], errors="coerce").diff()
    return history


def _parse_spec(value: str) -> MilestoneSpec:
    parts = value.split("|", 2)
    if len(parts) == 2:
        milestone, result_dir = parts
        notes = ""
    elif len(parts) == 3:
        milestone, result_dir, notes = parts
    else:
        raise argparse.ArgumentTypeError("spec must be milestone|result_dir or milestone|result_dir|notes")
    return MilestoneSpec(milestone=milestone, result_dir=Path(result_dir), notes=notes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile portfolio milestone metrics history.")
    parser.add_argument("--spec", action="append", type=_parse_spec, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    history = collect_milestone_metrics(args.spec)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    history.to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
