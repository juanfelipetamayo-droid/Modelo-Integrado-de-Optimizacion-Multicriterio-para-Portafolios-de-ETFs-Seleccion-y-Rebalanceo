from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import pandas as pd

from etf_optimizer.data.universe_master import MASTER_COLUMNS, _normalize_date_columns

TRADABLE_EXCHANGES = {
    "NYSE",
    "NYSE ARCA",
    "NASDAQ",
    "NASDAQ GM",
    "NASDAQ GS",
    "NASDAQ CM",
    "CBOE",
    "BATS",
    "CBOE BZX",
}


@dataclass(frozen=True)
class InvestableUniverseConfig:
    is_etf_or_etmf: bool = True
    exclude_mutual_funds: bool = True
    exclude_closed_end_funds: bool = True
    exclude_etns: bool = True
    exclude_leveraged: bool = True
    exclude_inverse: bool = True
    min_price: float = 5.0
    min_history_months: int = 24
    min_avg_dollar_volume: float | None = None
    max_missing_returns: float = 0.20
    tradable_exchange_only: bool = True
    lookback_periods: int | None = None
    tradable_exchanges: tuple[str, ...] = tuple(sorted(TRADABLE_EXCHANGES))


@dataclass(frozen=True)
class UniverseEligibilityReportResult:
    output_dir: Path
    summary_path: Path
    exclusions_by_reason_path: Path
    exclusion_detail_path: Path
    observed_snapshot_paths: list[Path]
    investable_snapshot_paths: list[Path]


class PublicApproximatePITUniverseProvider:
    """Point-in-time provider backed by prebuilt investable universe snapshots.

    Snapshots are treated as the source of truth for public-approximate PIT
    investability. For an arbitrary rebalance date the latest snapshot at or
    before the date is used, which supports quarterly/monthly backtests from
    annual or monthly Universe Master exports without looking ahead.
    """

    _SNAPSHOT_RE = re.compile(r"(\d{4})_(\d{2})(?:_(\d{2}))?\.csv$")

    def __init__(self, snapshot_dir: str | Path):
        self.snapshot_dir = Path(snapshot_dir)
        self._snapshot_paths = self._discover_snapshots(self.snapshot_dir)
        if not self._snapshot_paths:
            raise FileNotFoundError(f"no investable universe snapshots found in {self.snapshot_dir}")

    @classmethod
    def _discover_snapshots(cls, snapshot_dir: Path) -> dict[pd.Timestamp, Path]:
        snapshots: dict[pd.Timestamp, Path] = {}
        for path in sorted(snapshot_dir.glob("*.csv")):
            match = cls._SNAPSHOT_RE.search(path.name)
            if match is None:
                continue
            year, month, day = match.groups()
            snapshots[pd.Timestamp(year=int(year), month=int(month), day=int(day or 1))] = path
        return snapshots

    @property
    def available_snapshot_dates(self) -> list[pd.Timestamp]:
        return sorted(self._snapshot_paths)

    @property
    def sources(self) -> list[str]:
        return [str(self._snapshot_paths[date]) for date in self.available_snapshot_dates]

    @staticmethod
    def _read_snapshot(path: Path) -> pd.DataFrame:
        try:
            return pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=["ticker"])

    def snapshot_as_of(self, date: str | pd.Timestamp) -> tuple[pd.Timestamp, pd.DataFrame]:
        as_of = pd.Timestamp(date)
        usable_dates = [snapshot_date for snapshot_date in self.available_snapshot_dates if snapshot_date <= as_of]
        if not usable_dates:
            return as_of, pd.DataFrame(columns=["ticker"])
        snapshot_date = usable_dates[-1]
        snapshot = self._read_snapshot(self._snapshot_paths[snapshot_date])
        if "ticker" in snapshot.columns:
            snapshot["ticker"] = snapshot["ticker"].dropna().astype(str).str.upper()
            snapshot = snapshot.loc[snapshot["ticker"].notna() & (snapshot["ticker"] != "")].copy()
        snapshot["snapshot_date_used"] = snapshot_date.date().isoformat()
        snapshot["rebalance_date"] = as_of.date().isoformat()
        return snapshot_date, snapshot.reset_index(drop=True)

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
        _snapshot_date, eligible = self.snapshot_as_of(date)
        if eligible.empty or "ticker" not in eligible.columns:
            return eligible
        as_of = pd.Timestamp(date)
        mask = pd.Series(True, index=eligible.index)
        if min_age_months > 0:
            start_col = None
            for candidate in ["inception_date", "ticker_start_date", "source_available_date"]:
                if candidate in eligible.columns:
                    start_col = candidate
                    break
            if start_col is not None:
                starts = pd.to_datetime(eligible[start_col], errors="coerce")
                mask &= starts.isna() | (starts <= as_of - pd.DateOffset(months=min_age_months))
        tickers = eligible["ticker"].astype(str).str.upper().tolist()
        if prices is not None and (min_coverage_pct is not None or min_avg_dollar_volume is not None):
            available = [ticker for ticker in tickers if ticker in prices.columns]
            price_window = prices.loc[prices.index <= as_of, available]
            if lookback_periods is not None:
                price_window = price_window.tail(lookback_periods)
            coverage = price_window.notna().mean() if not price_window.empty else pd.Series(dtype="float64")
            eligible["price_coverage_pct"] = eligible["ticker"].map(coverage).astype(float)
            if min_coverage_pct is not None:
                mask &= eligible["price_coverage_pct"].fillna(0.0) >= min_coverage_pct
            if min_avg_dollar_volume is not None:
                if volume is None or price_window.empty:
                    eligible["avg_dollar_volume"] = pd.NA
                    mask &= False
                else:
                    volume_window = volume.loc[volume.index <= as_of, [ticker for ticker in available if ticker in volume.columns]]
                    if lookback_periods is not None:
                        volume_window = volume_window.tail(lookback_periods)
                    dollar_volume = (price_window * volume_window.reindex_like(price_window)).mean()
                    eligible["avg_dollar_volume"] = eligible["ticker"].map(dollar_volume)
                    mask &= eligible["avg_dollar_volume"].fillna(0.0) >= min_avg_dollar_volume
        return eligible.loc[mask].sort_values("ticker").reset_index(drop=True)


def _text(row: pd.Series) -> str:
    cols = ["fund_name", "product_type", "asset_class_bucket", "ticker"]
    return " ".join(str(row.get(col, "") or "") for col in cols).upper()


def _boolish(row: pd.Series, col: str, default: bool = False) -> bool:
    if col not in row or pd.isna(row[col]):
        return default
    value = row[col]
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _is_etf_or_etmf(row: pd.Series) -> bool:
    if "is_etf_or_etmf" in row and pd.notna(row["is_etf_or_etmf"]):
        return _boolish(row, "is_etf_or_etmf")
    text = _text(row)
    return ("ETF" in text or "ETMF" in text or "EXCHANGE TRADED FUND" in text) and "ETN" not in text


def _is_mutual_fund(row: pd.Series) -> bool:
    return _boolish(row, "is_mutual_fund") or "MUTUAL FUND" in _text(row)


def _is_closed_end_fund(row: pd.Series) -> bool:
    text = _text(row)
    return _boolish(row, "is_closed_end_fund") or "CLOSED-END" in text or "CLOSED END" in text


def _is_etn(row: pd.Series) -> bool:
    return _boolish(row, "is_etn") or "ETN" in _text(row) or "EXCHANGE TRADED NOTE" in _text(row)


def _is_leveraged(row: pd.Series) -> bool:
    text = _text(row)
    leveraged_terms = ["LEVERAGED", "ULTRA", " 2X", " 3X", "2X ", "3X ", "DAILY 2", "DAILY 3"]
    return _boolish(row, "is_leveraged") or any(term in text for term in leveraged_terms)


def _is_inverse(row: pd.Series) -> bool:
    text = _text(row)
    inverse_terms = ["INVERSE", "SHORT", "BEAR", "-1X", "-2X", "-3X"]
    return _boolish(row, "is_inverse") or any(term in text for term in inverse_terms)


def _tradable_exchange(row: pd.Series, config: InvestableUniverseConfig) -> bool:
    exchange = str(row.get("exchange", "") or "").upper().strip()
    if not exchange:
        return False
    allowed = {item.upper() for item in config.tradable_exchanges}
    return exchange in allowed


def observed_universe_as_of(listings_by_date: pd.DataFrame, rebalance_date: str | pd.Timestamp) -> pd.DataFrame:
    """Return instruments observable as of t, before investability filters.

    This layer applies only PIT visibility/listing availability rules. It may
    contain mutual funds, CEFs, ETNs, leveraged products or illiquid listings;
    those are removed by ``investable_universe_as_of``.
    """

    as_of = pd.Timestamp(rebalance_date)
    df = _normalize_date_columns(listings_by_date)
    if df.empty:
        cols = ["rebalance_date", "universe_layer", *[col for col in MASTER_COLUMNS if col in listings_by_date.columns]]
        return pd.DataFrame(columns=cols)
    if "fund_id" in df.columns:
        history_group_key = "fund_id"
    else:
        history_group_key = "ticker"
    if "ticker_start_date" in df.columns:
        first_observed_map = pd.to_datetime(df["ticker_start_date"], errors="coerce").groupby(df[history_group_key]).min()
    elif "source_available_date" in df.columns:
        first_observed_map = pd.to_datetime(df["source_available_date"], errors="coerce").groupby(df[history_group_key]).min()
    else:
        first_observed_map = pd.Series(dtype="datetime64[ns]")
    mask = df["source_available_date"].notna() & (df["source_available_date"] <= as_of)
    for start_col in ["observation_start_date", "ticker_start_date"]:
        if start_col in df.columns:
            mask &= df[start_col].isna() | (df[start_col] <= as_of)
    for end_col in ["observation_end_date", "ticker_end_date"]:
        if end_col in df.columns:
            mask &= df[end_col].isna() | (df[end_col] >= as_of)
    for dead_col in ["termination_date", "delisted_date"]:
        if dead_col in df.columns:
            mask &= df[dead_col].isna() | (df[dead_col] > as_of)
    observed = df.loc[mask].copy()
    if observed.empty:
        return observed
    if "fund_id" in observed.columns:
        group_key = "fund_id"
    else:
        group_key = "ticker"
    observed["first_observed_date"] = observed[group_key].map(first_observed_map)
    if "fund_id" in observed.columns:
        observed = observed.sort_values(["ticker", "source_available_date"]).drop_duplicates("fund_id", keep="last")
    observed.insert(0, "universe_layer", "observed")
    observed.insert(0, "rebalance_date", as_of.date().isoformat())
    return observed.sort_values("ticker").reset_index(drop=True)


def _empty_metrics() -> dict[str, object]:
    return {
        "rebalance_price": pd.NA,
        "return_missing_pct": pd.NA,
        "avg_dollar_volume": pd.NA,
    }


def _market_metrics_for_tickers(
    tickers: Iterable[str],
    as_of: pd.Timestamp,
    *,
    prices: pd.DataFrame | None,
    volume: pd.DataFrame | None,
    lookback_periods: int | None,
) -> dict[str, dict[str, object]]:
    unique_tickers = sorted(set(str(ticker) for ticker in tickers))
    metrics = {ticker: _empty_metrics() for ticker in unique_tickers}
    if prices is None or not unique_tickers:
        return metrics
    available = [ticker for ticker in unique_tickers if ticker in prices.columns]
    if not available:
        return metrics
    price_window = prices.loc[prices.index <= as_of, available]
    if lookback_periods is not None:
        price_window = price_window.tail(lookback_periods)
    if price_window.empty:
        return metrics
    last_prices = price_window.ffill().iloc[-1]
    returns = price_window.pct_change(fill_method=None)
    missing_returns = returns.iloc[1:].isna().mean() if len(returns) > 1 else pd.Series(pd.NA, index=available)
    avg_dollar_volume = pd.Series(pd.NA, index=available, dtype="object")
    if volume is not None:
        volume_available = [ticker for ticker in available if ticker in volume.columns]
        if volume_available:
            volume_window = volume.loc[volume.index <= as_of, volume_available]
            if lookback_periods is not None:
                volume_window = volume_window.tail(lookback_periods)
            aligned_prices = price_window[volume_available].reindex_like(volume_window)
            avg_dollar_volume = (aligned_prices * volume_window).mean()
    for ticker in available:
        ticker_metrics = metrics[ticker]
        if pd.notna(last_prices.get(ticker)):
            ticker_metrics["rebalance_price"] = float(last_prices[ticker])
        if pd.notna(missing_returns.get(ticker)):
            ticker_metrics["return_missing_pct"] = float(missing_returns[ticker])
        if ticker in avg_dollar_volume.index and pd.notna(avg_dollar_volume.get(ticker)):
            ticker_metrics["avg_dollar_volume"] = float(avg_dollar_volume[ticker])
    return metrics


def _exclusion_reasons(
    row: pd.Series,
    as_of: pd.Timestamp,
    config: InvestableUniverseConfig,
    *,
    metrics_by_ticker: dict[str, dict[str, object]],
) -> tuple[list[str], dict[str, object]]:
    reasons: list[str] = []
    if config.is_etf_or_etmf and not _is_etf_or_etmf(row):
        reasons.append("not_etf_or_etmf")
    if config.exclude_mutual_funds and _is_mutual_fund(row):
        reasons.append("mutual_fund")
    if config.exclude_closed_end_funds and _is_closed_end_fund(row):
        reasons.append("closed_end_fund")
    if config.exclude_etns and _is_etn(row):
        reasons.append("etn")
    if config.exclude_leveraged and _is_leveraged(row):
        reasons.append("leveraged")
    if config.exclude_inverse and _is_inverse(row):
        reasons.append("inverse")
    if config.tradable_exchange_only and not _tradable_exchange(row, config):
        reasons.append("non_tradable_exchange")

    start_candidates = []
    for col in ["inception_date", "ticker_start_date", "first_observed_date"]:
        if col in row and pd.notna(row[col]):
            start_candidates.append(pd.Timestamp(row[col]))
    if config.min_history_months > 0:
        effective_start = min(start_candidates) if start_candidates else pd.NaT
        min_start = as_of - pd.DateOffset(months=config.min_history_months)
        if pd.isna(effective_start) or effective_start > min_start:
            reasons.append("insufficient_history")

    metrics = metrics_by_ticker.get(str(row.get("ticker")), _empty_metrics())
    price = metrics["rebalance_price"]
    if pd.isna(price):
        reasons.append("missing_price")
    elif float(price) < config.min_price:
        reasons.append("price_below_min")

    missing_returns = metrics["return_missing_pct"]
    if pd.isna(missing_returns):
        reasons.append("missing_returns_unavailable")
    elif float(missing_returns) > config.max_missing_returns:
        reasons.append("missing_returns_above_max")

    adv = metrics["avg_dollar_volume"]
    if config.min_avg_dollar_volume is not None:
        if pd.isna(adv):
            reasons.append("avg_dollar_volume_unavailable")
        elif float(adv) < config.min_avg_dollar_volume:
            reasons.append("avg_dollar_volume_below_min")
    return reasons, metrics


def investable_universe_as_of(
    observed_universe: pd.DataFrame,
    rebalance_date: str | pd.Timestamp,
    *,
    config: InvestableUniverseConfig | None = None,
    prices: pd.DataFrame | None = None,
    volume: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split an observed PIT universe into investable assets and exclusions."""

    config = config or InvestableUniverseConfig()
    as_of = pd.Timestamp(rebalance_date)
    rows: list[pd.Series] = []
    exclusion_rows: list[dict[str, object]] = []
    market_metrics_by_ticker = _market_metrics_for_tickers(
        observed_universe["ticker"].astype(str) if "ticker" in observed_universe.columns else [],
        as_of,
        prices=prices,
        volume=volume,
        lookback_periods=config.lookback_periods,
    )
    for _, row in observed_universe.iterrows():
        reasons, metrics = _exclusion_reasons(row, as_of, config, metrics_by_ticker=market_metrics_by_ticker)
        enriched = row.copy()
        for metric_name, metric_value in metrics.items():
            enriched[metric_name] = metric_value
        enriched["is_investable"] = not reasons
        enriched["exclusion_reasons"] = ";".join(reasons)
        if reasons:
            exclusion_rows.append(
                {
                    "rebalance_date": as_of.date().isoformat(),
                    "ticker": row.get("ticker"),
                    "fund_id": row.get("fund_id", row.get("ticker")),
                    "exclusion_reasons": ";".join(reasons),
                }
            )
        else:
            rows.append(enriched)
    investable = pd.DataFrame(rows)
    if not investable.empty:
        if "universe_layer" in investable.columns:
            investable["universe_layer"] = "investable"
        else:
            investable.insert(0, "universe_layer", "investable")
        investable = investable.sort_values("ticker").reset_index(drop=True)
    exclusions = pd.DataFrame(exclusion_rows, columns=["rebalance_date", "ticker", "fund_id", "exclusion_reasons"])
    return investable, exclusions


def _reason_counts(exclusions: pd.DataFrame, rebalance_date: pd.Timestamp) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for reasons in exclusions.get("exclusion_reasons", pd.Series(dtype=str)).dropna().astype(str):
        for reason in [item for item in reasons.split(";") if item]:
            rows.append({"rebalance_date": rebalance_date.date().isoformat(), "exclusion_reason": reason})
    if not rows:
        return pd.DataFrame(columns=["rebalance_date", "exclusion_reason", "excluded_count"])
    counts = pd.DataFrame(rows).value_counts(["rebalance_date", "exclusion_reason"]).reset_index(name="excluded_count")
    return counts.sort_values(["rebalance_date", "exclusion_reason"]).reset_index(drop=True)


def build_universe_eligibility_report(
    listings_by_date: pd.DataFrame,
    *,
    rebalance_dates: Iterable[str | pd.Timestamp],
    output_dir: str | Path,
    config: InvestableUniverseConfig | None = None,
    prices: pd.DataFrame | None = None,
    volume: pd.DataFrame | None = None,
) -> UniverseEligibilityReportResult:
    """Write observed/investable snapshots and exclusion diagnostics by date."""

    config = config or InvestableUniverseConfig()
    output_path = Path(output_dir)
    observed_dir = output_path / "observed_universe_snapshots"
    investable_dir = output_path / "investable_universe_snapshots"
    observed_dir.mkdir(parents=True, exist_ok=True)
    investable_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []
    all_reason_counts: list[pd.DataFrame] = []
    all_exclusion_details: list[pd.DataFrame] = []
    observed_paths: list[Path] = []
    investable_paths: list[Path] = []

    for dt in rebalance_dates:
        as_of = pd.Timestamp(dt)
        observed = observed_universe_as_of(listings_by_date, as_of)
        investable, exclusions = investable_universe_as_of(
            observed,
            as_of,
            config=config,
            prices=prices,
            volume=volume,
        )
        reason_counts = _reason_counts(exclusions, as_of)
        reason_dict = {row["exclusion_reason"]: int(row["excluded_count"]) for _, row in reason_counts.iterrows()}
        summary_rows.append(
            {
                "rebalance_date": as_of.date().isoformat(),
                "observed_universe_count": int(len(observed)),
                "investable_universe_count": int(len(investable)),
                "excluded_by_reason": json.dumps(reason_dict, sort_keys=True),
            }
        )
        observed_path = observed_dir / f"observed_universe_{as_of:%Y_%m_%d}.csv"
        investable_path = investable_dir / f"investable_universe_{as_of:%Y_%m_%d}.csv"
        observed.to_csv(observed_path, index=False)
        investable.to_csv(investable_path, index=False)
        observed_paths.append(observed_path)
        investable_paths.append(investable_path)
        all_reason_counts.append(reason_counts)
        all_exclusion_details.append(exclusions)

    summary = pd.DataFrame(summary_rows)
    exclusions_by_reason = (
        pd.concat(all_reason_counts, ignore_index=True)
        if all_reason_counts
        else pd.DataFrame(columns=["rebalance_date", "exclusion_reason", "excluded_count"])
    )
    exclusion_detail = (
        pd.concat(all_exclusion_details, ignore_index=True)
        if all_exclusion_details
        else pd.DataFrame(columns=["rebalance_date", "ticker", "fund_id", "exclusion_reasons"])
    )
    summary_path = output_path / "universe_eligibility_by_date.csv"
    exclusions_by_reason_path = output_path / "universe_exclusions_by_reason.csv"
    exclusion_detail_path = output_path / "universe_exclusion_details.csv"
    summary.to_csv(summary_path, index=False)
    exclusions_by_reason.to_csv(exclusions_by_reason_path, index=False)
    exclusion_detail.to_csv(exclusion_detail_path, index=False)
    return UniverseEligibilityReportResult(
        output_dir=output_path,
        summary_path=summary_path,
        exclusions_by_reason_path=exclusions_by_reason_path,
        exclusion_detail_path=exclusion_detail_path,
        observed_snapshot_paths=observed_paths,
        investable_snapshot_paths=investable_paths,
    )
