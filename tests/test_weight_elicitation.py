from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.weight_elicitation import (
    bwm_weights,
    generate_weight_artifacts,
    load_mcdm_criterion_names,
)


def test_bwm_weights_sum_to_one_and_prioritize_best_criterion() -> None:
    criteria = ["momentum_12_1", "rolling_max_drawdown", "fund_age_months"]
    best_to_others = {
        "momentum_12_1": 1,
        "rolling_max_drawdown": 2,
        "fund_age_months": 5,
    }
    others_to_worst = {
        "momentum_12_1": 5,
        "rolling_max_drawdown": 3,
        "fund_age_months": 1,
    }

    result = bwm_weights(
        criteria,
        best_criterion="momentum_12_1",
        worst_criterion="fund_age_months",
        best_to_others=best_to_others,
        others_to_worst=others_to_worst,
    )

    assert abs(sum(result.weights.values()) - 1.0) < 1e-9
    assert result.weights["momentum_12_1"] > result.weights["rolling_max_drawdown"]
    assert result.weights["rolling_max_drawdown"] > result.weights["fund_age_months"]
    assert result.consistency_xi >= 0.0


def test_generate_weight_artifacts_creates_definition_of_done_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "weights"

    manifest = generate_weight_artifacts(
        criteria_config_path=Path("configs/criteria_config.yaml"),
        output_dir=output_dir,
        n_sensitivity_samples=25,
        random_seed=7,
    )

    expected_files = {
        "weights_manual.csv",
        "weights_bwm.csv",
        "weights_equal.csv",
        "weights_sensitivity_samples.csv",
        "weight_consistency_report.md",
        "weight_elicitation.md",
    }
    assert expected_files == {path.name for path in manifest}

    criteria = load_mcdm_criterion_names(Path("configs/criteria_config.yaml"))
    for file_name in ["weights_manual.csv", "weights_bwm.csv", "weights_equal.csv"]:
        weights = pd.read_csv(output_dir / file_name)
        assert set(weights["criterion_name"]) == set(criteria)
        assert abs(weights["weight"].sum() - 1.0) < 1e-9
        assert {"criterion_name", "weight", "method", "elicitation_source", "rationale"} <= set(weights.columns)

    sensitivity = pd.read_csv(output_dir / "weights_sensitivity_samples.csv")
    assert set(sensitivity["criterion_name"]) == set(criteria)
    assert sensitivity["sample_id"].nunique() == 25
    sample_sums = sensitivity.groupby("sample_id")["weight"].sum()
    assert ((sample_sums - 1.0).abs() < 1e-9).all()

    report = (output_dir / "weight_consistency_report.md").read_text(encoding="utf-8")
    assert "BWM" in report
    assert "manual_weights_baseline" in report
    assert "BWM_weights_main" in report
    assert "equal_weights_baseline" in report
    assert "random_weight_sensitivity" in report
    assert "manual_weights_baseline" in report
    assert "director/profesor" in report

    methodology = (output_dir / "weight_elicitation.md").read_text(encoding="utf-8")
    assert "manual_weights_baseline" in methodology
    assert "equal_weights_baseline" in methodology
    assert "BWM_weights_main" in methodology
    assert "random_weight_sensitivity" in methodology
    assert "AHP" in methodology
    assert "manuales" in methodology.lower()
