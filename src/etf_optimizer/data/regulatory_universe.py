from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, Literal

import numpy as np
import pandas as pd

from etf_optimizer.features import returns_from_prices, tracking_error

SourceType = Literal["regulatory", "issuer", "identifier_api", "price_api", "web_reference", "manual_curated"]
AllowedUse = Literal["primary", "fallback", "manual_reference", "disallowed"]
BenchmarkType = Literal["official", "issuer_stated", "proxy", "inferred", "missing"]
FallbackLevel = Literal["primary", "secondary", "proxy", "missing"]

SOURCE_TYPES: tuple[str, ...] = (
    "regulatory",
    "issuer",
    "identifier_api",
    "price_api",
    "web_reference",
    "manual_curated",
)
SOURCE_ALLOWED_USES: tuple[str, ...] = ("primary", "fallback", "manual_reference", "disallowed")
BENCHMARK_TYPES: tuple[str, ...] = ("official", "issuer_stated", "proxy", "inferred", "missing")
FALLBACK_LEVELS: tuple[str, ...] = ("primary", "secondary", "proxy", "missing")

SEC_RATE_LIMIT_POLICY = (
    "Use a descriptive User-Agent, avoid burst traffic, cache retrieved filings, "
    "and keep request rates within current SEC fair-access guidance."
)
OPENFIGI_RATE_LIMIT_POLICY = "Respect OpenFIGI API key/no-key rate limits and cache identifier mappings."

SOURCE_REGISTRY_COLUMNS = [
    "source_id",
    "source_name",
    "source_type",
    "base_url",
    "license_or_terms_summary",
    "allowed_use",
    "retrieval_method",
    "rate_limit_policy",
    "quality_rank",
    "notes",
]

SEC_NPORT_DATASETS_URL = "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets"
SEC_NCEN_DATASETS_URL = "https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/"
OPENFIGI_DOCS_URL = "https://www.openfigi.com/api/documentation"
YFINANCE_REPO_URL = "https://github.com/ranaroussi/yfinance"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_name: str
    source_type: SourceType
    base_url: str
    license_or_terms_summary: str
    allowed_use: AllowedUse
    retrieval_method: str
    rate_limit_policy: str
    quality_rank: str
    notes: str = ""


def default_source_registry() -> pd.DataFrame:
    """Return the approved public/regulatory source registry for thesis runs."""
    records = [
        SourceRecord(
            "sec_nport",
            "SEC Form N-PORT Data Sets",
            "regulatory",
            SEC_NPORT_DATASETS_URL,
            "Public SEC data; no guarantee of completeness or restatement-free history.",
            "primary",
            "downloaded SEC structured datasets or filings",
            SEC_RATE_LIMIT_POLICY,
            "high",
            "Primary 2019+ holdings/net-assets source for public regulatory PIT evidence.",
        ),
        SourceRecord(
            "sec_ncen",
            "SEC Form N-CEN Data Sets",
            "regulatory",
            SEC_NCEN_DATASETS_URL,
            "Public SEC data; annual fund metadata with public-data limitations.",
            "primary",
            "downloaded SEC structured datasets or filings",
            SEC_RATE_LIMIT_POLICY,
            "high",
            "ETF status and operational metadata source.",
        ),
        SourceRecord(
            "sec_edgar_submissions",
            "SEC EDGAR submissions JSON",
            "regulatory",
            SEC_SUBMISSIONS_URL,
            "Public SEC endpoint; requires fair-access behavior.",
            "primary",
            "CIK submissions JSON and filing archives",
            SEC_RATE_LIMIT_POLICY,
            "high",
            "Filing index, first/last observed filing and amendment audit trail.",
        ),
        SourceRecord(
            "openfigi",
            "OpenFIGI API",
            "identifier_api",
            OPENFIGI_DOCS_URL,
            "Public API with documented rate limits; identifier mapping only.",
            "fallback",
            "API lookup with cached responses",
            OPENFIGI_RATE_LIMIT_POLICY,
            "medium_high",
            "Used to corroborate CUSIP/ISIN/FIGI mappings, not as universe authority.",
        ),
        SourceRecord(
            "issuer_metadata",
            "ETF issuer factsheets/product pages",
            "issuer",
            "issuer-specific official product pages and downloads",
            "Terms vary by issuer; use only allowed downloads and cite restrictions.",
            "fallback",
            "downloaded official issuer files or manually curated factsheets",
            "Respect issuer terms, robots, and cache files.",
            "medium_high",
            "Expense ratio, benchmark, inception and holdings fallback.",
        ),
        SourceRecord(
            "public_price_yfinance",
            "yfinance public price access",
            "price_api",
            YFINANCE_REPO_URL,
            "Library is open-source; underlying Yahoo data has usage restrictions.",
            "fallback",
            "OHLCV download or local parquet derived from public prices",
            "Cache downloads and disclose public vendor limitations.",
            "medium",
            "Performance and liquidity input, not universe authority.",
        ),
    ]
    return pd.DataFrame([record.__dict__ for record in records], columns=SOURCE_REGISTRY_COLUMNS)


def validate_source_registry(registry: pd.DataFrame) -> list[str]:
    """Return validation errors for the source registry contract."""
    errors: list[str] = []
    missing = [column for column in SOURCE_REGISTRY_COLUMNS if column not in registry.columns]
    if missing:
        errors.append(f"missing source registry columns: {missing}")
        return errors
    invalid_types = sorted(set(registry["source_type"].dropna().astype(str)) - set(SOURCE_TYPES))
    if invalid_types:
        errors.append(f"invalid source_type values: {invalid_types}")
    invalid_use = sorted(set(registry["allowed_use"].dropna().astype(str)) - set(SOURCE_ALLOWED_USES))
    if invalid_use:
        errors.append(f"invalid allowed_use values: {invalid_use}")
    if registry["source_id"].duplicated().any():
        errors.append("source_id values must be unique")
    return errors


def _clean_identifier(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().upper()
    if not text or text in {"NAN", "NONE", "<NA>"}:
        return None
    return text


def stable_security_id(row: pd.Series | dict[str, object]) -> str:
    """Create a stable ETF identity from regulatory/security identifiers, not ticker alone."""
    get = row.get if isinstance(row, dict) else row.get
    identifier_sets = [
        ("cik", "series_id", "class_id"),
        ("figi",),
        ("isin",),
        ("cusip",),
    ]
    for keys in identifier_sets:
        values = [_clean_identifier(get(key)) for key in keys]
        if all(values):
            raw = "|".join(values)  # type: ignore[arg-type]
            digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
            return f"ETF-{digest}"
    ticker = _clean_identifier(get("ticker")) or "UNKNOWN"
    issuer = _clean_identifier(get("issuer")) or _clean_identifier(get("fund_name")) or "UNVERIFIED"
    digest = hashlib.sha1(f"{ticker}|{issuer}".encode("utf-8")).hexdigest()[:12]
    return f"ETF-UNVERIFIED-{digest}"


SECURITY_MASTER_COLUMNS = [
    "security_id",
    "ticker",
    "cusip",
    "isin",
    "figi",
    "cik",
    "series_id",
    "class_id",
    "fund_name",
    "issuer",
    "exchange",
    "currency",
    "inception_date",
    "closure_date",
    "valid_from",
    "valid_to",
    "identifier_confidence",
    "identity_qc_flags",
]


def build_security_master(records: pd.DataFrame) -> pd.DataFrame:
    """Normalize ETF identity records into a stable security master."""
    if records.empty:
        return pd.DataFrame(columns=SECURITY_MASTER_COLUMNS)
    df = records.copy()
    for col in SECURITY_MASTER_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    if "security_id" not in records.columns or df["security_id"].isna().all():
        df["security_id"] = df.apply(stable_security_id, axis=1)
    for col in ["ticker", "cusip", "isin", "figi", "cik", "series_id", "class_id"]:
        df[col] = df[col].map(_clean_identifier)
    for col in ["inception_date", "closure_date", "valid_from", "valid_to"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    has_regulatory_key = df[["cik", "series_id", "class_id"]].notna().all(axis=1)
    has_security_key = df[["figi", "isin", "cusip"]].notna().any(axis=1)
    df["identifier_confidence"] = np.select(
        [has_regulatory_key, has_security_key],
        ["high_regulatory_series_class", "medium_security_identifier"],
        default="low_ticker_issuer_fallback",
    )
    flags = []
    for _, row in df.iterrows():
        row_flags = []
        if str(row["security_id"]).startswith("ETF-UNVERIFIED"):
            row_flags.append("ticker_not_durable_identity")
        if pd.isna(row.get("cik")):
            row_flags.append("missing_cik")
        if pd.isna(row.get("series_id")) or pd.isna(row.get("class_id")):
            row_flags.append("missing_series_class")
        flags.append(";".join(row_flags))
    df["identity_qc_flags"] = flags
    return df[SECURITY_MASTER_COLUMNS].drop_duplicates("security_id").sort_values("ticker").reset_index(drop=True)


IDENTIFIER_MAPPING_COLUMNS = [
    "security_id",
    "identifier_type",
    "identifier_value",
    "valid_from",
    "valid_to",
    "mapping_confidence",
]


def build_identifier_mappings(security_master: pd.DataFrame) -> pd.DataFrame:
    """Explode security master identifiers into validity-scoped mapping records."""
    rows: list[dict[str, object]] = []
    if security_master.empty:
        return pd.DataFrame(columns=IDENTIFIER_MAPPING_COLUMNS)
    for _, row in security_master.iterrows():
        for identifier_type in ["ticker", "cusip", "isin", "figi", "cik", "series_id", "class_id"]:
            value = _clean_identifier(row.get(identifier_type))
            if value is None:
                continue
            rows.append(
                {
                    "security_id": row["security_id"],
                    "identifier_type": identifier_type,
                    "identifier_value": value,
                    "valid_from": row.get("valid_from"),
                    "valid_to": row.get("valid_to"),
                    "mapping_confidence": row.get("identifier_confidence", "unknown"),
                }
            )
    return pd.DataFrame(rows, columns=IDENTIFIER_MAPPING_COLUMNS)


def detect_identifier_ambiguities(mappings: pd.DataFrame) -> pd.DataFrame:
    """Detect identifiers mapping to multiple security IDs inside overlapping/unscoped periods."""
    if mappings.empty:
        return pd.DataFrame(columns=["identifier_type", "identifier_value", "security_ids", "ambiguity_flag"])
    rows: list[dict[str, object]] = []
    for (identifier_type, identifier_value), group in mappings.groupby(["identifier_type", "identifier_value"], dropna=False):
        security_ids = sorted(set(group["security_id"].dropna().astype(str)))
        if len(security_ids) > 1:
            rows.append(
                {
                    "identifier_type": identifier_type,
                    "identifier_value": identifier_value,
                    "security_ids": ";".join(security_ids),
                    "ambiguity_flag": "identifier_maps_to_multiple_security_ids",
                }
            )
    return pd.DataFrame(rows, columns=["identifier_type", "identifier_value", "security_ids", "ambiguity_flag"])


FILING_INDEX_COLUMNS = [
    "filing_id",
    "source_id",
    "cik",
    "accession_number",
    "form_type",
    "period_end_date",
    "filed_date",
    "accepted_datetime",
    "public_available_date",
    "source_url",
    "is_amendment",
    "amends_accession",
    "filing_qc_flags",
]


def build_filing_index(raw_filings: pd.DataFrame, *, default_source_id: str = "sec_edgar_submissions") -> pd.DataFrame:
    """Normalize EDGAR/N-PORT/N-CEN filing metadata without overwriting amendments."""
    if raw_filings.empty:
        return pd.DataFrame(columns=FILING_INDEX_COLUMNS)
    df = raw_filings.copy()
    aliases = {
        "accessionNumber": "accession_number",
        "accession": "accession_number",
        "form": "form_type",
        "reportDate": "period_end_date",
        "periodOfReport": "period_end_date",
        "filingDate": "filed_date",
        "acceptanceDateTime": "accepted_datetime",
        "primaryDocumentUrl": "source_url",
    }
    df = df.rename(columns={old: new for old, new in aliases.items() if old in df.columns})
    for col in FILING_INDEX_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df["source_id"] = df["source_id"].fillna(default_source_id)
    df["cik"] = df["cik"].map(lambda value: str(value).split(".")[0].zfill(10) if pd.notna(value) else pd.NA)
    for col in ["period_end_date", "filed_date", "accepted_datetime", "public_available_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["public_available_date"] = df["public_available_date"].fillna(df["accepted_datetime"]).fillna(df["filed_date"])
    df["is_amendment"] = df["is_amendment"].fillna(df["form_type"].astype(str).str.endswith("/A")).astype(bool)
    if "filing_id" not in raw_filings.columns or df["filing_id"].isna().all():
        df["filing_id"] = df.apply(
            lambda row: f"{row['cik']}-{row['accession_number']}" if pd.notna(row["accession_number"]) else hashlib.sha1(str(row.to_dict()).encode("utf-8")).hexdigest()[:16],
            axis=1,
        )
    flags = []
    for _, row in df.iterrows():
        row_flags = []
        if pd.isna(row.get("public_available_date")):
            row_flags.append("missing_public_available_date")
        if bool(row.get("is_amendment")) and pd.isna(row.get("amends_accession")):
            row_flags.append("amendment_without_linked_accession")
        flags.append(";".join(row_flags))
    df["filing_qc_flags"] = flags
    return df[FILING_INDEX_COLUMNS].sort_values(["cik", "public_available_date", "accession_number"]).reset_index(drop=True)


FUND_SNAPSHOT_COLUMNS = [
    "security_id",
    "filing_id",
    "as_of_date",
    "filed_date",
    "public_available_date",
    "aum_or_net_assets",
    "nav",
    "shares_outstanding",
    "expense_ratio",
    "issuer",
    "category",
    "asset_class",
    "benchmark_name",
    "etf_flag",
    "confidence",
    "snapshot_qc_flags",
]

HOLDINGS_SNAPSHOT_COLUMNS = [
    "security_id",
    "filing_id",
    "holding_id",
    "as_of_date",
    "public_available_date",
    "holding_name",
    "holding_cusip",
    "holding_isin",
    "holding_figi",
    "market_value",
    "weight",
    "shares",
    "asset_type",
    "sector",
    "country",
    "holding_qc_flags",
]


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = pd.NA
    return out


def build_fund_snapshots(records: pd.DataFrame) -> pd.DataFrame:
    """Normalize fund-level snapshots and flag missing thesis-critical metadata."""
    df = _ensure_columns(records, FUND_SNAPSHOT_COLUMNS)
    for col in ["as_of_date", "filed_date", "public_available_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["public_available_date"] = df["public_available_date"].fillna(df["filed_date"])
    flags = []
    for _, row in df.iterrows():
        row_flags = []
        if pd.isna(row.get("expense_ratio")):
            row_flags.append("missing_expense_ratio")
        if pd.isna(row.get("benchmark_name")):
            row_flags.append("missing_benchmark")
        if pd.isna(row.get("public_available_date")):
            row_flags.append("missing_public_available_date")
        if pd.notna(row.get("public_available_date")) and pd.notna(row.get("as_of_date")) and row["public_available_date"] < row["as_of_date"]:
            row_flags.append("public_date_before_measurement_date_check_source")
        flags.append(";".join(row_flags))
    df["snapshot_qc_flags"] = flags
    df["confidence"] = df["confidence"].fillna("medium")
    return df[FUND_SNAPSHOT_COLUMNS].reset_index(drop=True)


def build_holdings_snapshots(records: pd.DataFrame) -> pd.DataFrame:
    """Normalize holdings snapshots and preserve public availability dates."""
    df = _ensure_columns(records, HOLDINGS_SNAPSHOT_COLUMNS)
    for col in ["as_of_date", "public_available_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    if df["holding_id"].isna().any():
        df["holding_id"] = df.apply(
            lambda row: hashlib.sha1(
                "|".join(str(row.get(col, "")) for col in ["security_id", "holding_cusip", "holding_isin", "holding_name"]).encode("utf-8")
            ).hexdigest()[:16],
            axis=1,
        )
    flags = []
    for _, row in df.iterrows():
        row_flags = []
        if pd.isna(row.get("weight")) and pd.isna(row.get("market_value")):
            row_flags.append("incomplete_holdings_value")
        if pd.isna(row.get("public_available_date")):
            row_flags.append("missing_public_available_date")
        flags.append(";".join(row_flags))
    df["holding_qc_flags"] = flags
    return df[HOLDINGS_SNAPSHOT_COLUMNS].reset_index(drop=True)


def validate_snapshot_dates(snapshot: pd.DataFrame) -> list[str]:
    """Check that snapshots keep economic and public-availability dates."""
    errors: list[str] = []
    for col in ["as_of_date", "public_available_date"]:
        if col not in snapshot.columns:
            errors.append(f"missing {col}")
    if not errors and snapshot["public_available_date"].isna().any():
        errors.append("public_available_date contains missing values")
    return errors


PRICE_HISTORY_COLUMNS = [
    "security_id",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
    "dividend",
    "split",
    "source_id",
    "retrieved_at",
    "price_qc_flags",
]


def normalize_price_history(
    prices: pd.DataFrame,
    *,
    volume: pd.DataFrame | None = None,
    adjusted_prices: pd.DataFrame | None = None,
    security_master: pd.DataFrame | None = None,
    source_id: str = "public_price_yfinance",
    retrieved_at: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Normalize wide public price panels into long price-history records."""
    if prices.empty:
        return pd.DataFrame(columns=PRICE_HISTORY_COLUMNS)
    ticker_to_security = {}
    if security_master is not None and not security_master.empty and {"ticker", "security_id"}.issubset(security_master.columns):
        ticker_to_security = security_master.drop_duplicates("ticker").set_index("ticker")["security_id"].astype(str).to_dict()
    rows: list[dict[str, object]] = []
    retrieved = pd.Timestamp(retrieved_at) if retrieved_at is not None else pd.Timestamp.utcnow()
    for ticker in prices.columns:
        security_id = ticker_to_security.get(str(ticker), stable_security_id({"ticker": ticker}))
        for date, close in prices[ticker].items():
            if pd.isna(close):
                continue
            vol = volume.at[date, ticker] if volume is not None and ticker in volume.columns and date in volume.index else pd.NA
            adj = adjusted_prices.at[date, ticker] if adjusted_prices is not None and ticker in adjusted_prices.columns and date in adjusted_prices.index else close
            flags = []
            if pd.isna(adj):
                flags.append("missing_adjusted_close")
            if pd.isna(vol):
                flags.append("missing_volume")
            rows.append(
                {
                    "security_id": security_id,
                    "date": pd.Timestamp(date),
                    "open": pd.NA,
                    "high": pd.NA,
                    "low": pd.NA,
                    "close": close,
                    "adjusted_close": adj,
                    "volume": vol,
                    "dividend": pd.NA,
                    "split": pd.NA,
                    "source_id": source_id,
                    "retrieved_at": retrieved,
                    "price_qc_flags": ";".join(flags),
                }
            )
    return pd.DataFrame(rows, columns=PRICE_HISTORY_COLUMNS)


def liquidity_metrics(price_history: pd.DataFrame) -> pd.DataFrame:
    """Derive ADV/liquidity coverage and price sanity flags by security."""
    if price_history.empty:
        return pd.DataFrame(columns=["security_id", "avg_dollar_volume", "valid_trading_days", "price_coverage_pct", "volume_coverage_pct", "price_qc_flags"])
    df = price_history.copy()
    df["dollar_volume"] = pd.to_numeric(df["adjusted_close"], errors="coerce") * pd.to_numeric(df["volume"], errors="coerce")
    rows = []
    total_dates = max(1, int(df["date"].nunique()))
    for security_id, group in df.groupby("security_id"):
        close = pd.to_numeric(group["adjusted_close"], errors="coerce")
        returns = close.pct_change(fill_method=None).abs()
        flags = []
        if (returns > 0.8).any():
            flags.append("extreme_price_move_check_adjustments")
        if group["date"].duplicated().any():
            flags.append("duplicate_price_dates")
        rows.append(
            {
                "security_id": security_id,
                "avg_dollar_volume": float(group["dollar_volume"].dropna().mean()) if group["dollar_volume"].notna().any() else np.nan,
                "valid_trading_days": int(close.notna().sum()),
                "price_coverage_pct": float(close.notna().sum() / total_dates),
                "volume_coverage_pct": float(group["volume"].notna().sum() / total_dates),
                "price_qc_flags": ";".join(flags),
            }
        )
    return pd.DataFrame(rows)


BENCHMARK_MAP_COLUMNS = [
    "security_id",
    "benchmark_id",
    "benchmark_name",
    "benchmark_ticker_or_proxy",
    "benchmark_type",
    "valid_from",
    "valid_to",
    "mapping_confidence",
    "mapping_rationale",
]


def build_benchmark_map(records: pd.DataFrame) -> pd.DataFrame:
    """Normalize benchmark mappings and confidence labels."""
    df = _ensure_columns(records, BENCHMARK_MAP_COLUMNS)
    df["benchmark_type"] = df["benchmark_type"].fillna("missing")
    invalid = ~df["benchmark_type"].isin(BENCHMARK_TYPES)
    df.loc[invalid, "benchmark_type"] = "missing"
    df["mapping_confidence"] = df["mapping_confidence"].fillna(
        df["benchmark_type"].map({"official": "high", "issuer_stated": "medium_high", "proxy": "medium", "inferred": "low", "missing": "none"})
    )
    for col in ["valid_from", "valid_to"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df[BENCHMARK_MAP_COLUMNS].reset_index(drop=True)


def compute_tracking_error_with_mapping(
    etf_returns: pd.Series,
    benchmark_returns: pd.Series | None,
    mapping_row: pd.Series | dict[str, object],
    *,
    periods_per_year: int = 252,
) -> dict[str, object]:
    """Compute tracking error while preserving official/proxy/inferred labeling."""
    benchmark_type = str(mapping_row.get("benchmark_type", "missing"))
    if benchmark_returns is None or benchmark_type == "missing":
        return {"tracking_error": np.nan, "benchmark_type": benchmark_type, "fallback_level": "missing", "tracking_error_label": "missing"}
    value = tracking_error(etf_returns, benchmark_returns, periods_per_year=periods_per_year)
    fallback_level = "primary" if benchmark_type in {"official", "issuer_stated"} else "proxy"
    label = "official" if benchmark_type == "official" else benchmark_type
    return {"tracking_error": value, "benchmark_type": benchmark_type, "fallback_level": fallback_level, "tracking_error_label": label}


def is_pit_eligible(
    *,
    measurement_date: str | pd.Timestamp | None,
    public_available_date: str | pd.Timestamp | None,
    decision_date: str | pd.Timestamp,
    qc_flags: str | Iterable[str] | None = None,
) -> bool:
    """Return whether a feature is safe for a decision date under PIT controls."""
    decision = pd.Timestamp(decision_date)
    measurement = pd.Timestamp(measurement_date) if measurement_date is not None and not pd.isna(measurement_date) else None
    available = pd.Timestamp(public_available_date) if public_available_date is not None and not pd.isna(public_available_date) else None
    if measurement is not None and measurement > decision:
        return False
    if available is None or available > decision:
        return False
    flags = ";".join(qc_flags) if isinstance(qc_flags, (list, tuple, set)) else str(qc_flags or "")
    return "invalid" not in flags.lower()


def build_electre_features_pit(
    feature_values: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp,
    rebalance_date: str | pd.Timestamp | None = None,
    source_id: str = "derived_feature",
    source_date: str | pd.Timestamp | None = None,
    public_available_date: str | pd.Timestamp | None = None,
    fallback_level: FallbackLevel = "primary",
    confidence: str = "medium",
) -> pd.DataFrame:
    """Convert wide feature values into traceable PIT feature rows."""
    rows: list[dict[str, object]] = []
    for security_id, values in feature_values.iterrows():
        for criterion, value in values.items():
            available = public_available_date if public_available_date is not None else source_date
            qc_flags = "" if is_pit_eligible(
                measurement_date=source_date,
                public_available_date=available,
                decision_date=decision_date,
            ) else "post_date_data_excluded"
            rows.append(
                {
                    "security_id": security_id,
                    "decision_date": pd.Timestamp(decision_date),
                    "rebalance_date": pd.Timestamp(rebalance_date or decision_date),
                    "criterion": criterion,
                    "value": value if not qc_flags else np.nan,
                    "source_id": source_id,
                    "source_date": pd.Timestamp(source_date) if source_date is not None else pd.NaT,
                    "public_available_date": pd.Timestamp(available) if available is not None else pd.NaT,
                    "fallback_level": fallback_level,
                    "confidence": confidence,
                    "qc_flags": qc_flags,
                }
            )
    return pd.DataFrame(rows)


def criteria_coverage_from_pit_features(
    features_pit: pd.DataFrame,
    required: Iterable[str],
) -> pd.DataFrame:
    """Coverage report over long PIT feature rows with proxy/missing states."""
    rows: list[dict[str, object]] = []
    total_assets = int(features_pit["security_id"].nunique()) if not features_pit.empty else 0
    for criterion in required:
        subset = features_pit.loc[features_pit["criterion"].astype(str) == criterion] if not features_pit.empty else pd.DataFrame()
        non_null = int(subset["value"].notna().sum()) if "value" in subset else 0
        fallback_levels = sorted(set(subset.get("fallback_level", pd.Series(dtype=str)).dropna().astype(str))) if not subset.empty else []
        if non_null == 0:
            status = "missing"
        elif any(level in {"proxy", "secondary"} for level in fallback_levels):
            status = "proxy"
        elif total_assets and non_null >= total_assets:
            status = "complete"
        else:
            status = "partial"
        rows.append(
            {
                "criterion": criterion,
                "non_null_count": non_null,
                "coverage_pct": float(non_null / total_assets) if total_assets else 0.0,
                "fallback_levels": ";".join(fallback_levels),
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def regulatory_data_quality_verdict(
    *,
    universe_mode: str,
    criteria_coverage_table: pd.DataFrame,
    pit_controls_passed: bool,
    survivorship_bias_free: bool = False,
    identifier_ambiguities: int = 0,
    benchmark_mapping_quality: str = "partial",
    pre_2019_coverage_complete: bool = False,
) -> dict[str, object]:
    """Classify allowed claims for regulatory-enriched public ETF data."""
    statuses = criteria_coverage_table.set_index("criterion")["status"].astype(str).to_dict() if not criteria_coverage_table.empty and "criterion" in criteria_coverage_table else {}
    missing = [criterion for criterion, status in statuses.items() if status not in {"complete", "proxy"}]
    normalized = universe_mode.lower()
    if "static_current" in normalized:
        verdict = "pilot_static_current_not_primary"
    elif "regulatory" in normalized and pit_controls_passed and not missing and identifier_ambiguities == 0:
        verdict = "thesis_aligned_public_regulatory_pit"
    elif "2015" in normalized and not pre_2019_coverage_complete:
        verdict = "extended_robustness_public_data_limited"
    elif "regulatory" in normalized:
        verdict = "partial_regulatory_alignment"
    else:
        verdict = "public_point_in_time_pilot"
    prohibited = [
        "fully point-in-time",
        "institutional survivorship-bias-free",
        "complete US ETF universe",
        "official tracking error for all ETFs",
        "guaranteed benchmark outperformance",
    ]
    allowed = (
        "Public/regulatory enriched ETF evidence with approximate PIT controls; disclose public-data limitations."
        if verdict == "thesis_aligned_public_regulatory_pit"
        else "Partial or robustness evidence; disclose gaps before thesis-grade claims."
    )
    return {
        "verdict": verdict,
        "universe_mode": universe_mode,
        "criteria_complete_or_proxy": not missing,
        "missing_or_partial_criteria": missing,
        "pit_controls_passed": bool(pit_controls_passed),
        "survivorship_bias_free": bool(survivorship_bias_free),
        "identifier_ambiguities": int(identifier_ambiguities),
        "benchmark_mapping_quality": benchmark_mapping_quality,
        "allowed_claims": allowed,
        "prohibited_claims": prohibited,
        "public_data_limitations": [
            "Public sources do not prove complete institutional survivorship-bias-free coverage.",
            "Benchmark and expense data may be proxy or issuer-derived when regulatory fields are incomplete.",
        ],
    }


def permitted_claims_for_verdict(verdict: dict[str, object]) -> list[str]:
    """Return human-readable claims that match the data-quality verdict."""
    if verdict.get("verdict") == "thesis_aligned_public_regulatory_pit":
        return [
            "Universo ETF público/regulatorio enriquecido.",
            "Control point-in-time aproximado mediante fechas de disponibilidad.",
            "Evaluación empírica contra benchmarks tradicionales.",
        ]
    return [
        "Evidencia parcial, piloto o de robustez.",
        "No reclamar universo fully point-in-time ni survivor-bias-free institucional.",
    ]


def benchmark_returns_from_price_history(price_history: pd.DataFrame, benchmark_security_id: str) -> pd.Series:
    """Build benchmark returns from normalized price history for a benchmark security."""
    subset = price_history.loc[price_history["security_id"].astype(str) == str(benchmark_security_id)]
    if subset.empty:
        return pd.Series(dtype="float64")
    prices = subset.sort_values("date").set_index("date")["adjusted_close"]
    return returns_from_prices(prices)
