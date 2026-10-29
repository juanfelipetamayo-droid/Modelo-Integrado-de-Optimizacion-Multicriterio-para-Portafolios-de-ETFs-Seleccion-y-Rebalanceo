from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.reporting.classification_diagnostics import write_classification_diagnostics


def _write_fold(base: Path, fold: int, date: str, rows: list[dict[str, object]]) -> None:
    fold_dir = base / f"fold_{fold:03d}_{date}"
    fold_dir.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(fold_dir / "electre_assignments.csv", index=False)
    pd.DataFrame(
        [
            {"ticker": row["ticker"], "cagr": row["cagr"], "volatility": row["volatility"], "sharpe": row["sharpe"], "sortino": row["sortino"]}
            for row in rows
        ]
    ).to_csv(fold_dir / "criteria_matrix.csv", index=False)


def test_write_classification_diagnostics_exports_required_tables(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    stage_dir = results_dir / "fold_stage_artifacts"
    stage_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "strategy": "ELECTRE_MaxSharpe_walk_forward",
                "fold": 1,
                "start_date": "2020-02-29",
                "end_date": "2020-03-31",
                "n_observations": 2,
            },
            {
                "strategy": "ELECTRE_MaxSharpe_walk_forward",
                "fold": 2,
                "start_date": "2020-04-30",
                "end_date": "2020-05-31",
                "n_observations": 2,
            },
        ]
    ).to_csv(results_dir / "fold_performance.csv", index=False)
    _write_fold(
        stage_dir,
        1,
        "2020_02_29",
        [
            {"ticker": "GOOD", "category": "above_preferred", "cagr": 0.12, "volatility": 0.10, "sharpe": 1.0, "sortino": 1.2},
            {"ticker": "MID", "category": "between_minimum_preferred", "cagr": 0.05, "volatility": 0.15, "sharpe": 0.5, "sortino": 0.6},
            {"ticker": "BAD", "category": "below_minimum", "cagr": 0.00, "volatility": 0.30, "sharpe": 0.0, "sortino": 0.0},
        ],
    )
    _write_fold(
        stage_dir,
        2,
        "2020_04_30",
        [
            {"ticker": "GOOD", "category": "above_preferred", "cagr": 0.11, "volatility": 0.11, "sharpe": 0.9, "sortino": 1.1},
            {"ticker": "MID", "category": "below_minimum", "cagr": 0.01, "volatility": 0.25, "sharpe": 0.1, "sortino": 0.2},
            {"ticker": "BAD", "category": "between_minimum_preferred", "cagr": 0.04, "volatility": 0.16, "sharpe": 0.4, "sortino": 0.5},
        ],
    )
    prices = pd.DataFrame(
        {
            "GOOD": [100.0, 110.0, 121.0, 133.1, 146.41],
            "MID": [100.0, 101.0, 102.0, 101.0, 102.0],
            "BAD": [100.0, 90.0, 81.0, 82.0, 81.0],
        },
        index=pd.to_datetime(["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30", "2020-05-31"]),
    )
    prices_path = tmp_path / "prices.parquet"
    prices.to_parquet(prices_path)

    output_dir = tmp_path / "diagnostics"
    artifacts = write_classification_diagnostics(results_dir, prices_path, output_dir)

    expected = {
        "classification_effectiveness.csv",
        "category_forward_returns.csv",
        "category_forward_sharpe.csv",
        "category_forward_drawdown.csv",
        "pessimistic_optimistic_divergence.csv",
        "category_transition_matrix.csv",
        "selection_jaccard_by_fold.csv",
    }
    assert expected == {path.name for path in output_dir.glob("*.csv")}
    assert set(artifacts.classification_effectiveness["category"]) == {
        "above_preferred",
        "between_minimum_preferred",
        "below_minimum",
    }
    assert not artifacts.pessimistic_optimistic_divergence.empty
    assert artifacts.selection_jaccard_by_fold.loc[0, "selected_jaccard"] == 1.0
    assert {"from_category", "to_category", "transition_count"}.issubset(artifacts.category_transition_matrix.columns)
