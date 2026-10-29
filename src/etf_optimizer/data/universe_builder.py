from __future__ import annotations

from pathlib import Path

import pandas as pd

from etf_optimizer.data.schema import CANONICAL_COLUMNS, convert_dates, make_fund_id, normalize_tickers
from etf_optimizer.data.public_universe import load_public_current_etf_snapshot
from etf_optimizer.data.sec_universe import load_sec_company_tickers_exchange


def merge_universe_sources(
    sources: list[pd.DataFrame],
    source_names: list[str] | None = None,
) -> pd.DataFrame:
    """Merge universe DataFrames, deduplicating by fund_id.

    Earlier sources have priority for non-null values. Use this for multiple ETF-specific
    sources, not for appending broad all-equity registrant databases.
    """
    if not sources:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    normalized = []
    for df in sources:
        if df.empty:
            continue
        df = normalize_tickers(df.copy())
        df = convert_dates(df)
        if "fund_id" not in df.columns or df["fund_id"].isna().all():
            df["fund_id"] = df.apply(make_fund_id, axis=1)
        normalized.append(df)

    if not normalized:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    combined = pd.concat(normalized, ignore_index=True)
    for col in CANONICAL_COLUMNS:
        if col not in combined.columns:
            combined[col] = None
    combined = combined[CANONICAL_COLUMNS].dropna(subset=["fund_id"])
    return _deduplicate_by_fund_id(combined).reset_index(drop=True)


def _deduplicate_by_fund_id(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate by fund_id, keeping the first source but filling missing values."""
    seen: dict[str, dict[str, object]] = {}
    for _, row in df.iterrows():
        fid = str(row["fund_id"])
        if fid not in seen:
            seen[fid] = row.to_dict()
            continue
        existing = seen[fid]
        for col in df.columns:
            val = row.get(col)
            existing_val = existing.get(col)
            if pd.notna(val) and (existing_val is None or pd.isna(existing_val)):
                existing[col] = val
    return pd.DataFrame.from_dict(seen, orient="index")


def enrich_universe_with_sec_metadata(universe: pd.DataFrame, sec: pd.DataFrame) -> pd.DataFrame:
    """Add SEC CIK/exchange/name metadata by ticker without expanding the ETF universe.

    SEC company tickers are a broad registrant crosswalk, not an ETF-only universe. This
    function prevents accidentally adding all listed equities to the ETF candidate set.
    """
    if universe.empty or sec.empty or "ticker" not in universe.columns or "ticker" not in sec.columns:
        return universe.copy()
    base = normalize_tickers(universe.copy())
    sec_meta = normalize_tickers(sec.copy()).drop_duplicates("ticker")
    fill_cols = [col for col in ["cik", "exchange", "source_url"] if col in sec_meta.columns]
    enriched = base.merge(sec_meta[["ticker", *fill_cols]], on="ticker", how="left", suffixes=("", "_sec"))
    for col in fill_cols:
        sec_col = f"{col}_sec"
        if sec_col in enriched.columns:
            if col in enriched.columns:
                enriched[col] = enriched[col].combine_first(enriched[sec_col])
            else:
                enriched[col] = enriched[sec_col]
            enriched = enriched.drop(columns=[sec_col])
    if "source" in enriched.columns:
        enriched["source"] = enriched["source"].fillna("nasdaq")
    return enriched


def build_universe(
    include_sec: bool = True,
    include_public: bool = True,
    extra_sources: list[pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Build a merged ETF universe from ETF-specific sources and SEC metadata.

    Public/current ETF snapshots and user-provided extras define membership. SEC is used
    only to enrich matching tickers with legal identifiers; it is not unioned in by default.
    """
    sources: list[pd.DataFrame] = []
    if include_public:
        sources.append(load_public_current_etf_snapshot())
    if extra_sources:
        sources.extend(extra_sources)

    universe = merge_universe_sources(sources)
    if include_sec and not universe.empty:
        universe = enrich_universe_with_sec_metadata(universe, load_sec_company_tickers_exchange())
        universe = merge_universe_sources([universe])
    return universe


def generate_coverage_report(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a coverage report for the universe."""
    total = len(df)
    if total == 0:
        return pd.DataFrame({"metric": ["total_funds"], "count": [0], "pct": [0.0]})

    rows: list[dict[str, object]] = [{"metric": "total_funds", "count": total, "pct": 100.0}]
    for col in ["ticker", "name", "cik", "exchange", "sponsor", "inception_date", "termination_date"]:
        if col in df.columns:
            n = int(df[col].notna().sum())
            rows.append({"metric": f"{col}_present", "count": n, "pct": round(n / total * 100, 2)})
    if "source" in df.columns:
        for src in df["source"].dropna().unique():
            n = int((df["source"] == src).sum())
            rows.append({"metric": f"source_{src}", "count": n, "pct": round(n / total * 100, 2)})
    n_active = int(df["active_flag"].sum()) if "active_flag" in df.columns else total
    rows.append({"metric": "active", "count": n_active, "pct": round(n_active / total * 100, 2)})
    return pd.DataFrame(rows)


def write_universe_snapshot(
    df: pd.DataFrame,
    out_dir: str | Path,
    prefix: str = "etf_universe",
) -> dict[str, Path]:
    """Write raw, clean, and coverage report CSVs to out_dir."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_path = out / f"{prefix}_raw.csv"
    df.to_csv(raw_path, index=False)
    clean = df.drop_duplicates("fund_id").copy()
    clean_path = out / f"{prefix}_clean.csv"
    clean.to_csv(clean_path, index=False)
    coverage_path = out / f"{prefix}_coverage_report.csv"
    generate_coverage_report(clean).to_csv(coverage_path, index=False)
    return {"raw": raw_path, "clean": clean_path, "coverage": coverage_path}
