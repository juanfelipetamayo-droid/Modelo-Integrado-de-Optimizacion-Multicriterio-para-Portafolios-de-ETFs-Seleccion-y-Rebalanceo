from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class OhlcvBatchResult(dict[str, pd.DataFrame]):
    """Backward-compatible batch result with explicit per-ticker failures.

    The object behaves like the historical ``dict[str, DataFrame]`` return value
    while exposing ``frames``, ``failed_tickers`` and ``errors`` for callers that
    need to audit failed or missing tickers.
    """

    def __init__(
        self,
        frames: dict[str, pd.DataFrame] | None = None,
        failed_tickers: list[str] | None = None,
        errors: dict[str, str] | None = None,
    ) -> None:
        super().__init__(frames or {})
        self.failed_tickers = failed_tickers or []
        self.errors = errors or {}

    @property
    def frames(self) -> dict[str, pd.DataFrame]:
        return self


def download_ohlcv(tickers: list[str], start: str, end: str, auto_adjust: bool = True) -> dict[str, pd.DataFrame]:
    """Download public historical ETF data from Yahoo Finance via yfinance."""
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=auto_adjust,
        group_by="column",
        progress=False,
        threads=True,
    )
    if isinstance(data.columns, pd.MultiIndex):
        return {field.lower().replace(" ", "_"): data[field].dropna(how="all") for field in data.columns.levels[0] if field in data}
    return {field.lower().replace(" ", "_"): data[[field]].rename(columns={field: tickers[0]}) for field in data.columns}


def save_ohlcv(frames: dict[str, pd.DataFrame], out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_parquet(out / f"{name}.parquet")


MAX_RETRIES = 3
RETRY_DELAY_SEC = 2.0
DEFAULT_BATCH_SIZE = 50


def download_ohlcv_batch(
    tickers: list[str],
    start: str,
    end: str,
    auto_adjust: bool = True,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_retries: int = MAX_RETRIES,
) -> dict[str, pd.DataFrame]:
    """Download prices in batches with retry logic for robustness.

    Returns a flat dict-like result of {field_name: DataFrame} across all
    batches. The result also exposes ``frames``, ``failed_tickers`` and
    ``errors`` so failures are auditable without breaking existing callers.
    """
    all_frames: dict[str, pd.DataFrame] = {}
    failed_tickers: list[str] = []
    errors: dict[str, str] = {}

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            try:
                frames = download_ohlcv(batch, start, end, auto_adjust)
                downloaded_tickers: set[str] = set()
                for field, frame in frames.items():
                    valid_cols = [c for c in frame.columns if c in batch]
                    downloaded_tickers.update(valid_cols)
                    if field in all_frames:
                        existing_cols = set(all_frames[field].columns)
                        new_cols = [c for c in valid_cols if c not in existing_cols]
                        if new_cols:
                            all_frames[field] = pd.concat(
                                [all_frames[field], frame[new_cols]], axis=1,
                            )
                    else:
                        all_frames[field] = frame[valid_cols] if valid_cols else frame
                for missing_ticker in [ticker for ticker in batch if ticker not in downloaded_tickers]:
                    if missing_ticker not in errors:
                        failed_tickers.append(missing_ticker)
                        errors[missing_ticker] = "missing_from_download"
                success = True
            except Exception as exc:
                attempt += 1
                if attempt < max_retries:
                    logger.warning("Batch %d-%d failed (attempt %d/%d), retrying...",
                                   i, i + len(batch), attempt, max_retries)
                    time.sleep(RETRY_DELAY_SEC)
                else:
                    for ticker in batch:
                        if ticker not in errors:
                            failed_tickers.append(ticker)
                            errors[ticker] = str(exc)
                    logger.warning("Batch %d-%d failed after %d attempts, skipping.",
                                   i, i + len(batch), max_retries)

    return OhlcvBatchResult(all_frames, failed_tickers=failed_tickers, errors=errors)


def compute_price_coverage(
    tickers: list[str],
    prices: pd.DataFrame,
    start: str,
    end: str,
) -> pd.DataFrame:
    """Compute coverage report for downloaded price data."""
    total = len(tickers)
    expected_periods = pd.bdate_range(start=start, end=end)
    n_expected = len(expected_periods)

    rows: list[dict[str, object]] = [
        {"metric": "requested_tickers", "count": total, "pct": 100.0},
        {"metric": "expected_periods", "count": n_expected, "pct": 100.0},
    ]

    if prices.empty:
        rows.append({"metric": "tickers_with_data", "count": 0, "pct": 0.0})
        return pd.DataFrame(rows)

    available = [t for t in tickers if t in prices.columns and prices[t].notna().sum() > 0]
    pct_available = round(len(available) / total * 100, 2) if total > 0 else 0.0
    rows.append({"metric": "tickers_with_data", "count": len(available), "pct": pct_available})

    n_periods = len(prices)
    rows.append({"metric": "actual_periods", "count": n_periods, "pct": round(n_periods / n_expected * 100, 2)})

    return pd.DataFrame(rows)


def _format_valid_date(value: Any) -> str | None:
    if value is None:
        return None
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return None
    return timestamp.strftime("%Y-%m-%d")


def compute_ticker_coverage(
    tickers: list[str],
    prices: pd.DataFrame,
    start: str,
    end: str,
    min_coverage: float = 0.80,
) -> pd.DataFrame:
    """Compute per-ticker coverage audit for downloaded price data.

    The report is intentionally based on observed non-null prices rather than
    filling gaps, so missing history cannot be mistaken for investable data.
    """
    expected = pd.bdate_range(start=start, end=end)
    expected_obs = len(expected)
    columns = [
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
    rows: list[dict[str, object]] = []

    for ticker in tickers:
        if ticker not in prices.columns:
            rows.append(
                {
                    "ticker": ticker,
                    "requested": True,
                    "downloaded": False,
                    "first_valid": None,
                    "last_valid": None,
                    "n_obs": 0,
                    "expected_obs": expected_obs,
                    "coverage_pct": 0.0,
                    "nan_pct": 1.0,
                    "has_sufficient_history": False,
                    "error": "missing_column",
                }
            )
            continue

        requested_prices = prices[ticker].reindex(expected)
        valid_prices = requested_prices.dropna()
        n_obs = int(valid_prices.shape[0])
        coverage = n_obs / expected_obs if expected_obs else 0.0
        rows.append(
            {
                "ticker": ticker,
                "requested": True,
                "downloaded": n_obs > 0,
                "first_valid": _format_valid_date(valid_prices.index.min()) if n_obs else None,
                "last_valid": _format_valid_date(valid_prices.index.max()) if n_obs else None,
                "n_obs": n_obs,
                "expected_obs": expected_obs,
                "coverage_pct": round(coverage, 4),
                "nan_pct": round(1.0 - coverage, 4),
                "has_sufficient_history": coverage >= min_coverage,
                "error": None if n_obs else "no_prices",
            }
        )

    return pd.DataFrame(rows, columns=columns)
