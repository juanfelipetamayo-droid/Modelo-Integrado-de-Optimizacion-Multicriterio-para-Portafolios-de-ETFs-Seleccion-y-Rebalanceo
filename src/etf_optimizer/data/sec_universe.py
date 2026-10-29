from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from etf_optimizer.data.schema import CANONICAL_COLUMNS, make_fund_id, normalize_tickers

SEC_USER_AGENT = "portfolio-etf-optimizer/0.1.0 (research project; contact: juan.tamayo@email.com)"
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
ETF_NAME_KEYWORDS = (" ETF", "EXCHANGE TRADED", " ETF ", "TRUST")


def _canonicalize(df: pd.DataFrame, source_url: str) -> pd.DataFrame:
    df = normalize_tickers(df)
    df["source"] = "sec"
    df["source_url"] = source_url
    df["active_flag"] = True
    df["fund_id"] = df.apply(make_fund_id, axis=1)
    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
    mask = df["ticker"].notna() & (df["ticker"] != "")
    return df.loc[mask, CANONICAL_COLUMNS].reset_index(drop=True)


def load_sec_company_tickers(
    url: str = SEC_COMPANY_TICKERS_URL,
    user_agent: str = SEC_USER_AGENT,
    timeout: int = 30,
) -> pd.DataFrame:
    """Load SEC company tickers from EDGAR's official JSON endpoint.

    This endpoint is a legal/citable crosswalk for CIK, ticker and registrant name.
    It is **not** an ETF universe by itself; use it to enrich or corroborate a universe
    assembled from ETF-specific sources.
    """
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        records = [
            {
                "cik": str(entry.get("cik_str", "")).zfill(10),
                "ticker": str(entry.get("ticker", "")).strip().upper(),
                "name": entry.get("title", ""),
            }
            for entry in data.values()
            if isinstance(entry, dict)
        ]
        return _canonicalize(pd.DataFrame(records), url)
    except (requests.RequestException, ValueError, KeyError, AttributeError):
        return pd.DataFrame(columns=CANONICAL_COLUMNS)


def _parse_sec_exchange_json(data: object) -> list[dict[str, object]]:
    """Parse SEC company_tickers_exchange JSON in either documented or row-dict shape."""
    if isinstance(data, dict) and "fields" in data and "data" in data:
        fields = [str(field) for field in data["fields"]]
        return [dict(zip(fields, row, strict=False)) for row in data["data"] if isinstance(row, (list, tuple))]
    if isinstance(data, list):
        return [entry for entry in data if isinstance(entry, dict)]
    if isinstance(data, dict):
        return [entry for entry in data.values() if isinstance(entry, dict)]
    return []


def load_sec_company_tickers_exchange(
    url: str = SEC_COMPANY_TICKERS_EXCHANGE_URL,
    user_agent: str = SEC_USER_AGENT,
    timeout: int = 30,
) -> pd.DataFrame:
    """Load SEC company tickers with exchange info from EDGAR."""
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        records = []
        for entry in _parse_sec_exchange_json(data):
            records.append(
                {
                    "cik": str(entry.get("cik", entry.get("cik_str", ""))).zfill(10),
                    "ticker": str(entry.get("ticker", "")).strip().upper(),
                    "name": entry.get("name", entry.get("title", "")),
                    "exchange": entry.get("exchange", ""),
                }
            )
        return _canonicalize(pd.DataFrame(records), url)
    except (requests.RequestException, ValueError, KeyError, AttributeError):
        return pd.DataFrame(columns=CANONICAL_COLUMNS)


def filter_likely_etf_entities(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort SEC-name filter for ETF-like registrants.

    This is deliberately conservative and should not be treated as a survivor-bias-free
    ETF universe. Its role is legal corroboration/enrichment, not primary universe selection.
    """
    if df.empty or "name" not in df.columns:
        return df.copy()
    names = df["name"].fillna("").str.upper()
    mask = names.str.contains("ETF|EXCHANGE TRADED|ISHARES|SPDR|VANGUARD.*INDEX|INVESCO.*TRUST", regex=True)
    return df.loc[mask].reset_index(drop=True)


def _sec_series_class_url(year: int) -> str:
    return (
        "https://www.sec.gov/files/investment/data/other/"
        "investment-company-series-and-class-information/"
        f"investment_company_series_class_{year}.csv"
    )


def _is_likely_sec_etf_row(row: pd.Series) -> bool:
    text = " ".join(
        str(row.get(col, ""))
        for col in ["entity_name", "series_name", "class_name", "name"]
        if pd.notna(row.get(col, None))
    ).upper()
    include = (
        " ETF" in f" {text} "
        or "EXCHANGE TRADED" in text
        or "EXCHANGE-TRADED" in text
        or "ISHARES" in text
        or "SPDR" in text
        or "VANGUARD" in text
        or "INVESCO" in text
    )
    exclude = any(term in text for term in ["MUTUAL FUND", "MONEY MARKET", "VARIABLE ANNUITY"])
    return include and not exclude


def load_sec_series_class_snapshot(path_or_url: str | Path, year: int) -> pd.DataFrame:
    """Load one SEC Investment Company Series/Class annual snapshot.

    The SEC file is not ETF-only. This loader keeps a conservative ETF candidate subset,
    normalizes identifiers, and annotates the observation window for point-in-time use.
    """
    raw = pd.read_csv(path_or_url)
    header_aliases = {
        "Reporting File Number",
        "rep_file_num",
        "CIK",
        "CIK Number",
        "entity_name",
        "Entity Name",
        "Name of Registrant",
    }
    if not (set(map(str, raw.columns)) & header_aliases):
        header_row = None
        for idx, row in raw.head(5).iterrows():
            values = {str(value).strip() for value in row.tolist() if pd.notna(value)}
            if values & header_aliases:
                header_row = int(idx)
                break
        if header_row is not None:
            seek = getattr(path_or_url, "seek", None)
            if callable(seek):
                seek(0)
            df = pd.read_csv(path_or_url, skiprows=header_row + 1)
            df.columns = [str(value).strip() for value in raw.iloc[header_row].tolist()[: len(df.columns)]]
        else:
            df = raw
    else:
        df = raw
    rename_map = {
        "CIK": "cik",
        "CIK Number": "cik",
        "class_ticker_symbol": "ticker",
        "Class Ticker": "ticker",
        "series_id": "series_id",
        "Series ID": "series_id",
        "class_id": "class_id",
        "Class ID": "class_id",
        "series_name": "series_name",
        "Series Name": "series_name",
        "class_name": "class_name",
        "Class Name": "class_name",
        "entity_name": "entity_name",
        "Entity Name": "entity_name",
        "Name of Registrant": "entity_name",
        "Registrant Name": "entity_name",
        "Reporting File Number": "reporting_file_number",
        "rep_file_num": "reporting_file_number",
    }
    df = df.rename(columns={old: new for old, new in rename_map.items() if old in df.columns})
    if "ticker" not in df.columns:
        return pd.DataFrame(columns=[*CANONICAL_COLUMNS, "source_year", "first_seen_date", "last_seen_date", "is_etf_candidate", "etf_confidence"])

    df = df.copy()
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df = df.loc[df["ticker"].notna() & (df["ticker"] != "") & (df["ticker"] != "NAN")]
    df["is_etf_candidate"] = df.apply(_is_likely_sec_etf_row, axis=1)
    df = df.loc[df["is_etf_candidate"]].copy()
    if df.empty:
        return pd.DataFrame(columns=[*CANONICAL_COLUMNS, "source_year", "first_seen_date", "last_seen_date", "is_etf_candidate", "etf_confidence"])

    if "cik" in df.columns:
        df["cik"] = df["cik"].apply(lambda value: str(value).split(".")[0].zfill(10) if pd.notna(value) else None)
    df["name"] = df.get("series_name", df.get("entity_name", pd.Series(index=df.index, dtype=object))).combine_first(
        df.get("class_name", pd.Series(index=df.index, dtype=object))
    )
    df["source"] = "sec"
    df["source_url"] = str(path_or_url)
    df["source_year"] = int(year)
    df["first_seen_date"] = pd.Timestamp(year=year, month=1, day=1)
    df["last_seen_date"] = pd.Timestamp(year=year, month=12, day=31)
    df["active_flag"] = True
    df["etf_confidence"] = "heuristic_name_match"
    df = normalize_tickers(df)
    df["fund_id"] = df.apply(make_fund_id, axis=1)
    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
    out_cols = [*CANONICAL_COLUMNS, "source_year", "first_seen_date", "last_seen_date", "is_etf_candidate", "etf_confidence"]
    return df[out_cols].drop_duplicates("fund_id").sort_values("ticker").reset_index(drop=True)


def download_sec_series_class_snapshot(year: int, timeout: int = 60, user_agent: str = SEC_USER_AGENT) -> pd.DataFrame:
    """Download and parse a SEC Series/Class annual snapshot for a given year."""
    url = _sec_series_class_url(year)
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    from io import StringIO

    return load_sec_series_class_snapshot(StringIO(response.text), year=year)


def build_point_in_time_master(snapshots: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge annual snapshots into one point-in-time master table.

    Rows are collapsed by fund_id/ticker while preserving first/last observation dates so
    new ETFs enter only after they are historically observable and disappeared ETFs leave.
    """
    if not snapshots:
        return pd.DataFrame(columns=[*CANONICAL_COLUMNS, "first_seen_date", "last_seen_date", "source_year", "is_etf_candidate", "etf_confidence"])
    frames = []
    for snapshot in snapshots:
        if snapshot.empty:
            continue
        frame = normalize_tickers(snapshot.copy())
        if "fund_id" not in frame.columns:
            frame["fund_id"] = frame.apply(make_fund_id, axis=1)
        for col in ["first_seen_date", "last_seen_date", "inception_date", "termination_date"]:
            if col in frame.columns:
                frame[col] = pd.to_datetime(frame[col], errors="coerce")
        if "is_etf_candidate" not in frame.columns:
            frame["is_etf_candidate"] = True
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=[*CANONICAL_COLUMNS, "first_seen_date", "last_seen_date", "source_year", "is_etf_candidate", "etf_confidence"])
    combined = pd.concat(frames, ignore_index=True)
    for col in [*CANONICAL_COLUMNS, "first_seen_date", "last_seen_date", "source_year", "is_etf_candidate", "etf_confidence"]:
        if col not in combined.columns:
            combined[col] = None

    rows: list[dict[str, object]] = []
    for _fund_id, group in combined.groupby("fund_id", dropna=False, sort=False):
        group = group.sort_values("first_seen_date")
        base = group.iloc[-1].to_dict()
        base["first_seen_date"] = group["first_seen_date"].min()
        base["last_seen_date"] = group["last_seen_date"].max()
        if "inception_date" in group.columns and group["inception_date"].notna().any():
            base["inception_date"] = group["inception_date"].dropna().min()
        if "termination_date" in group.columns and group["termination_date"].notna().any():
            base["termination_date"] = group["termination_date"].dropna().min()
        base["source_year"] = ",".join(str(int(y)) for y in sorted(group["source_year"].dropna().unique())) if "source_year" in group else None
        base["is_etf_candidate"] = bool(group["is_etf_candidate"].fillna(False).any())
        rows.append(base)
    out = pd.DataFrame(rows)
    return out.sort_values("ticker").reset_index(drop=True)


class PointInTimeETFUniverseProvider:
    """ETF universe provider that answers membership as-of a historical date."""

    def __init__(self, master: pd.DataFrame):
        self.master = master.copy()
        for col in ["first_seen_date", "last_seen_date", "inception_date", "termination_date"]:
            if col in self.master.columns:
                self.master[col] = pd.to_datetime(self.master[col], errors="coerce")
        if "is_etf_candidate" not in self.master.columns:
            self.master["is_etf_candidate"] = True

    def constituents_as_of(
        self,
        date: str | pd.Timestamp,
        *,
        min_age_months: int = 0,
        min_coverage_pct: float | None = None,
        min_avg_dollar_volume: float | None = None,
        prices: pd.DataFrame | None = None,
        volume: pd.DataFrame | None = None,
        lookback_periods: int | None = None,
    ) -> pd.DataFrame:
        as_of = pd.Timestamp(date)
        df = self.master.copy()
        if df.empty:
            return df
        first_seen = pd.to_datetime(df.get("first_seen_date"), errors="coerce")
        last_seen = pd.to_datetime(df.get("last_seen_date"), errors="coerce")
        inception = pd.to_datetime(df.get("inception_date"), errors="coerce")
        termination = pd.to_datetime(df.get("termination_date"), errors="coerce")
        effective_start = pd.concat([first_seen, inception], axis=1).max(axis=1)
        mask = df["is_etf_candidate"].fillna(True).astype(bool)
        mask &= first_seen.isna() | (first_seen <= as_of)
        mask &= last_seen.isna() | (last_seen >= as_of)
        mask &= inception.isna() | (inception <= as_of)
        mask &= termination.isna() | (termination > as_of)
        if min_age_months > 0:
            min_start = as_of - pd.DateOffset(months=min_age_months)
            mask &= effective_start <= min_start
        eligible = df.loc[mask].copy()
        if eligible.empty:
            return eligible.sort_values("ticker").reset_index(drop=True)
        eligible = self._apply_market_data_filters(
            eligible,
            as_of=as_of,
            min_coverage_pct=min_coverage_pct,
            min_avg_dollar_volume=min_avg_dollar_volume,
            prices=prices,
            volume=volume,
            lookback_periods=lookback_periods,
        )
        return eligible.sort_values("ticker").reset_index(drop=True)

    def _apply_market_data_filters(
        self,
        eligible: pd.DataFrame,
        *,
        as_of: pd.Timestamp,
        min_coverage_pct: float | None,
        min_avg_dollar_volume: float | None,
        prices: pd.DataFrame | None,
        volume: pd.DataFrame | None,
        lookback_periods: int | None,
    ) -> pd.DataFrame:
        if prices is None or (min_coverage_pct is None and min_avg_dollar_volume is None):
            return eligible
        tickers = [ticker for ticker in eligible["ticker"].astype(str) if ticker in prices.columns]
        if not tickers:
            return eligible.iloc[0:0].copy()
        price_window = prices.loc[prices.index <= as_of, tickers]
        if lookback_periods is not None:
            price_window = price_window.tail(lookback_periods)
        coverage = price_window.notna().mean()
        eligible = eligible.set_index("ticker", drop=False)
        eligible["price_coverage_pct"] = coverage.reindex(eligible.index)
        mask = eligible["price_coverage_pct"].fillna(0.0) >= (min_coverage_pct if min_coverage_pct is not None else 0.0)
        if min_avg_dollar_volume is not None:
            if volume is None:
                mask &= False
            else:
                volume_window = volume.loc[volume.index <= as_of, [ticker for ticker in tickers if ticker in volume.columns]]
                if lookback_periods is not None:
                    volume_window = volume_window.tail(lookback_periods)
                dollar_volume = (price_window * volume_window.reindex_like(price_window)).mean()
                eligible["avg_dollar_volume"] = dollar_volume.reindex(eligible.index)
                mask &= eligible["avg_dollar_volume"].fillna(0.0) >= min_avg_dollar_volume
        return eligible.loc[mask].reset_index(drop=True)
