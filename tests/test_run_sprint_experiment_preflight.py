from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_sprint_experiment.py"
SPEC = importlib.util.spec_from_file_location("run_sprint_experiment", SCRIPT_PATH)
assert SPEC is not None
run_sprint_experiment = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_sprint_experiment)
main = run_sprint_experiment.main
build_eligible_universe_outputs = run_sprint_experiment.build_eligible_universe_outputs
validate_input_paths = run_sprint_experiment.validate_input_paths
validate_cli_args = run_sprint_experiment.validate_cli_args
calculate_fold_diagnostics = run_sprint_experiment.calculate_fold_diagnostics
classify_data_quality = run_sprint_experiment.classify_data_quality


def test_calculate_fold_diagnostics_accounts_for_pct_change_and_flags_pilot_only():
    monthly_prices = pd.DataFrame(
        {"AAA": range(48), "BBB": range(100, 148)},
        index=pd.date_range("2021-01-31", periods=48, freq="ME"),
    )

    diagnostics = calculate_fold_diagnostics(
        monthly_prices,
        train_size=36,
        test_size=12,
        step_size=12,
        min_thesis_folds=5,
        min_thesis_oos_periods=60,
    )

    assert diagnostics["price_observations"] == 48
    assert diagnostics["return_observations"] == 47
    assert diagnostics["walk_forward_folds"] == 0
    assert diagnostics["oos_periods"] == 0
    assert diagnostics["sufficiency_label"] == "insufficient_oos"
    assert diagnostics["thesis_grade_oos"] is False
    assert "No complete walk-forward fold" in diagnostics["warning"]


def test_calculate_fold_diagnostics_marks_multiple_folds_as_thesis_grade():
    monthly_prices = pd.DataFrame(
        {"AAA": range(132), "BBB": range(100, 232)},
        index=pd.date_range("2015-01-31", periods=132, freq="ME"),
    )

    diagnostics = calculate_fold_diagnostics(
        monthly_prices,
        train_size=36,
        test_size=12,
        step_size=12,
        min_thesis_folds=5,
        min_thesis_oos_periods=60,
    )

    assert diagnostics["return_observations"] == 131
    assert diagnostics["walk_forward_folds"] == 7
    assert diagnostics["oos_periods"] == 84
    assert diagnostics["sufficiency_label"] == "thesis_grade_oos"
    assert diagnostics["thesis_grade_oos"] is True
    assert diagnostics["warning"] == ""


def test_classify_data_quality_separates_synthetic_public_and_institutional_runs():
    assert classify_data_quality(price_source="synthetic structural test data", universe_type="active_current_public_snapshot") == {
        "verdict": "structural_test_only",
        "survivorship_bias_free": False,
        "allowed_claims": "Software smoke test only; do not interpret as market performance evidence.",
    }
    assert classify_data_quality(price_source="yfinance", universe_type="active_current_public_snapshot")["verdict"] == "public_data_pilot"
    institutional = classify_data_quality(
        price_source="crsp",
        universe_type="institutional_survivorship_bias_free",
    )
    assert institutional["verdict"] == "institutional_thesis_grade"
    assert institutional["survivorship_bias_free"] is True
    regulatory = classify_data_quality(price_source="regulatory_enriched_public", universe_type="regulatory_enriched_pit")
    assert regulatory["verdict"] == "thesis_aligned_public_regulatory_pit"
    assert regulatory["survivorship_bias_free"] is False
    assert "guaranteed benchmark outperformance" in regulatory["prohibited_claims"]


def test_validate_input_paths_accepts_synthetic_mode_without_prices():
    assert validate_input_paths(None, None) == []


def test_validate_cli_args_rejects_invalid_quant_parameters(tmp_path):
    class Args:
        universe = tmp_path / "universe.csv"
        prices = None
        volume = None
        start = "2024-12-31"
        end = "2020-12-31"
        cost_bps = -1.0
        min_coverage_pct = 1.5
        min_avg_dollar_volume = -10.0

    errors = validate_cli_args(Args())

    assert "missing universe file" in errors[0]
    assert "start must be on or before end" in errors
    assert "cost_bps must be finite and nonnegative" in errors
    assert "min_coverage_pct must be finite and between 0 and 1" in errors
    assert "min_avg_dollar_volume must be finite and nonnegative" in errors


def test_validate_cli_args_rejects_nat_and_nonfinite_numbers(tmp_path):
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker\nSPY\n", encoding="utf-8")

    args = SimpleNamespace(
        universe=universe,
        prices=None,
        volume=None,
        start="NaT",
        end="2024-12-31",
        cost_bps=float("inf"),
        min_coverage_pct=float("nan"),
        min_avg_dollar_volume=float("nan"),
    )
    errors = validate_cli_args(args)

    assert "start and end must be valid finite dates" in errors
    assert "cost_bps must be finite and nonnegative" in errors
    assert "min_coverage_pct must be finite and between 0 and 1" in errors
    assert "min_avg_dollar_volume must be finite and nonnegative" in errors


def test_validate_cli_args_rejects_invalid_exposure_cap(tmp_path):
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker\nSPY\n", encoding="utf-8")
    args = SimpleNamespace(
        universe=universe,
        prices=None,
        volume=None,
        start="2020-12-31",
        end="2024-12-31",
        cost_bps=10.0,
        min_coverage_pct=0.8,
        min_avg_dollar_volume=0.0,
        category_exposure_cap=1.5,
    )

    errors = validate_cli_args(args)

    assert "category_exposure_cap must be finite and between 0 and 1" in errors



def test_validate_input_paths_reports_missing_prices_file(tmp_path):
    missing_prices = tmp_path / "missing_prices.parquet"

    errors = validate_input_paths(missing_prices, None)

    assert errors == [f"missing prices file: {missing_prices}"]


def test_validate_input_paths_reports_missing_volume_file(tmp_path):
    prices = tmp_path / "prices.parquet"
    prices.write_bytes(b"not used by preflight")
    missing_volume = tmp_path / "missing_volume.parquet"

    errors = validate_input_paths(prices, missing_volume)

    assert errors == [f"missing volume file: {missing_volume}"]


def test_build_eligible_universe_outputs_writes_final_universe_and_funnel_counts():
    universe = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB", "CCC", "DDD"],
            "name": ["A Fund", "B Fund", "C Fund", "D Fund"],
        }
    )
    coverage = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB", "CCC", "DDD"],
            "downloaded": [True, True, True, False],
            "first_valid": ["2020-01-01", "2020-01-01", "2021-01-01", None],
            "coverage_pct": [1.0, 0.9, 0.4, 0.0],
        }
    )
    prices = pd.DataFrame(
        {
            "AAA": [10.0, 11.0],
            "BBB": [20.0, 21.0],
            "CCC": [30.0, 31.0],
        }
    )
    volume = pd.DataFrame(
        {
            "AAA": [1_000_000, 1_000_000],
            "BBB": [1_000, 1_000],
            "CCC": [1_000_000, 1_000_000],
        }
    )

    eligible_universe, funnel, counts = build_eligible_universe_outputs(
        universe=universe,
        coverage=coverage,
        prices=prices,
        volume=volume,
        min_coverage_pct=0.8,
        min_avg_dollar_volume=1_000_000.0,
    )

    assert eligible_universe["ticker"].tolist() == ["AAA"]
    assert "avg_dollar_volume" in eligible_universe.columns
    assert funnel.to_dict("records") == [
        {"stage": "requested", "count": 4, "pct_of_requested": 100.0},
        {"stage": "downloaded", "count": 3, "pct_of_requested": 75.0},
        {"stage": "sufficient_history", "count": 2, "pct_of_requested": 50.0},
        {"stage": "liquidity_pass", "count": 1, "pct_of_requested": 25.0},
        {"stage": "final_eligible", "count": 1, "pct_of_requested": 25.0},
    ]
    assert counts == {
        "requested": 4,
        "downloaded": 3,
        "failed": 1,
        "sufficient_history": 2,
        "liquidity_pass": 1,
        "final_eligible": 1,
    }


def test_build_eligible_universe_outputs_excludes_late_first_valid_dates():
    universe = pd.DataFrame({"ticker": ["FULL", "LATE"], "name": ["Full Fund", "Late Fund"]})
    coverage = pd.DataFrame(
        {
            "ticker": ["FULL", "LATE"],
            "downloaded": [True, True],
            "first_valid": ["2020-12-31", "2021-02-01"],
            "coverage_pct": [1.0, 0.95],
        }
    )
    prices = pd.DataFrame({"FULL": [10.0, 11.0], "LATE": [20.0, 21.0]})
    volume = pd.DataFrame({"FULL": [1_000_000, 1_000_000], "LATE": [1_000_000, 1_000_000]})

    eligible_universe, funnel, counts = build_eligible_universe_outputs(
        universe=universe,
        coverage=coverage,
        prices=prices,
        volume=volume,
        min_coverage_pct=0.8,
        min_avg_dollar_volume=1_000_000.0,
        min_first_valid="2020-12-31",
    )

    assert eligible_universe["ticker"].tolist() == ["FULL"]
    assert counts["sufficient_history"] == 1
    assert funnel.loc[funnel["stage"] == "sufficient_history", "count"].item() == 1


def test_main_writes_fold_diagnostics_and_data_quality_verdict(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    pd.DataFrame({"ticker": ["SPY", "BND", "QQQ", "IWM", "TLT"]}).to_csv(universe, index=False)
    output_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_sprint_experiment.py",
            "--universe",
            str(universe),
            "--start",
            "2020-01-01",
            "--end",
            "2024-12-31",
            "--out",
            str(output_dir),
        ],
    )

    main()

    fold_diagnostics = json.loads((output_dir / "fold_diagnostics.json").read_text(encoding="utf-8"))
    assert fold_diagnostics["sufficiency_label"] == "pilot_only_oos"
    assert fold_diagnostics["walk_forward_folds"] == 1
    assert fold_diagnostics["thesis_grade_oos"] is False
    assert (output_dir / "fold_diagnostics.csv").exists()
    data_quality = json.loads((output_dir / "data_quality_verdict.json").read_text(encoding="utf-8"))
    assert data_quality["verdict"] == "structural_test_only"
    assert data_quality["survivorship_bias_free"] is False


def test_main_writes_electre_selection_by_rebalance_file(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    pd.DataFrame({"ticker": ["SPY", "BND", "QQQ", "IWM", "TLT"]}).to_csv(universe, index=False)
    output_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_sprint_experiment.py",
            "--universe",
            str(universe),
            "--start",
            "2020-01-01",
            "--end",
            "2024-12-31",
            "--out",
            str(output_dir),
        ],
    )

    main()

    selection_path = output_dir / "electre_selection_by_rebalance.csv"
    assert selection_path.exists()
    selection = pd.read_csv(selection_path)
    assert selection.columns.tolist() == [
        "rebalance_date",
        "ticker",
        "selected",
        "category",
        "thesis_category",
        "cagr",
        "volatility",
        "sharpe",
        "sortino",
        "peer_group",
        "profile_scope",
        "liquidity",
        "avg_dollar_volume",
    ]
    assert not selection.empty


def test_main_writes_methodology_report_with_core_content(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    pd.DataFrame(
        {
            "ticker": ["SPY", "BND", "QQQ", "IWM", "TLT"],
            "source": ["nasdaq"] * 5,
            "source_url": ["https://api.nasdaq.com/api/screener/etf?download=true"] * 5,
        }
    ).to_csv(universe, index=False)
    output_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_sprint_experiment.py",
            "--universe",
            str(universe),
            "--start",
            "2020-01-01",
            "--end",
            "2024-12-31",
            "--out",
            str(output_dir),
        ],
    )

    main()

    report = (output_dir / "methodology_report.md").read_text(encoding="utf-8")
    assert "Universe source: nasdaq" in report
    assert "Snapshot date: current Nasdaq active ETF snapshot" in report
    assert "Price source: synthetic structural test data" in report
    assert "Temporal range: 2020-01-01 to 2024-12-31" in report
    assert "Walk-forward windows: train=36, test=12, step=12, rebalance=annual" in report
    assert "Transaction costs: 10.0 bps" in report
    assert "cagr | 0.35 | max" in report
    assert "Coverage filter: minimum observed price coverage 80.00%" in report
    assert "Liquidity filter: minimum average daily dollar volume 0.0" in report
    assert "final_eligible" in report
    assert "No elimina completamente survivorship bias" in report
    assert "Synthetic data limitation: this no-price run uses deterministic structural test data" in report
    assert "precios públicos vía yfinance" not in report
    assert "yfinance is a public API" not in report


def test_main_writes_run_manifest_with_reproducibility_schema(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    pd.DataFrame({"ticker": ["SPY", "BND", "QQQ", "IWM", "TLT"]}).to_csv(universe, index=False)
    output_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_sprint_experiment.py",
            "--universe",
            str(universe),
            "--start",
            "2020-01-01",
            "--end",
            "2024-12-31",
            "--rebalance",
            "annual",
            "--cost-bps",
            "12.5",
            "--out",
            str(output_dir),
        ],
    )

    main()

    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert set(manifest) == {
        "git_commit",
        "timestamp_utc",
        "python_version",
        "package_versions",
        "paths",
        "parameters",
    }
    assert isinstance(manifest["git_commit"], str)
    assert isinstance(manifest["timestamp_utc"], str)
    assert isinstance(manifest["python_version"], str)
    assert {"numpy", "pandas", "scipy", "sklearn", "yfinance", "pyarrow"}.issubset(
        manifest["package_versions"]
    )
    assert manifest["paths"] == {
        "universe": str(universe),
        "prices": None,
        "volume": None,
        "out": str(output_dir),
    }
    assert manifest["parameters"] == {
        "start": "2020-01-01",
        "end": "2024-12-31",
        "rebalance": "annual",
        "cost_bps": 12.5,
        "min_coverage_pct": 0.80,
        "min_avg_dollar_volume": 0.0,
        "train_size": 36,
        "test_size": 12,
        "step_size": 12,
        "weight_drift": "buy_and_hold",
        "electre_assignment": "pessimistic",
        "electre_use_veto": True,
        "electre_backend": "internal",
        "rebalance_policy": "calendar",
        "drift_tolerance": 0.05,
        "optimizer_fallback": True,
        "recategorization_policy": "rebalance_only",
        "turnover_penalty": 0.0,
        "category_confirmation_periods": 1,
        "category_change_min_score_improvement": 0.0,
        "category_exposure_cap": None,
    }


def test_main_report_labels_keep_optimized_benchmarks_walk_forward(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    pd.DataFrame({"ticker": ["SPY", "BND", "QQQ", "IWM", "TLT"]}).to_csv(universe, index=False)
    output_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_sprint_experiment.py",
            "--universe",
            str(universe),
            "--start",
            "2020-01-01",
            "--end",
            "2024-12-31",
            "--out",
            str(output_dir),
        ],
    )

    main()

    comparison = pd.read_csv(output_dir / "strategy_comparison.csv", index_col=0)
    labels = set(comparison.index)
    assert {
        "ELECTRE_EqualWeight_walk_forward",
        "ELECTRE_MinVariance_walk_forward",
        "ELECTRE_MaxSharpe_walk_forward",
        "Universe_EqualWeight_walk_forward",
        "MinVariance_walk_forward",
        "MaxSharpe_walk_forward",
    }.issubset(labels)
    assert labels.isdisjoint({"ELECTRE_MaxSharpe", "Universe_EqualWeight", "MinVariance", "MaxSharpe"})
    assert not any("in_sample" in label for label in labels)


def test_main_aborts_before_loading_universe_when_prices_file_is_missing(tmp_path, monkeypatch, capsys):
    universe = tmp_path / "universe.csv"
    missing_prices = tmp_path / "missing_prices.parquet"
    output_dir = tmp_path / "out"
    read_csv_calls: list[Path] = []

    def fake_read_csv(path: Path):
        read_csv_calls.append(path)
        raise AssertionError("universe should not be loaded after preflight failure")

    monkeypatch.setattr("pandas.read_csv", fake_read_csv)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_sprint_experiment.py",
            "--universe",
            str(universe),
            "--prices",
            str(missing_prices),
            "--out",
            str(output_dir),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    assert "missing prices file" in capsys.readouterr().err
    assert read_csv_calls == []
