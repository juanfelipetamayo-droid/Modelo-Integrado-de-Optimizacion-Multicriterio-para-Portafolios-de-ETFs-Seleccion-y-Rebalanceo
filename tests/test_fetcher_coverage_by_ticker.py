from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from etf_optimizer.data.fetcher import OhlcvBatchResult, compute_ticker_coverage


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "download_data.py"
SPEC = importlib.util.spec_from_file_location("download_data", SCRIPT_PATH)
assert SPEC is not None
download_data = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(download_data)


EXPECTED_COLUMNS = [
    "ticker",
    "requested",
    "downloaded",
    "first_valid",
    "last_valid",
    "n_obs",
    "expected_obs",
    "coverage_pct",
    "nan_pct",
    "has_sufficient_history",
    "error",
]


def test_compute_ticker_coverage_reports_per_ticker_schema_and_history_flags():
    idx = pd.bdate_range("2021-01-01", "2021-01-08")
    prices = pd.DataFrame(
        {
            "SPY": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
            "QQQ": [200.0, None, 202.0, None, None, 205.0],
        },
        index=idx,
    )

    report = compute_ticker_coverage(["SPY", "QQQ"], prices, "2021-01-01", "2021-01-08", min_coverage=0.80)

    assert list(report.columns) == EXPECTED_COLUMNS
    rows = report.set_index("ticker").to_dict(orient="index")
    assert rows["SPY"] == {
        "requested": True,
        "downloaded": True,
        "first_valid": "2021-01-01",
        "last_valid": "2021-01-08",
        "n_obs": 6,
        "expected_obs": 6,
        "coverage_pct": 1.0,
        "nan_pct": 0.0,
        "has_sufficient_history": True,
        "error": None,
    }
    assert rows["QQQ"]["downloaded"] is True
    assert rows["QQQ"]["n_obs"] == 3
    assert rows["QQQ"]["coverage_pct"] == 0.5
    assert rows["QQQ"]["nan_pct"] == 0.5
    assert rows["QQQ"]["has_sufficient_history"] is False
    assert rows["QQQ"]["error"] is None


def test_compute_ticker_coverage_ignores_prices_outside_requested_window():
    idx = pd.to_datetime(["2020-12-31", "2021-01-01", "2021-01-04", "2021-01-09"])
    prices = pd.DataFrame({"SPY": [99.0, 100.0, 101.0, 102.0]}, index=idx)

    report = compute_ticker_coverage(["SPY"], prices, "2021-01-01", "2021-01-04")

    row = report.set_index("ticker").loc["SPY"].to_dict()
    assert row["first_valid"] == "2021-01-01"
    assert row["last_valid"] == "2021-01-04"
    assert row["n_obs"] == 2
    assert row["expected_obs"] == 2
    assert row["coverage_pct"] == 1.0
    assert row["nan_pct"] == 0.0


def test_compute_ticker_coverage_reports_missing_and_empty_tickers():
    idx = pd.bdate_range("2021-01-01", "2021-01-08")
    prices = pd.DataFrame({"EMPTY": [None] * len(idx)}, index=idx)

    report = compute_ticker_coverage(["MISSING", "EMPTY"], prices, "2021-01-01", "2021-01-08")

    rows = report.set_index("ticker").to_dict(orient="index")
    assert rows["MISSING"] == {
        "requested": True,
        "downloaded": False,
        "first_valid": None,
        "last_valid": None,
        "n_obs": 0,
        "expected_obs": 6,
        "coverage_pct": 0.0,
        "nan_pct": 1.0,
        "has_sufficient_history": False,
        "error": "missing_column",
    }
    assert rows["EMPTY"]["downloaded"] is False
    assert rows["EMPTY"]["error"] == "no_prices"


def test_download_data_writes_coverage_by_ticker_csv_by_default(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker\nSPY\nQQQ\n", encoding="utf-8")
    out = tmp_path / "yfinance"
    idx = pd.bdate_range("2021-01-01", "2021-01-08")
    close = pd.DataFrame({"SPY": [100.0] * len(idx), "QQQ": [None] * len(idx)}, index=idx)

    def fake_download_ohlcv_batch(tickers, start, end, batch_size, max_retries):
        assert tickers == ["SPY", "QQQ"]
        assert start == "2021-01-01"
        assert end == "2021-01-08"
        return {"close": close}

    monkeypatch.setattr(download_data, "download_ohlcv_batch", fake_download_ohlcv_batch)
    monkeypatch.setattr(download_data, "save_ohlcv", lambda frames, out_dir: Path(out_dir).mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(
        "sys.argv",
        [
            "download_data.py",
            "--universe",
            str(universe),
            "--start",
            "2021-01-01",
            "--end",
            "2021-01-08",
            "--out",
            str(out),
        ],
    )

    download_data.main()

    coverage_path = out / "coverage_by_ticker.csv"
    assert coverage_path.exists()
    coverage = pd.read_csv(coverage_path)
    assert list(coverage.columns) == EXPECTED_COLUMNS
    assert coverage["ticker"].tolist() == ["SPY", "QQQ"]


def test_download_data_limit_applies_after_normalizing_and_deduplicating_tickers(tmp_path, monkeypatch, caplog):
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker\nspy\nQQQ\nSPY\n dia \n\n", encoding="utf-8")
    out = tmp_path / "yfinance"
    idx = pd.bdate_range("2021-01-01", "2021-01-08")
    close = pd.DataFrame({"SPY": [100.0] * len(idx), "QQQ": [200.0] * len(idx)}, index=idx)

    def fake_download_ohlcv_batch(tickers, start, end, batch_size, max_retries):
        assert tickers == ["SPY", "QQQ"]
        return {"close": close}

    monkeypatch.setattr(download_data, "download_ohlcv_batch", fake_download_ohlcv_batch)
    monkeypatch.setattr(download_data, "save_ohlcv", lambda frames, out_dir: Path(out_dir).mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(
        "sys.argv",
        [
            "download_data.py",
            "--universe",
            str(universe),
            "--start",
            "2021-01-01",
            "--end",
            "2021-01-08",
            "--out",
            str(out),
            "--limit",
            "2",
        ],
    )

    with caplog.at_level("INFO", logger=download_data.logger.name):
        download_data.main()

    assert "Ticker universe: requested=4 normalized_unique=3 used=2 limit=2" in caplog.text
    coverage = pd.read_csv(out / "coverage_by_ticker.csv")
    assert coverage["ticker"].tolist() == ["SPY", "QQQ"]


def test_download_data_rejects_negative_limit(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker\nSPY\nQQQ\nDIA\n", encoding="utf-8")

    def fail_download_ohlcv_batch(*args, **kwargs):
        raise AssertionError("download should not run with a negative limit")

    monkeypatch.setattr(download_data, "download_ohlcv_batch", fail_download_ohlcv_batch)
    monkeypatch.setattr(
        "sys.argv",
        [
            "download_data.py",
            "--universe",
            str(universe),
            "--limit",
            "-1",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        download_data.main()

    assert exc_info.value.code == 2


def test_download_data_writes_batch_failures_csv_by_default(tmp_path, monkeypatch):
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker\nSPY\nBAD\n", encoding="utf-8")
    out = tmp_path / "yfinance"
    idx = pd.bdate_range("2021-01-01", "2021-01-08")
    close = pd.DataFrame({"SPY": [100.0] * len(idx)}, index=idx)

    def fake_download_ohlcv_batch(tickers, start, end, batch_size, max_retries):
        assert tickers == ["SPY", "BAD"]
        return OhlcvBatchResult({"close": close}, failed_tickers=["BAD"], errors={"BAD": "yahoo unavailable"})

    monkeypatch.setattr(download_data, "download_ohlcv_batch", fake_download_ohlcv_batch)
    monkeypatch.setattr(download_data, "save_ohlcv", lambda frames, out_dir: Path(out_dir).mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(
        "sys.argv",
        [
            "download_data.py",
            "--universe",
            str(universe),
            "--start",
            "2021-01-01",
            "--end",
            "2021-01-08",
            "--out",
            str(out),
        ],
    )

    download_data.main()

    failures_path = out / "download_failures.csv"
    assert failures_path.exists()
    failures = pd.read_csv(failures_path)
    assert failures.to_dict(orient="records") == [{"ticker": "BAD", "error": "yahoo unavailable"}]
