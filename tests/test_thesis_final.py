from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from etf_optimizer.thesis_final import run_thesis_final


def test_run_thesis_final_smoke_generates_required_layout_and_final_models(tmp_path: Path) -> None:
    config_path = tmp_path / "thesis_final.yaml"
    output_dir = tmp_path / "thesis_final"
    config = {
        "output_dir": str(output_dir),
        "smoke_test": True,
        "period": {"start": "2015-01-01", "end": "2025-12-31"},
        "rebalance": "quarterly",
        "lookback_months": 36,
        "minimum_oos_months": 60,
        "cost_bps": 10.0,
        "universe_mode": "public_approximate_pit",
        "models_final": [
            "SPY_buy_hold",
            "60/40_SPY_AGG_fixed_weight",
            "Universe_EqualWeight_walk_forward",
            "Universe_MinVariance_walk_forward",
            "ELECTRE_EqualWeight_walk_forward",
            "ELECTRE_MinVariance_walk_forward",
            "ELECTRE_InverseVol_walk_forward",
            "FlowSort_EqualWeight_walk_forward",
            "FlowSort_MinVariance_walk_forward",
            "FlowSort_InverseVol_walk_forward",
        ],
        "experimental_models": ["ELECTRE_MaxSharpe_walk_forward"],
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest_path = run_thesis_final(config_path)

    assert manifest_path == output_dir / "run_manifest.json"
    for subdir in ["tables", "figures", "diagnostics", "configs", "logs", "manuscript_outputs"]:
        assert (output_dir / subdir).is_dir()

    comparison = pd.read_csv(output_dir / "tables" / "final_strategy_comparison.csv")
    expected_models = set(config["models_final"] + config["experimental_models"])
    assert expected_models <= set(comparison["strategy"])
    assert comparison.loc[comparison["strategy"].eq("ELECTRE_MaxSharpe_walk_forward"), "model_role"].item() == "experimental"
    assert {"estimate", "confidence_interval", "benchmark_delta", "statistical_note"}.issubset(comparison.columns)

    intervals = pd.read_csv(output_dir / "tables" / "final_statistical_intervals.csv")
    assert {"estimate", "confidence_interval", "benchmark_delta", "statistical_note"}.issubset(intervals.columns)
    assert {"cagr", "sharpe", "max_drawdown"} <= set(intervals["metric"])
    assert set(intervals["method"]) == {"monthly_moving_block_bootstrap"}
    assert (output_dir / "tables" / "final_return_difference_tests.csv").is_file()
    assert (output_dir / "tables" / "final_drawdown_comparison.csv").is_file()
    for name in ["sensitivity_cap.csv", "sensitivity_rebalance_frequency.csv"]:
        sensitivity = pd.read_csv(output_dir / "tables" / name)
        assert {"estimate", "confidence_interval", "benchmark_delta", "statistical_note"}.issubset(sensitivity.columns)

    diagnostics = json.loads((output_dir / "diagnostics" / "data_flags.json").read_text(encoding="utf-8"))
    assert diagnostics["universe_mode"] == "public_approximate_pit"
    assert diagnostics["costs_included"] is True
    assert diagnostics["turnover_included"] is True
    assert diagnostics["minimum_oos_months"] == 60

    report = (output_dir / "manuscript_outputs" / "thesis_final_summary.md").read_text(encoding="utf-8")
    assert "MaxSharpe solo como experimental" in report
    assert "public_approximate_pit" in report
