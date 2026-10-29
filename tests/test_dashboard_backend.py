from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from etf_optimizer.dashboard.backend import (
    build_download_command,
    build_pipeline_command,
    build_sprint_command,
    build_target_portfolio_from_state,
    build_universe_command,
    load_dashboard_state,
)


def _write_csv(path: Path, data: list[dict[str, object]]) -> None:
    pd.DataFrame(data).to_csv(path, index=False)


def test_load_dashboard_state_reads_results_artifacts(tmp_path):
    results = tmp_path / "sprint"
    results.mkdir()
    _write_csv(
        results / "strategy_comparison.csv",
        [
            {"strategy": "ELECTRE_MaxSharpe_walk_forward", "cagr": 0.12, "sharpe": 1.1},
            {"strategy": "EqualWeight_walk_forward", "cagr": 0.08, "sharpe": 0.7},
        ],
    )
    _write_csv(
        results / "electre_weights.csv",
        [
            {"Unnamed: 0": "2024-01-31", "AAA": 0.7, "BBB": 0.3},
        ],
    )
    _write_csv(
        results / "eligible_universe.csv",
        [
            {"ticker": "AAA", "name": "Alpha ETF", "asset_class": "Equity", "category": "Large Cap"},
            {"ticker": "BBB", "name": "Bond ETF", "asset_class": "Fixed Income", "category": "Aggregate Bond"},
        ],
    )
    _write_csv(
        results / "filter_funnel.csv",
        [
            {"stage": "requested", "count": 300, "pct_of_requested": 100.0},
            {"stage": "final_eligible", "count": 75, "pct_of_requested": 25.0},
        ],
    )
    (results / "methodology_report.md").write_text("# Methodology Report\n", encoding="utf-8")
    (results / "run_manifest.json").write_text(
        json.dumps({"git_commit": "abc123", "parameters": {"rebalance": "annual"}}),
        encoding="utf-8",
    )
    (results / "fold_diagnostics.csv").write_text(
        "walk_forward_folds,oos_periods,sufficiency_label,thesis_grade_oos\n1,12,pilot_only_oos,False\n",
        encoding="utf-8",
    )
    (results / "fold_diagnostics.json").write_text(
        json.dumps({"walk_forward_folds": 1, "sufficiency_label": "pilot_only_oos"}),
        encoding="utf-8",
    )
    (results / "data_quality_verdict.json").write_text(
        json.dumps({"verdict": "public_data_pilot", "survivorship_bias_free": False}),
        encoding="utf-8",
    )
    (results / "provenance.json").write_text(
        json.dumps({"schema_version": "1.0", "data_sources": [{"name": "Nasdaq ETF Screener"}]}),
        encoding="utf-8",
    )

    state = load_dashboard_state(results)

    assert state.results_dir == results
    assert state.is_ready is True
    assert state.metrics["strategies"] == 2
    assert state.metrics["final_eligible"] == 75
    assert state.metrics["best_strategy"] == "ELECTRE_MaxSharpe_walk_forward"
    assert state.manifest["git_commit"] == "abc123"
    assert state.provenance["data_sources"][0]["name"] == "Nasdaq ETF Screener"
    assert state.methodology.startswith("# Methodology Report")
    assert state.tables["strategy_comparison"].shape == (2, 3)
    assert state.tables["electre_weights"].shape == (1, 3)
    assert state.artifacts["run_manifest.json"].exists is True
    assert state.artifacts["fold_diagnostics.json"].exists is True
    assert state.artifacts["data_quality_verdict.json"].exists is True
    assert state.tables["fold_diagnostics"].loc[0, "sufficiency_label"] == "pilot_only_oos"
    assert state.data_quality["verdict"] == "public_data_pilot"

    target = build_target_portfolio_from_state(state, capital=10_000, risk_profile="moderado", max_positions=2)

    assert target is not None
    assert target.profile_es == "Moderado"
    assert [line.ticker for line in target.lines] == ["AAA", "BBB"]
    assert round(sum(line.target_value for line in target.lines), 2) == 10_000.0


def test_build_target_portfolio_from_state_requires_weights_and_universe(tmp_path):
    state = load_dashboard_state(tmp_path / "missing")

    assert build_target_portfolio_from_state(state, capital=10_000, risk_profile="moderado") is None

    state = load_dashboard_state(tmp_path / "missing")

    assert state.is_ready is False
    assert state.metrics["strategies"] == 0
    assert state.metrics["final_eligible"] == 0
    assert state.tables == {}
    assert state.manifest == {}
    assert state.provenance == {}
    assert state.data_quality == {}
    assert state.methodology == ""
    assert state.artifacts["strategy_comparison.csv"].exists is False


def test_workflow_command_builders_return_safe_argv_lists(tmp_path):
    universe = tmp_path / "universe.csv"
    prices = tmp_path / "close.parquet"
    volume = tmp_path / "volume.parquet"
    out = tmp_path / "out"

    assert build_universe_command(out).argv == [
        "uv",
        "run",
        "python",
        "scripts/build_universe.py",
        "--out",
        str(out),
    ]
    assert build_download_command(
        universe=universe,
        start="2020-12-31",
        end="2024-12-31",
        out=out,
        batch_size=25,
        max_retries=3,
        limit=300,
    ).argv == [
        "uv",
        "run",
        "python",
        "scripts/download_data.py",
        "--universe",
        str(universe),
        "--start",
        "2020-12-31",
        "--end",
        "2024-12-31",
        "--out",
        str(out),
        "--batch-size",
        "25",
        "--max-retries",
        "3",
        "--limit",
        "300",
    ]
    assert build_pipeline_command(prices=prices, volume=volume, out=out).argv[-6:] == [
        "--prices",
        str(prices),
        "--volume",
        str(volume),
        "--out",
        str(out),
    ]
    assert build_sprint_command(
        universe=universe,
        prices=prices,
        volume=volume,
        start="2020-12-31",
        end="2024-12-31",
        rebalance="annual",
        cost_bps=10.0,
        out=out,
        min_coverage_pct=0.8,
        min_avg_dollar_volume=1_000_000.0,
    ).argv == [
        "uv",
        "run",
        "python",
        "scripts/run_sprint_experiment.py",
        "--universe",
        str(universe),
        "--start",
        "2020-12-31",
        "--end",
        "2024-12-31",
        "--rebalance",
        "annual",
        "--cost-bps",
        "10.0",
        "--out",
        str(out),
        "--min-coverage-pct",
        "0.8",
        "--min-avg-dollar-volume",
        "1000000.0",
        "--prices",
        str(prices),
        "--volume",
        str(volume),
    ]
