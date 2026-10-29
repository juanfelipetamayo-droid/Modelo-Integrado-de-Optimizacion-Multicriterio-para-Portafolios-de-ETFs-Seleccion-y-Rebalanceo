from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_sprint_experiment.py"
SPEC = importlib.util.spec_from_file_location("run_sprint_experiment", SCRIPT_PATH)
assert SPEC is not None
run_sprint_experiment = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_sprint_experiment)
build_fixed_reference_benchmarks = run_sprint_experiment.build_fixed_reference_benchmarks


def test_build_fixed_reference_benchmarks_uses_raw_returns_not_eligible_subset():
    idx = pd.date_range("2021-01-31", periods=6, freq="ME")
    all_returns = pd.DataFrame(
        {
            "SPY": [0.01, 0.02, -0.01, 0.005, 0.008, 0.004],
            "BND": [0.002, 0.001, 0.003, -0.001, 0.002, 0.001],
            "AAA": [0.03, -0.02, 0.01, 0.0, 0.02, -0.01],
        },
        index=idx,
    )
    eligible_returns = all_returns[["AAA"]]
    report_index = idx[2:]

    references = build_fixed_reference_benchmarks(
        all_returns=all_returns,
        eligible_returns=eligible_returns,
        reference_returns=pd.DataFrame(index=idx),
        report_index=report_index,
        rebalance_periods=12,
    )

    assert set(references) == {"SPY_buy_hold", "60/40_SPY_BND_fixed_weight"}
    assert references["SPY_buy_hold"].index.equals(report_index)
    assert references["SPY_buy_hold"].equals(all_returns["SPY"].reindex(report_index))


def test_build_fixed_reference_benchmarks_can_use_external_reference_returns():
    idx = pd.date_range("2021-01-31", periods=6, freq="ME")
    all_returns = pd.DataFrame({"AAA": [0.03, -0.02, 0.01, 0.0, 0.02, -0.01]}, index=idx)
    eligible_returns = all_returns.copy()
    reference_returns = pd.DataFrame(
        {
            "SPY": [0.011, 0.021, -0.011, 0.006, 0.009, 0.005],
            "BND": [0.003, 0.002, 0.004, 0.0, 0.003, 0.002],
        },
        index=idx,
    )
    report_index = idx[2:]

    references = build_fixed_reference_benchmarks(
        all_returns=all_returns,
        eligible_returns=eligible_returns,
        reference_returns=reference_returns,
        report_index=report_index,
        rebalance_periods=12,
    )

    assert set(references) == {"SPY_buy_hold", "60/40_SPY_BND_fixed_weight"}
    assert references["SPY_buy_hold"].equals(reference_returns["SPY"].reindex(report_index))
