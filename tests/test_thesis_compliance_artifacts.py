from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_thesis_compliance_artifacts.py"
SPEC = importlib.util.spec_from_file_location("build_thesis_compliance_artifacts", SCRIPT_PATH)
assert SPEC is not None
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)
build_run_compliance_artifacts = module.build_run_compliance_artifacts


def test_build_run_compliance_artifacts_preserves_negative_objective3(tmp_path):
    result_dir = tmp_path / "run"
    diagnostics_dir = result_dir / "electre_classification_diagnostics"
    diagnostics_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "cagr": [0.1, 0.2],
            "volatility": [0.2, 0.3],
            "sharpe": [0.5, 0.6],
            "liquidity": [1_000_000, 2_000_000],
            "tracking_error": [0.03, 0.04],
            "expense_ratio": [0.001, 0.002],
        }
    ).to_csv(result_dir / "features_table.csv", index=False)
    pd.DataFrame(
        {
            "rebalance_date": ["2025-01-31"] * 10,
            "ticker": [f"ETF{i}" for i in range(10)],
            "selected": [True] * 10,
        }
    ).to_csv(result_dir / "electre_selection_by_rebalance.csv", index=False)
    pd.DataFrame(
        {
            "strategy": ["ELECTRE_EqualWeight_walk_forward", "SPY_buy_hold", "60/40_SPY_BND_fixed_weight", "Universe_EqualWeight_walk_forward"],
            "cagr": [0.05, 0.12, 0.08, 0.07],
            "volatility": [0.18, 0.15, 0.10, 0.12],
            "sharpe": [0.5, 1.0, 0.9, 0.8],
            "sortino": [0.7, 1.2, 1.0, 0.9],
            "max_drawdown": [-0.20, -0.10, -0.08, -0.12],
        }
    ).to_csv(result_dir / "strategy_comparison.csv", index=False)
    pd.DataFrame(
        {
            "category": ["above_preferred", "between_minimum_preferred", "below_minimum"],
            "mean_forward_sharpe": [0.5, 0.3, 0.1],
        }
    ).to_csv(diagnostics_dir / "classification_effectiveness.csv", index=False)

    paths = build_run_compliance_artifacts(
        result_dir,
        start="2021-01-01",
        end="2025-12-31",
        universe_mode="regulatory_enriched_pit",
    )

    assert all(path.exists() for path in paths.values())
    payload = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    objective3 = [row for row in payload["objective_statuses"] if row["objective"] == "specific_3"][0]
    assert objective3["status"] == "not empirically validated"
    summary = pd.read_csv(paths["compliance_summary"])
    assert "specific_3" in set(summary["objective"])
