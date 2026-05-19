from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


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

    Returns a flat dict of {field_name: DataFrame} across all batches.
    """
    all_frames: dict[str, pd.DataFrame] = {}
    failed_tickers: list[str] = []

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            try:
                frames = download_ohlcv(batch, start, end, auto_adjust)
                for field, frame in frames.items():
                    valid_cols = [c for c in frame.columns if c in batch]
                    if field in all_frames:
                        existing_cols = set(all_frames[field].columns)
                        new_cols = [c for c in valid_cols if c not in existing_cols]
                        if new_cols:
                            all_frames[field] = pd.concat(
                                [all_frames[field], frame[new_cols]], axis=1,
                            )
                    else:
                        all_frames[field] = frame[valid_cols] if valid_cols else frame
                success = True
            except Exception:
                attempt += 1
                if attempt < max_retries:
                    logger.warning("Batch %d-%d failed (attempt %d/%d), retrying...",
                                   i, i + len(batch), attempt, max_retries)
                    time.sleep(RETRY_DELAY_SEC)
                else:
                    failed_tickers.extend(batch)
                    logger.warning("Batch %d-%d failed after %d attempts, skipping.",
                                   i, i + len(batch), max_retries)

    return all_frames


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
