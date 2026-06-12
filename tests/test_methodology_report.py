from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.reporting.methodology_report import MethodologyReportConfig, write_methodology_report
from etf_optimizer.selection.electre_tri import Criterion, Profile


def test_write_methodology_report_includes_required_reproducibility_content(tmp_path):
    universe = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "source": ["nasdaq", "nasdaq"],
            "source_url": ["https://api.nasdaq.com/api/screener/etf?download=true"] * 2,
            "active_flag": [True, True],
        }
    )
    funnel = pd.DataFrame(
        [
            {"stage": "requested", "count": 2, "pct_of_requested": 100.0},
            {"stage": "downloaded", "count": 1, "pct_of_requested": 50.0},
            {"stage": "sufficient_history", "count": 1, "pct_of_requested": 50.0},
            {"stage": "liquidity_pass", "count": 1, "pct_of_requested": 50.0},
            {"stage": "final_eligible", "count": 1, "pct_of_requested": 50.0},
        ]
    )
    criteria = [
        Criterion("cagr", weight=0.35, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("volatility", weight=0.25, preference_direction="min", q=0.0, p=0.02, v=0.10),
    ]
    profiles = [Profile("acceptable", {"cagr": 0.03, "volatility": 0.25})]
    report_path = tmp_path / "methodology_report.md"

    write_methodology_report(
        report_path,
        MethodologyReportConfig(
            universe_path=Path("data/universe/etf_universe_clean.csv"),
            prices_path=Path("data/raw/yfinance_pilot/close.parquet"),
            volume_path=Path("data/raw/yfinance_pilot/volume.parquet"),
            start="2020-12-31",
            end="2024-12-31",
            rebalance="annual",
            train_size=36,
            test_size=12,
            step_size=12,
            cost_bps=10.0,
            min_coverage_pct=0.80,
            min_avg_dollar_volume=1_000_000.0,
            price_source="yfinance",
            universe_snapshot_date="current Nasdaq active ETF snapshot",
            fold_diagnostics={
                "walk_forward_folds": 1,
                "oos_periods": 12,
                "sufficiency_label": "pilot_only_oos",
                "thesis_grade_oos": False,
                "warning": "Out-of-sample evidence is pilot-only.",
            },
            data_quality={
                "verdict": "public_data_pilot",
                "survivorship_bias_free": False,
                "allowed_claims": "Preliminary public-data evidence only.",
            },
        ),
        universe=universe,
        filter_funnel=funnel,
        criteria=criteria,
        profiles=profiles,
    )

    text = report_path.read_text(encoding="utf-8")

    assert "# Methodology Report" in text
    assert "Universe source: nasdaq" in text
    assert "Snapshot date: current Nasdaq active ETF snapshot" in text
    assert "Price source: yfinance" in text
    assert "Temporal range: 2020-12-31 to 2024-12-31" in text
    assert "Walk-forward windows: train=36, test=12, step=12, rebalance=annual" in text
    assert "Transaction costs: 10.0 bps" in text
    assert "cagr | 0.35 | max | 0.0 | 0.02 | 0.05" in text
    assert "acceptable | cagr=0.03, volatility=0.25" in text
    assert "Coverage filter: minimum observed price coverage 80.00%" in text
    assert "Liquidity filter: minimum average daily dollar volume 1000000.0" in text
    assert "requested | 2 | 100.0" in text
    assert "final_eligible | 1 | 50.0" in text
    assert "No elimina completamente survivorship bias" in text
    assert "yfinance" in text and "public API" in text
    assert "## Out-of-sample sufficiency" in text
    assert "Walk-forward folds: 1" in text
    assert "OOS periods: 12" in text
    assert "pilot_only_oos" in text
    assert "Out-of-sample evidence is pilot-only." in text
    assert "## Data-quality verdict" in text
    assert "public_data_pilot" in text
    assert "Survivorship-bias-free: False" in text
    assert "Preliminary public-data evidence only." in text
