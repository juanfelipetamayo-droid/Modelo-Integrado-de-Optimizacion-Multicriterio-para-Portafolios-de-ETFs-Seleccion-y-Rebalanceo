from __future__ import annotations

import pandas as pd

from etf_optimizer.selection.electre_tri import Criterion, Profile
from etf_optimizer.reporting.flowsort_comparison import write_flowsort_comparison
from etf_optimizer.selection.flowsort import FlowSort


def test_flowsort_assigns_top_category_and_exports_flow_columns():
    criteria = [
        Criterion("cagr", weight=0.7, preference_direction="max", q=0.0, p=0.02),
        Criterion("volatility", weight=0.3, preference_direction="min", q=0.0, p=0.05),
    ]
    profiles = [Profile("acceptable", {"cagr": 0.05, "volatility": 0.20})]
    alternatives = pd.DataFrame(
        {
            "cagr": [0.12, -0.02],
            "volatility": [0.12, 0.35],
        },
        index=["GOOD", "BAD"],
    )

    assignments = FlowSort(criteria, profiles).assign(alternatives)

    assert assignments.loc["GOOD", "category"] == "above_acceptable"
    assert assignments.loc["BAD", "category"] == "below_acceptable"
    assert "flowsort_net_flow" in assignments.columns
    assert assignments.loc["GOOD", "flowsort_net_flow"] > assignments.loc["BAD", "flowsort_net_flow"]


def test_write_flowsort_comparison_exports_goal_12_artifacts(tmp_path):
    results_dir = tmp_path / "results"
    stage = results_dir / "fold_stage_artifacts"
    fold1 = stage / "fold_1_2020-01-31"
    fold2 = stage / "fold_2_2020-04-30"
    fold1.mkdir(parents=True)
    fold2.mkdir(parents=True)

    pd.DataFrame(
        [
            {"fold": 1, "strategy": "ELECTRE_MaxSharpe_walk_forward", "start_date": "2020-01-31", "end_date": "2020-03-31", "n_observations": 3},
            {"fold": 2, "strategy": "ELECTRE_MaxSharpe_walk_forward", "start_date": "2020-04-30", "end_date": "2020-06-30", "n_observations": 3},
        ]
    ).to_csv(results_dir / "fold_performance.csv", index=False)

    matrix = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB", "CCC"],
            "cagr": [0.14, 0.06, -0.02],
            "volatility": [0.10, 0.20, 0.32],
            "sharpe": [1.2, 0.55, -0.1],
            "sortino": [1.5, 0.7, -0.2],
        }
    )
    matrix.to_csv(fold1 / "criteria_matrix.csv", index=False)
    matrix.assign(cagr=[0.02, 0.12, 0.04], sharpe=[0.2, 1.1, 0.4], sortino=[0.3, 1.3, 0.5]).to_csv(
        fold2 / "criteria_matrix.csv", index=False
    )
    pd.DataFrame(
        {"ticker": ["AAA", "BBB", "CCC"], "category": ["above_preferred", "between_minimum_preferred", "below_minimum"]}
    ).to_csv(fold1 / "electre_assignments.csv", index=False)
    pd.DataFrame(
        {"ticker": ["AAA", "BBB", "CCC"], "category": ["below_minimum", "above_preferred", "between_minimum_preferred"]}
    ).to_csv(fold2 / "electre_assignments.csv", index=False)

    prices = pd.DataFrame(
        {
            "AAA": [100, 102, 104, 103, 102, 101],
            "BBB": [100, 101, 103, 105, 108, 110],
            "CCC": [100, 99, 98, 98, 99, 100],
        },
        index=pd.to_datetime(["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30", "2020-05-31", "2020-06-30"]),
    )
    prices_path = tmp_path / "prices.parquet"
    prices.to_parquet(prices_path)

    output_dir = tmp_path / "flowsort"
    report_path = tmp_path / "docs" / "electre_vs_flowsort.md"
    artifacts = write_flowsort_comparison(results_dir, prices_path, output_dir, report_path)

    expected = {
        "flowsort_assignments.csv",
        "flowsort_flows.csv",
        "electre_vs_flowsort_agreement.csv",
    }
    assert expected == {path.name for path in artifacts}
    assert report_path.exists()

    assignments = pd.read_csv(output_dir / "flowsort_assignments.csv")
    assert set(assignments["variant"]) == {
        "usual_net_flow",
        "v_shape_net_flow",
        "level_net_flow",
        "v_shape_leaving_flow",
    }
    assert {"fold", "rebalance_date", "ticker", "electre_category", "flowsort_category", "variant"} <= set(assignments.columns)

    flows = pd.read_csv(output_dir / "flowsort_flows.csv")
    assert {"flowsort_leaving_flow", "flowsort_entering_flow", "flowsort_net_flow", "ranking_flow"} <= set(flows.columns)

    agreement = pd.read_csv(output_dir / "electre_vs_flowsort_agreement.csv")
    assert {"category_agreement_rate", "selected_jaccard", "cohen_kappa", "mean_equal_weight_forward_cumulative_return"} <= set(
        agreement.columns
    )
    assert agreement["variant"].nunique() == 4
    assert "FlowSort es clasificación multicriterio" in report_path.read_text(encoding="utf-8")
