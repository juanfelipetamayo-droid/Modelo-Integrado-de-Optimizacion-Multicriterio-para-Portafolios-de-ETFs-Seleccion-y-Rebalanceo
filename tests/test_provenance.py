from __future__ import annotations

import json
from pathlib import Path

from etf_optimizer.reporting.provenance import MethodologySource, write_provenance_record


def test_write_provenance_record_tracks_code_data_methodology_sources(tmp_path):
    path = tmp_path / "provenance.json"

    write_provenance_record(
        path,
        code_paths=[Path("scripts/run_sprint_experiment.py"), Path("src/etf_optimizer/pipeline.py")],
        data_sources=[
            {
                "name": "Nasdaq ETF Screener",
                "type": "universe_snapshot",
                "url": "https://api.nasdaq.com/api/screener/etf?download=true",
                "license_or_access": "public endpoint; verify terms before redistribution",
                "survivorship_bias_free": False,
                "role": "active ETF candidate universe",
            }
        ],
        methodology_sources=[
            MethodologySource(
                name="ELECTRE Tri",
                citation="Roy-style outranking multicriteria sorting model",
                role="ETF acceptability sorting",
            )
        ],
        generated_artifacts=[Path("results/sprint/strategy_comparison.csv")],
        limitations=["Public active-current universe is not survivorship-bias-free."],
        run_metadata={"command": "run_sprint_experiment.py --example", "git_dirty": True},
        data_quality={"verdict": "public_data_pilot", "survivorship_bias_free": False},
    )

    record = json.loads(path.read_text(encoding="utf-8"))

    assert record["schema_version"] == "1.0"
    assert record["code_sources"][0]["path"] == "scripts/run_sprint_experiment.py"
    assert record["data_sources"][0]["survivorship_bias_free"] is False
    assert record["methodology_sources"][0]["name"] == "ELECTRE Tri"
    assert record["limitations"] == ["Public active-current universe is not survivorship-bias-free."]
    assert record["run_metadata"] == {"command": "run_sprint_experiment.py --example", "git_dirty": True}
    assert record["data_quality"]["verdict"] == "public_data_pilot"
    assert record["data_quality"]["survivorship_bias_free"] is False
