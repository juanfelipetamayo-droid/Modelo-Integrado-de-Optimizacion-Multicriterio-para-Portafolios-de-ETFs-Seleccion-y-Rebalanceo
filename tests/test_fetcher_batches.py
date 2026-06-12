from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.data.fetcher import (
    download_ohlcv_batch,
    compute_price_coverage,
    save_ohlcv,
    DEFAULT_BATCH_SIZE,
    MAX_RETRIES,
)


def test_default_batch_size_defined():
    assert DEFAULT_BATCH_SIZE > 0


def test_max_retries_defined():
    assert MAX_RETRIES >= 1


def test_compute_price_coverage_empty_prices():
    tickers = ["SPY", "QQQ"]
    prices = pd.DataFrame()
    report = compute_price_coverage(tickers, prices, "2021-01-01", "2021-12-31")
    metrics = dict(zip(report["metric"], report["count"]))
    assert metrics["requested_tickers"] == 2
    assert metrics["tickers_with_data"] == 0


def test_compute_price_coverage_with_data():
    tickers = ["SPY", "QQQ"]
    idx = pd.bdate_range("2021-01-01", "2021-12-31")
    prices = pd.DataFrame({"SPY": [100.0] * len(idx), "QQQ": [200.0] * len(idx)}, index=idx)
    report = compute_price_coverage(tickers, prices, "2021-01-01", "2021-12-31")
    metrics = dict(zip(report["metric"], report["count"]))
    assert metrics["tickers_with_data"] == 2


def test_compute_price_coverage_partial():
    tickers = ["MISSING", "SPY"]
    idx = pd.bdate_range("2021-01-01", "2021-12-31")
    prices = pd.DataFrame({"SPY": [100.0] * len(idx)}, index=idx)
    report = compute_price_coverage(tickers, prices, "2021-01-01", "2021-12-31")
    metrics = dict(zip(report["metric"], report["count"]))
    assert metrics["tickers_with_data"] == 1


def test_save_ohlcv(tmp_path: Path):
    idx = pd.bdate_range("2021-01-01", "2021-01-10")
    frames = {"close": pd.DataFrame({"SPY": [100.0] * len(idx)}, index=idx)}
    save_ohlcv(frames, str(tmp_path))
    assert (tmp_path / "close.parquet").exists()


def test_download_ohlcv_batch_empty():
    result = download_ohlcv_batch([], "2021-01-01", "2021-12-31")
    assert isinstance(result, dict)
    assert result.frames == {}
    assert result.failed_tickers == []
    assert result.errors == {}


def test_download_ohlcv_batch_records_missing_ticker_without_dropping_frames(monkeypatch):
    idx = pd.bdate_range("2021-01-01", "2021-01-08")
    close = pd.DataFrame({"SPY": [100.0] * len(idx)}, index=idx)

    def fake_download_ohlcv(tickers, start, end, auto_adjust=True):
        assert tickers == ["SPY", "MISSING"]
        return {"close": close}

    monkeypatch.setattr("etf_optimizer.data.fetcher.download_ohlcv", fake_download_ohlcv)

    result = download_ohlcv_batch(
        ["SPY", "MISSING"],
        "2021-01-01",
        "2021-01-08",
        batch_size=2,
        max_retries=1,
    )

    assert result.frames["close"].columns.tolist() == ["SPY"]
    assert result["close"].equals(close)
    assert result.failed_tickers == ["MISSING"]
    assert result.errors == {"MISSING": "missing_from_download"}


def test_download_ohlcv_batch_records_batch_exception_per_ticker(monkeypatch):
    def fake_download_ohlcv(tickers, start, end, auto_adjust=True):
        if tickers == ["BAD"]:
            raise RuntimeError("yahoo unavailable")
        idx = pd.bdate_range("2021-01-01", "2021-01-08")
        return {"close": pd.DataFrame({tickers[0]: [100.0] * len(idx)}, index=idx)}

    monkeypatch.setattr("etf_optimizer.data.fetcher.download_ohlcv", fake_download_ohlcv)

    result = download_ohlcv_batch(
        ["SPY", "BAD"],
        "2021-01-01",
        "2021-01-08",
        batch_size=1,
        max_retries=1,
    )

    assert result.frames["close"].columns.tolist() == ["SPY"]
    assert result.failed_tickers == ["BAD"]
    assert result.errors == {"BAD": "yahoo unavailable"}
