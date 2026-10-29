from __future__ import annotations


import pandas as pd

CANONICAL_COLUMNS: list[str] = [
    "fund_id",
    "ticker",
    "name",
    "cik",
    "series_id",
    "class_id",
    "exchange",
    "sponsor",
    "asset_class",
    "category",
    "inception_date",
    "termination_date",
    "source",
    "source_url",
    "active_flag",
    "expense_ratio",
    "aum",
    "benchmark",
]

REQUIRED_COLUMNS: list[str] = ["fund_id", "ticker", "source", "active_flag"]

KNOWN_SOURCES: list[str] = ["sec", "nasdaq", "vettafi", "manual"]


def validate_universe_schema(df: pd.DataFrame) -> dict[str, list[str]]:
    """Validate a universe DataFrame against the canonical schema.

    Returns a dict with keys 'missing_required', 'missing_optional',
    'invalid_sources', 'empty_required', 'duplicate_fund_ids', and 'errors'.
    """
    issues: dict[str, list[str]] = {
        "missing_required": [],
        "missing_optional": [],
        "invalid_sources": [],
        "empty_required": [],
        "duplicate_fund_ids": [],
        "errors": [],
    }

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            issues["missing_required"].append(col)

    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            issues["missing_optional"].append(col)

    if "source" in df.columns:
        bad = df.loc[~df["source"].isin(KNOWN_SOURCES), "source"].dropna().unique().tolist()
        if bad:
            issues["invalid_sources"].extend(str(b) for b in bad)

    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            empty = df.index[df[col].isna()].tolist()
            if empty:
                issues["empty_required"].append(f"{col}: {len(empty)} rows")

    if "fund_id" in df.columns:
        dups = df["fund_id"][df["fund_id"].duplicated()].unique().tolist()
        if dups:
            issues["duplicate_fund_ids"].extend(str(d) for d in dups)

    return issues


def normalize_ticker(ticker: str) -> str:
    return str(ticker).strip().upper()


def normalize_tickers(df: pd.DataFrame) -> pd.DataFrame:
    if "ticker" in df.columns:
        df = df.copy()
        df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    return df


def convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["inception_date", "termination_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def make_fund_id(row: pd.Series) -> str:
    tid = str(row.get("ticker", "")).strip().upper()
    cik = str(row.get("cik", "")).strip()
    if tid and tid != "NAN" and tid != "":
        return tid
    if cik and cik != "nan" and cik != "":
        return f"CIK_{cik}"
    return f"unknown_{hash(tuple(row))}"
