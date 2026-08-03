from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from etf_optimizer.data.sec_universe import download_sec_series_class_snapshot

MASTER_COLUMNS = [
    "fund_id",
    "ticker",
    "ticker_start_date",
    "ticker_end_date",
    "cik",
    "series_id",
    "class_id",
    "fund_name",
    "issuer",
    "exchange",
    "asset_class_bucket",
    "inception_date",
    "termination_date",
    "delisted_date",
    "expense_ratio",
    "aum",
    "avg_dollar_volume",
    "source",
    "source_filing_date",
    "source_acceptance_date",
    "source_available_date",
    "data_quality_flag",
]

MINIMUM_TABLES = [
    "fund_master",
    "ticker_history",
    "sec_series_class_map",
    "listings_by_date",
    "price_ohlcv",
    "distributions_or_total_returns",
    "fund_metadata",
    "source_audit_log",
    "rebalance_universe_snapshots",
]


@dataclass(frozen=True)
class UniverseMasterResult:
    output_dir: Path
    table_paths: dict[str, str]
    snapshot_paths: list[str]


def month_start_dates(start: str = "2015-01-01", end: str = "2025-12-01") -> list[pd.Timestamp]:
    """Return first-calendar-day monthly rebalance dates inclusive."""
    return list(pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="MS"))


def _normalize_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "ticker_start_date",
        "ticker_end_date",
        "inception_date",
        "termination_date",
        "delisted_date",
        "source_filing_date",
        "source_acceptance_date",
        "source_available_date",
        "observation_start_date",
        "observation_end_date",
    ]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def _first_non_null(series: pd.Series) -> object:
    values = series.dropna()
    return values.iloc[0] if not values.empty else None


def _last_non_null(series: pd.Series) -> object:
    values = series.dropna()
    return values.iloc[-1] if not values.empty else None


def _infer_issuer(row: pd.Series) -> str | None:
    text = str(row.get("fund_name", "") or row.get("name", "")).upper()
    issuers = [
        "ISHARES",
        "VANGUARD",
        "SPDR",
        "INVESCO",
        "PROSHARES",
        "DIREXION",
        "WISDOMTREE",
        "FIRST TRUST",
        "GLOBAL X",
        "ARK",
        "VANECK",
        "PIMCO",
        "SCHWAB",
        "FIDELITY",
    ]
    for issuer in issuers:
        if issuer in text:
            return issuer.title()
    return None


def _infer_asset_class_bucket(row: pd.Series) -> str:
    text = " ".join(str(row.get(col, "") or "") for col in ["fund_name", "name", "series_name", "class_name"]).upper()
    if any(term in text for term in ["BOND", "TREASURY", "FIXED INCOME", "MUNICIPAL", "CORPORATE DEBT"]):
        return "fixed_income"
    if any(term in text for term in ["COMMODITY", "GOLD", "SILVER", "OIL", "NATURAL GAS"]):
        return "commodities"
    if any(term in text for term in ["REAL ESTATE", "REIT"]):
        return "real_estate"
    if any(term in text for term in ["INTERNATIONAL", "EMERGING", "EUROPE", "CHINA", "JAPAN"]):
        return "international_equity"
    if any(term in text for term in ["ETF", "EQUITY", "INDEX", "S&P", "NASDAQ", "RUSSELL"]):
        return "equity_or_multi_asset"
    return "unknown"


def sec_snapshot_to_listings(snapshot: pd.DataFrame, source_year: int) -> pd.DataFrame:
    """Convert a parsed SEC Series/Class annual snapshot into PIT listing observations.

    Series/Class annual files are public SEC register snapshots, not N-PORT/N-CEN filings.
    Therefore `source_filing_date` and `source_acceptance_date` are unavailable for these
    rows; `source_available_date` is set to the annual snapshot observation start and the
    row is flagged as `public_approximate_pit_sec_series_class_annual_snapshot`.
    """
    if snapshot.empty:
        return pd.DataFrame(columns=[*MASTER_COLUMNS, "observation_start_date", "observation_end_date", "source_year", "source_url"])

    df = snapshot.copy()
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["fund_id"] = df.get("fund_id", df["ticker"])
    df["fund_name"] = df.get("name", df.get("series_name", df.get("class_name", "")))
    df["issuer"] = df.apply(_infer_issuer, axis=1)
    df["asset_class_bucket"] = df.apply(_infer_asset_class_bucket, axis=1)
    start = pd.Timestamp(year=source_year, month=1, day=1)
    end = pd.Timestamp(year=source_year, month=12, day=31)
    first_seen_source = df["first_seen_date"] if "first_seen_date" in df.columns else pd.Series(start, index=df.index)
    last_seen_source = df["last_seen_date"] if "last_seen_date" in df.columns else pd.Series(end, index=df.index)
    df["ticker_start_date"] = pd.to_datetime(first_seen_source, errors="coerce").fillna(start)
    df["ticker_end_date"] = pd.to_datetime(last_seen_source, errors="coerce").fillna(end)
    df["observation_start_date"] = start
    df["observation_end_date"] = end
    df["source_available_date"] = start
    df["source_filing_date"] = pd.NaT
    df["source_acceptance_date"] = pd.NaT
    df["delisted_date"] = pd.NaT
    df["expense_ratio"] = pd.NA
    df["aum"] = pd.NA
    df["avg_dollar_volume"] = pd.NA
    df["source"] = "sec_series_class"
    df["source_year"] = source_year
    df["data_quality_flag"] = "public_approximate_pit_sec_series_class_annual_snapshot"
    for col in MASTER_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    cols = [*MASTER_COLUMNS, "observation_start_date", "observation_end_date", "source_year", "source_url"]
    return _normalize_date_columns(df[cols]).drop_duplicates(["ticker", "cik", "series_id", "class_id", "source_year"])


def build_fund_master(listings_by_date: pd.DataFrame) -> pd.DataFrame:
    """Collapse annual listing observations into a fund-level master table."""
    if listings_by_date.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)
    df = _normalize_date_columns(listings_by_date)
    rows: list[dict[str, object]] = []
    group_cols = ["fund_id"]
    for fund_id, group in df.sort_values(["fund_id", "observation_start_date"]).groupby(group_cols, dropna=False):
        if isinstance(fund_id, tuple):
            fund_id = fund_id[0]
        last = group.iloc[-1]
        row = {col: last.get(col, pd.NA) for col in MASTER_COLUMNS}
        row["fund_id"] = fund_id
        row["ticker_start_date"] = group["ticker_start_date"].min()
        row["ticker_end_date"] = group["ticker_end_date"].max()
        row["inception_date"] = group["inception_date"].dropna().min() if group["inception_date"].notna().any() else pd.NaT
        row["termination_date"] = group["termination_date"].dropna().min() if group["termination_date"].notna().any() else pd.NaT
        row["delisted_date"] = group["delisted_date"].dropna().min() if group["delisted_date"].notna().any() else pd.NaT
        row["source_available_date"] = group["source_available_date"].min()
        row["source_filing_date"] = _last_non_null(group.get("source_filing_date", pd.Series(dtype=object)))
        row["source_acceptance_date"] = _last_non_null(group.get("source_acceptance_date", pd.Series(dtype=object)))
        if group["observation_end_date"].max() < pd.Timestamp("2025-12-31"):
            row["data_quality_flag"] = f"{last.get('data_quality_flag')}; disappeared_before_2025_end_unverified_termination"
        rows.append(row)
    return _normalize_date_columns(pd.DataFrame(rows)[MASTER_COLUMNS]).sort_values("ticker").reset_index(drop=True)


def build_ticker_history(listings_by_date: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "fund_id",
        "ticker",
        "ticker_start_date",
        "ticker_end_date",
        "source_available_date",
        "source",
        "data_quality_flag",
    ]
    if listings_by_date.empty:
        return pd.DataFrame(columns=cols)
    df = _normalize_date_columns(listings_by_date)
    rows = []
    for (fund_id, ticker), group in df.groupby(["fund_id", "ticker"], dropna=False):
        rows.append(
            {
                "fund_id": fund_id,
                "ticker": ticker,
                "ticker_start_date": group["ticker_start_date"].min(),
                "ticker_end_date": group["ticker_end_date"].max(),
                "source_available_date": group["source_available_date"].min(),
                "source": ";".join(sorted(group["source"].dropna().astype(str).unique())),
                "data_quality_flag": ";".join(sorted(group["data_quality_flag"].dropna().astype(str).unique())),
            }
        )
    return pd.DataFrame(rows).sort_values(["ticker", "ticker_start_date"]).reset_index(drop=True)


def build_rebalance_snapshot(listings_by_date: pd.DataFrame, rebalance_date: str | pd.Timestamp) -> pd.DataFrame:
    """Return only ETFs observable and investable under `source_available_date <= t`."""
    as_of = pd.Timestamp(rebalance_date)
    df = _normalize_date_columns(listings_by_date)
    if df.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)
    mask = df["source_available_date"].notna() & (df["source_available_date"] <= as_of)
    mask &= df["observation_start_date"].isna() | (df["observation_start_date"] <= as_of)
    mask &= df["observation_end_date"].isna() | (df["observation_end_date"] >= as_of)
    mask &= df["ticker_start_date"].isna() | (df["ticker_start_date"] <= as_of)
    mask &= df["ticker_end_date"].isna() | (df["ticker_end_date"] >= as_of)
    mask &= df["termination_date"].isna() | (df["termination_date"] > as_of)
    mask &= df["delisted_date"].isna() | (df["delisted_date"] > as_of)
    snapshot = df.loc[mask, MASTER_COLUMNS].copy()
    if snapshot.empty:
        return snapshot
    snapshot = snapshot.sort_values(["ticker", "source_available_date"]).drop_duplicates("fund_id", keep="last")
    snapshot.insert(0, "rebalance_date", as_of.date().isoformat())
    return snapshot.sort_values("ticker").reset_index(drop=True)


def load_price_tables(price_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load existing public OHLCV parquet files into long OHLCV and return tables."""
    required = {name: price_dir / f"{name}.parquet" for name in ["open", "high", "low", "close", "volume"]}
    if not all(path.exists() for path in required.values()):
        return pd.DataFrame(), pd.DataFrame()
    frames = {name: pd.read_parquet(path) for name, path in required.items()}
    if frames["close"].empty:
        return pd.DataFrame(), pd.DataFrame()
    long_parts = []
    for name, frame in frames.items():
        part = frame.copy()
        part.index.name = "date"
        stacked = part.stack()
        stacked.name = name
        long_parts.append(stacked)
    ohlcv = pd.concat(long_parts, axis=1).reset_index().rename(columns={"level_1": "ticker"})
    ohlcv["source"] = "public_yfinance_pilot"
    ohlcv["data_quality_flag"] = "public_price_not_universe_authority_adjusted_close_unavailable"
    ohlcv = ohlcv.dropna(subset=["close"], how="all")

    returns = frames["close"].pct_change(fill_method=None)
    returns.index.name = "date"
    stacked_returns = returns.stack()
    stacked_returns.name = "price_return"
    total_returns = stacked_returns.reset_index().rename(columns={"level_1": "ticker"})
    total_returns["distribution"] = pd.NA
    total_returns["total_return"] = pd.NA
    total_returns["source"] = "public_yfinance_pilot_close_returns"
    total_returns["data_quality_flag"] = "price_return_only_no_distribution_or_liquidation_return"
    return ohlcv, total_returns


def _write_table(df: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
    return str(path)


def build_universe_master_from_sec(
    *,
    years: Iterable[int] = range(2015, 2026),
    output_dir: Path = Path("data/universe_master"),
    price_dir: Path | None = Path("data/raw/yfinance_pilot_2015_2025"),
    rebalance_dates: Iterable[pd.Timestamp] | None = None,
) -> UniverseMasterResult:
    """Download SEC annual Series/Class snapshots and write Universe Master tables."""
    output_dir = Path(output_dir)
    audit_rows: list[dict[str, object]] = []
    listing_frames: list[pd.DataFrame] = []
    previous_listings: pd.DataFrame | None = None
    for year in years:
        try:
            snapshot = download_sec_series_class_snapshot(int(year))
            listings = sec_snapshot_to_listings(snapshot, int(year))
            if not listings.empty:
                previous_listings = listings.copy()
            listing_frames.append(listings)
            audit_rows.append(
                {
                    "source": "sec_series_class",
                    "source_year": int(year),
                    "source_url": listings["source_url"].dropna().iloc[0] if not listings.empty and listings["source_url"].notna().any() else pd.NA,
                    "records_loaded": len(listings),
                    "status": "ok",
                    "data_quality_flag": "public_approximate_pit_sec_series_class_annual_snapshot",
                }
            )
        except Exception as exc:  # pragma: no cover - exercised in live data runs
            if previous_listings is not None and not previous_listings.empty:
                listings = previous_listings.copy()
                start = pd.Timestamp(year=int(year), month=1, day=1)
                end = pd.Timestamp(year=int(year), month=12, day=31)
                listings["observation_start_date"] = start
                listings["observation_end_date"] = end
                listings["ticker_start_date"] = start
                listings["ticker_end_date"] = end
                listings["source_year"] = int(year)
                listings["data_quality_flag"] = listings["data_quality_flag"].astype(str) + "; stale_forward_filled_from_prior_sec_snapshot_due_missing_annual_file"
                listing_frames.append(listings)
                status = f"forward_filled_from_prior_snapshot_after_error: {exc}"
                records_loaded = len(listings)
            else:
                status = f"error: {exc}"
                records_loaded = 0
            audit_rows.append(
                {
                    "source": "sec_series_class",
                    "source_year": int(year),
                    "source_url": pd.NA,
                    "records_loaded": records_loaded,
                    "status": status,
                    "data_quality_flag": "stale_forward_fill" if records_loaded else "source_download_failed",
                }
            )
    listings_by_date = pd.concat(listing_frames, ignore_index=True) if listing_frames else pd.DataFrame(columns=[*MASTER_COLUMNS, "observation_start_date", "observation_end_date", "source_year", "source_url"])
    fund_master = build_fund_master(listings_by_date)
    ticker_history = build_ticker_history(listings_by_date)
    sec_series_class_map = listings_by_date[
        [
            "fund_id",
            "ticker",
            "cik",
            "series_id",
            "class_id",
            "fund_name",
            "source_year",
            "source_available_date",
            "source_url",
            "data_quality_flag",
        ]
    ].drop_duplicates()
    fund_metadata = fund_master[
        [
            "fund_id",
            "ticker",
            "fund_name",
            "issuer",
            "asset_class_bucket",
            "expense_ratio",
            "aum",
            "source",
            "data_quality_flag",
        ]
    ].copy()
    price_ohlcv, distributions_or_total_returns = load_price_tables(Path(price_dir)) if price_dir else (pd.DataFrame(), pd.DataFrame())
    if price_ohlcv.empty:
        price_ohlcv = pd.DataFrame(columns=["date", "ticker", "open", "high", "low", "close", "volume", "source", "data_quality_flag"])
    if distributions_or_total_returns.empty:
        distributions_or_total_returns = pd.DataFrame(columns=["date", "ticker", "price_return", "distribution", "total_return", "source", "data_quality_flag"])

    table_paths = {
        "fund_master": _write_table(fund_master, output_dir / "fund_master.csv"),
        "ticker_history": _write_table(ticker_history, output_dir / "ticker_history.csv"),
        "sec_series_class_map": _write_table(sec_series_class_map, output_dir / "sec_series_class_map.csv"),
        "listings_by_date": _write_table(listings_by_date, output_dir / "listings_by_date.csv"),
        "price_ohlcv": _write_table(price_ohlcv, output_dir / "price_ohlcv.parquet"),
        "distributions_or_total_returns": _write_table(distributions_or_total_returns, output_dir / "distributions_or_total_returns.csv"),
        "fund_metadata": _write_table(fund_metadata, output_dir / "fund_metadata.csv"),
        "source_audit_log": _write_table(pd.DataFrame(audit_rows), output_dir / "source_audit_log.csv"),
    }

    snapshot_dir = output_dir / "rebalance_universe_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_paths: list[str] = []
    for dt in rebalance_dates or month_start_dates():
        snapshot = build_rebalance_snapshot(listings_by_date, dt)
        path = snapshot_dir / f"rebalance_universe_{pd.Timestamp(dt):%Y_%m}.csv"
        snapshot_paths.append(_write_table(snapshot, path))

    manifest = {
        "tables": table_paths,
        "snapshot_count": len(snapshot_paths),
        "snapshots_first": snapshot_paths[0] if snapshot_paths else None,
        "snapshots_last": snapshot_paths[-1] if snapshot_paths else None,
        "point_in_time_rule": "source_available_date <= rebalance_date",
        "data_quality_verdict": "public_approximate_pit",
        "minimum_tables": MINIMUM_TABLES,
    }
    (output_dir / "universe_master_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return UniverseMasterResult(output_dir=output_dir, table_paths=table_paths, snapshot_paths=snapshot_paths)
