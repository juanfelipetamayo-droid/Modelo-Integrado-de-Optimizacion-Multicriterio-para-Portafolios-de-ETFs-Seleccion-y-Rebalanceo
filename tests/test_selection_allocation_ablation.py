from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.reporting.selection_allocation_ablation import run_selection_allocation_ablation, write_selection_allocation_ablation


def _write_fold(base: Path, fold: int, date: str) -> None:
    fold_dir = base / f"fold_{fold:03d}_{date.replace('-', '_')}"
    fold_dir.mkdir(parents=True)
    pd.DataFrame({"rebalance_date": [date], "n_candidates": [3], "n_selected": [1]}).to_csv(
        fold_dir / "classification_diagnostics.csv", index=False
    )
    pd.DataFrame({"ticker": ["A", "B", "C"]}).to_csv(fold_dir / "universe_snapshot.csv", index=False)
    pd.DataFrame(
        [
            {"ticker": "A", "cagr": 0.12, "volatility": 0.10, "sharpe": 1.1, "sortino": 1.2},
            {"ticker": "B", "cagr": 0.05, "volatility": 0.16, "sharpe": 0.5, "sortino": 0.6},
            {"ticker": "C", "cagr": 0.01, "volatility": 0.28, "sharpe": 0.1, "sortino": 0.2},
        ]
    ).to_csv(fold_dir / "criteria_matrix.csv", index=False)
    pd.DataFrame(
        [
            {"ticker": "A", "category": "above_preferred"},
            {"ticker": "B", "category": "between_minimum_preferred"},
            {"ticker": "C", "category": "below_minimum"},
        ]
    ).to_csv(fold_dir / "electre_assignments.csv", index=False)


def test_selection_allocation_ablation_writes_full_grid(tmp_path: Path) -> None:
    dates = pd.date_range("2020-01-31", periods=8, freq="ME")
    prices = pd.DataFrame(
        {
            "A": [100, 102, 104, 106, 108, 110, 112, 114],
            "B": [100, 101, 100, 102, 101, 103, 102, 104],
            "C": [100, 99, 98, 99, 97, 98, 96, 97],
        },
        index=dates,
    )
    prices_path = tmp_path / "prices.parquet"
    prices.to_parquet(prices_path)

    results_dir = tmp_path / "baseline"
    stage_dir = results_dir / "fold_stage_artifacts"
    for fold, date in enumerate(["2020-05-31", "2020-06-30", "2020-07-31", "2020-08-31"], start=1):
        _write_fold(stage_dir, fold, date)

    result = run_selection_allocation_ablation(
        prices_path,
        results_dir,
        train_size=3,
        test_size=1,
        step_size=1,
        cost_bps=0.0,
        max_weight=None,
    )
    assert result.ablation_grid.shape[0] == 19
    assert "Universe_EqualWeight_walk_forward" in set(result.ablation_grid["strategy"])
    assert "ELECTRE_pessimistic_no_veto_InverseVol_walk_forward" in set(result.ablation_grid["strategy"])

    out = tmp_path / "out"
    write_selection_allocation_ablation(result, out)
    assert (out / "ablation_grid.csv").exists()
    assert (out / "turnover_summary.csv").exists()
