from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "compile_milestone_metrics.py"
_SPEC = importlib.util.spec_from_file_location("compile_milestone_metrics", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["compile_milestone_metrics"] = _MODULE
_SPEC.loader.exec_module(_MODULE)
MilestoneSpec = _MODULE.MilestoneSpec
collect_milestone_metrics = _MODULE.collect_milestone_metrics


def _write_result_dir(path: Path, cagr: float, sharpe: float, max_dd: float, event_type: str, turnover: float):
    path.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "strategy": "ELECTRE_MaxSharpe_walk_forward",
                "cagr": cagr,
                "sharpe": sharpe,
                "max_drawdown": max_dd,
                "volatility": 0.1,
                "calmar": 1.0,
            }
        ]
    ).to_csv(path / "strategy_comparison.csv", index=False)
    pd.DataFrame([{"date": "2024-01-31", "event_type": event_type, "turnover": turnover}]).to_csv(
        path / "rebalance_events.csv",
        index=False,
    )
    (path / "run_manifest.json").write_text(
        json.dumps(
            {
                "parameters": {
                    "rebalance": "quarterly",
                    "weight_drift": "buy_and_hold",
                    "rebalance_policy": "threshold",
                    "recategorization_policy": "every_period",
                    "turnover_penalty": 0.5,
                    "category_confirmation_periods": 2,
                    "electre_assignment": "pessimistic",
                    "electre_use_veto": False,
                }
            }
        ),
        encoding="utf-8",
    )


def test_collect_milestone_metrics_records_deltas_and_event_counts(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_result_dir(first, cagr=0.10, sharpe=1.0, max_dd=-0.05, event_type="calendar", turnover=0.5)
    _write_result_dir(second, cagr=0.13, sharpe=1.3, max_dd=-0.04, event_type="category_change", turnover=0.2)

    history = collect_milestone_metrics(
        [
            MilestoneSpec("baseline", first, "first run"),
            MilestoneSpec("penalized", second, "second run"),
        ]
    )

    assert history["milestone"].tolist() == ["baseline", "penalized"]
    assert history.loc[0, "calendar_events"] == 1
    assert history.loc[1, "category_change_events"] == 1
    assert history.loc[1, "delta_cagr"] == 0.03
    assert history.loc[1, "delta_total_turnover"] == -0.3
    assert history.loc[1, "turnover_penalty"] == 0.5
    assert history.loc[1, "category_confirmation_periods"] == 2
