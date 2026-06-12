from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_presentation_deliverables.py"
SPEC = importlib.util.spec_from_file_location("build_presentation_deliverables", SCRIPT_PATH)
assert SPEC is not None
build_presentation_deliverables = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_presentation_deliverables)

bibliography_entries = build_presentation_deliverables.bibliography_entries
format_percent = build_presentation_deliverables.format_percent
build_front_chart_data = build_presentation_deliverables.build_front_chart_data
load_metric_bundle = build_presentation_deliverables.load_metric_bundle


def test_format_percent_handles_signed_metrics():
    assert format_percent(0.0246775) == "2.47%"
    assert format_percent(-0.240142) == "-24.01%"


def test_bibliography_entries_include_libraries_and_data_sources():
    entries = bibliography_entries()
    joined = "\n".join(entries).lower()

    assert "electre" in joined
    assert "yahoo finance" in joined
    assert "nasdaq" in joined
    assert "pandas" in joined
    assert "scikit-learn" in joined
    assert "pydecision" in joined


def test_front_chart_data_serializes_equity_curves_and_rebalance_events(tmp_path):
    result_dir = tmp_path / "result"
    result_dir.mkdir()
    pd.DataFrame(
        {
            "date": ["2020-01-31", "2020-02-29"],
            "Strategy_A": [1.0, 1.1],
            "SPY_buy_hold": [1.0, 1.05],
        }
    ).to_csv(result_dir / "equity_curves.csv", index=False)
    pd.DataFrame(
        {"date": ["2020-02-29"], "event_type": ["calendar"], "turnover": [0.25], "max_abs_drift": [0.08]}
    ).to_csv(result_dir / "rebalance_events.csv", index=False)

    data = build_front_chart_data(result_dir)

    assert [series["name"] for series in data["series"]] == ["Strategy_A", "SPY_buy_hold"]
    assert data["series"][0]["kind"] == "strategy"
    assert data["series"][1]["kind"] == "benchmark"
    assert data["series"][0]["values"][1] == {"date": "2020-02-29", "value": 1.1}
    assert data["events"] == [{"date": "2020-02-29", "type": "calendar", "turnover": 0.25, "max_abs_drift": 0.08}]


def test_front_html_explains_diagnosis_planning_execution(tmp_path):
    bundle = {
        "baseline": {"cagr": -0.01, "sharpe": 0.01, "max_drawdown": -0.40, "volatility": 0.15, "calmar": -0.02},
        "candidate": {"cagr": 0.02, "sharpe": 0.25, "max_drawdown": -0.24, "volatility": 0.13, "calmar": 0.10},
        "deltas": {"cagr": 0.03, "sharpe": 0.24, "max_drawdown": 0.16, "volatility": -0.02, "calmar": 0.12},
        "candidate_turnover": 1.5,
    }

    path = build_presentation_deliverables.build_front_html(tmp_path / "front", bundle)
    html = path.read_text(encoding="utf-8")

    assert "Diagnóstico, planeación y ejecución" in html
    assert "Proceder correcto" in html
    assert "Integridad de datos" in html
    assert "Diseño de corrida" in html
    assert "Comando visible" in html
    assert "Strategy timeline with rebalance points" in html
    assert "front-chart-data" in html
    assert "strategy-chart" in html
    assert "strategy-toggles" in html
    assert "Toggle lines" in html
    assert "Próximo paso de datos point-in-time" in html
    assert "CRSP, Morningstar Direct, Lipper, Bloomberg o Refinitiv/LSEG" in html
    assert "oklch" in html
    assert "border-left" not in html


def test_load_metric_bundle_reads_candidate_and_baseline(tmp_path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    baseline.mkdir()
    candidate.mkdir()
    pd.DataFrame(
        [{"strategy": "ELECTRE_MaxSharpe_walk_forward", "cagr": -0.01, "sharpe": 0.01, "max_drawdown": -0.40, "volatility": 0.15, "calmar": -0.02}]
    ).to_csv(baseline / "strategy_comparison.csv", index=False)
    pd.DataFrame(
        [{"strategy": "ELECTRE_MaxSharpe_walk_forward", "cagr": 0.02, "sharpe": 0.25, "max_drawdown": -0.24, "volatility": 0.13, "calmar": 0.10}]
    ).to_csv(candidate / "strategy_comparison.csv", index=False)
    pd.DataFrame({"event_type": ["calendar", "category_change"], "turnover": [1.0, 0.5]}).to_csv(
        candidate / "rebalance_events.csv", index=False
    )

    bundle = load_metric_bundle(baseline, candidate)

    assert bundle["candidate"]["cagr"] == 0.02
    assert bundle["baseline"]["cagr"] == -0.01
    assert bundle["deltas"]["cagr"] == 0.03
    assert bundle["candidate_events"] == {"calendar": 1, "category_change": 1}
    assert bundle["candidate_turnover"] == 1.5
