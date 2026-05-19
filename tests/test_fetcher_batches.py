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
