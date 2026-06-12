from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import platform
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, cast

import pandas as pd

from etf_optimizer.backtesting.benchmarks import (
    benchmark_spy,
    benchmark_60_40,
    benchmark_equal_weight_walk_forward,
    benchmark_min_variance_walk_forward,
    benchmark_max_sharpe_walk_forward,
)
from etf_optimizer.backtesting.engine import BacktestConfig
from etf_optimizer.data.eligibility import (
    compute_avg_dollar_volume,
    filter_by_history,
    filter_by_liquidity,
)
from etf_optimizer.data.fetcher import compute_price_coverage, compute_ticker_coverage
from etf_optimizer.data.investable_universe import PublicApproximatePITUniverseProvider
from etf_optimizer.data.sec_universe import (
    PointInTimeETFUniverseProvider,
    build_point_in_time_master,
    download_sec_series_class_snapshot,
    load_sec_series_class_snapshot,
)
from etf_optimizer.features import returns_from_prices
from etf_optimizer.optimization.exposure import category_exposure_table
from etf_optimizer.pipeline import AssignmentName, PipelineConfig, run_research_pipeline
from etf_optimizer.reporting.fold_performance import fold_performance_table
from etf_optimizer.reporting.holdings_attribution import fold_holdings_attribution_table
from etf_optimizer.reporting.methodology_report import MethodologyReportConfig, write_methodology_report
from etf_optimizer.reporting.provenance import MethodologySource, write_provenance_record
from etf_optimizer.reporting.robustness import (
    bootstrap_metric_intervals,
    cost_sensitivity_table,
    electre_sensitivity_table,
)
from etf_optimizer.reporting.statistical_tests import paired_benchmark_tests_table
from etf_optimizer.reporting.tables import (
    build_strategy_comparison,
    build_equity_curves,
    build_drawdowns,
    write_comparison_tables,
)
from etf_optimizer.reporting.plots import plot_equity_curves, coverage_plot_summary
from etf_optimizer.selection.electre_tri import Criterion, Profile, SelectionBackend

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[1]

IMPORTANT_PACKAGES = ("numpy", "pandas", "scipy", "scikit-learn", "yfinance", "pyarrow")
PACKAGE_MANIFEST_KEYS = {"scikit-learn": "sklearn"}
DEFAULT_COST_GRID_BPS = (0.0, 5.0, 10.0, 25.0, 50.0)
DEFAULT_ELECTRE_LAMBDAS = (0.65, 0.75, 0.85)
DEFAULT_ELECTRE_WEIGHT_MULTIPLIERS = (
    {},
    {"cagr": 1.25, "volatility": 0.85},
    {"cagr": 0.85, "volatility": 1.25},
)
MIN_THESIS_FOLDS = 5
MIN_THESIS_OOS_PERIODS = 60
PUBLIC_ACTIVE_UNIVERSE_TYPE = "active_current_public_snapshot"
PUBLIC_POINT_IN_TIME_UNIVERSE_TYPE = "public_sec_series_class_point_in_time"
PUBLIC_APPROXIMATE_PIT_UNIVERSE_TYPE = "public_approximate_pit_universe_master"
INSTITUTIONAL_SURVIVORSHIP_FREE_TYPE = "institutional_survivorship_bias_free"


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_dirty() -> bool | None:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(output.strip())


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package_name in IMPORTANT_PACKAGES:
        manifest_key = PACKAGE_MANIFEST_KEYS.get(package_name, package_name)
        try:
            versions[manifest_key] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            versions[manifest_key] = "not-installed"
    return versions


def _sha256(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raw_input_source(path: Path | None, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(path) if path is not None else None,
        "sha256": _sha256(path),
        "exists": bool(path is not None and path.exists()),
    }


def calculate_fold_diagnostics(
    monthly_prices: pd.DataFrame,
    *,
    train_size: int,
    test_size: int,
    step_size: int,
    min_thesis_folds: int = MIN_THESIS_FOLDS,
    min_thesis_oos_periods: int = MIN_THESIS_OOS_PERIODS,
) -> dict[str, int | bool | str]:
    """Return walk-forward sample-size diagnostics after monthly returns conversion."""
    if min(train_size, test_size, step_size, min_thesis_folds, min_thesis_oos_periods) <= 0:
        raise ValueError("fold diagnostic sizes and thresholds must be positive")
    price_observations = int(len(monthly_prices.sort_index()))
    return_observations = max(price_observations - 1, 0)
    required_for_one_fold = train_size + test_size
    if return_observations < required_for_one_fold:
        folds = 0
        oos_periods = 0
    else:
        test_windows = []
        start = 0
        while start + required_for_one_fold <= return_observations:
            test_start = start + train_size
            test_stop = test_start + test_size
            test_windows.append(range(test_start, test_stop))
            start += step_size
        folds = len(test_windows)
        oos_periods = len({idx for window in test_windows for idx in window})
    thesis_grade = folds >= min_thesis_folds and oos_periods >= min_thesis_oos_periods
    if folds == 0:
        label = "insufficient_oos"
        warning = (
            "No complete walk-forward fold is available after pct_change(); "
            f"return_observations={return_observations}, required={required_for_one_fold}."
        )
    elif not thesis_grade:
        label = "pilot_only_oos"
        warning = (
            "Out-of-sample evidence is pilot-only; thesis-grade inference requires at least "
            f"{min_thesis_folds} folds and {min_thesis_oos_periods} OOS periods."
        )
    else:
        label = "thesis_grade_oos"
        warning = ""
    return {
        "price_observations": price_observations,
        "return_observations": return_observations,
        "train_size": int(train_size),
        "test_size": int(test_size),
        "step_size": int(step_size),
        "required_return_observations_for_one_fold": int(required_for_one_fold),
        "walk_forward_folds": int(folds),
        "oos_periods": int(oos_periods),
        "min_thesis_folds": int(min_thesis_folds),
        "min_thesis_oos_periods": int(min_thesis_oos_periods),
        "thesis_grade_oos": bool(thesis_grade),
        "sufficiency_label": label,
        "warning": warning,
    }


def classify_data_quality(*, price_source: str, universe_type: str) -> dict[str, str | bool]:
    """Classify what academic claims are allowed by the current data source."""
    normalized_price = price_source.lower()
    if "synthetic" in normalized_price:
        return {
            "verdict": "structural_test_only",
            "survivorship_bias_free": False,
            "allowed_claims": "Software smoke test only; do not interpret as market performance evidence.",
        }
    if universe_type == INSTITUTIONAL_SURVIVORSHIP_FREE_TYPE and any(
        source in normalized_price
        for source in ("crsp", "morningstar", "lipper", "bloomberg", "refinitiv", "etfgi")
    ):
        return {
            "verdict": "institutional_thesis_grade",
            "survivorship_bias_free": True,
            "allowed_claims": "Eligible for thesis-grade survivorship-bias-free empirical claims, subject to sufficient out-of-sample folds and statistical tests.",
        }
    if universe_type in {PUBLIC_POINT_IN_TIME_UNIVERSE_TYPE, PUBLIC_APPROXIMATE_PIT_UNIVERSE_TYPE}:
        label = "SEC point-in-time universe" if universe_type == PUBLIC_POINT_IN_TIME_UNIVERSE_TYPE else "Universe Master public-approximate PIT universe"
        return {
            "verdict": "public_point_in_time_pilot",
            "survivorship_bias_free": False,
            "allowed_claims": f"{label} reduces static-universe look-ahead/survivorship bias, but ETF heuristic coverage, snapshot granularity, and public price data remain pilot-only for thesis claims.",
        }
    if universe_type == "regulatory_enriched_pit":
        return {
            "verdict": "thesis_aligned_public_regulatory_pit",
            "survivorship_bias_free": False,
            "allowed_claims": "Public/regulatory enriched ETF evidence with approximate PIT controls; disclose public-data limitations and fallback/proxy usage.",
            "prohibited_claims": [
                "fully point-in-time",
                "institutional survivorship-bias-free",
                "complete US ETF universe",
                "guaranteed benchmark outperformance",
            ],
        }
    return {
        "verdict": "public_data_pilot",
        "survivorship_bias_free": False,
        "allowed_claims": "Preliminary public-data evidence only; do not claim survivorship-bias-free or statistically conclusive performance.",
    }


def write_fold_diagnostics(output_dir: Path, diagnostics: dict[str, int | bool | str]) -> tuple[Path, Path]:
    json_path = output_dir / "fold_diagnostics.json"
    csv_path = output_dir / "fold_diagnostics.csv"
    json_path.write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame([diagnostics]).to_csv(csv_path, index=False)
    return json_path, csv_path


def write_run_manifest(
    output_path: Path,
    *,
    universe_path: Path | None,
    prices_path: Path | None,
    volume_path: Path | None,
    output_dir: Path,
    parameters: dict[str, object],
) -> Path:
    manifest = {
        "git_commit": _git_commit(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "python_version": platform.python_version(),
        "package_versions": _package_versions(),
        "paths": {
            "universe": str(universe_path) if universe_path is not None else None,
            "prices": str(prices_path) if prices_path is not None else None,
            "volume": str(volume_path) if volume_path is not None else None,
            "out": str(output_dir),
        },
        "parameters": parameters,
    }
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def validate_input_paths(prices_path: Path | None, volume_path: Path | None) -> list[str]:
    errors: list[str] = []
    if prices_path is not None and not prices_path.exists():
        errors.append(f"missing prices file: {prices_path}")
    if volume_path is not None and not volume_path.exists():
        errors.append(f"missing volume file: {volume_path}")
    return errors


def validate_cli_args(args: argparse.Namespace) -> list[str]:
    """Validate quantitative CLI inputs before loading data or running experiments."""
    errors: list[str] = []
    universe_mode = getattr(args, "universe_mode", "static_current")
    sec_series_class_years = getattr(args, "sec_series_class_years", [])
    universe_path = Path(args.universe) if args.universe is not None else None
    if universe_mode in {"static_current", "static_start"} and universe_path is None:
        errors.append("--universe is required for static_current/static_start universe modes")
    if universe_path is not None and not universe_path.exists():
        errors.append(f"missing universe file: {universe_path}")
    if universe_mode == "point_in_time" and not sec_series_class_years:
        errors.append("--sec-series-class-years is required for --universe-mode point_in_time")
    if universe_mode == "public_approximate_pit":
        investable_dir = Path(getattr(args, "investable_universe_dir", "data/universe_master/investable_universe/investable_universe_snapshots"))
        if not investable_dir.exists():
            errors.append(f"missing investable universe snapshot directory: {investable_dir}")
    try:
        start = pd.Timestamp(args.start)
        end = pd.Timestamp(args.end)
    except ValueError:
        errors.append("start and end must be parseable dates")
    else:
        if pd.isna(start) or pd.isna(end):
            errors.append("start and end must be valid finite dates")
        elif start > end:
            errors.append("start must be on or before end")
    if not math.isfinite(args.cost_bps) or args.cost_bps < 0.0:
        errors.append("cost_bps must be finite and nonnegative")
    if not math.isfinite(args.min_coverage_pct) or not 0.0 <= args.min_coverage_pct <= 1.0:
        errors.append("min_coverage_pct must be finite and between 0 and 1")
    if not math.isfinite(args.min_avg_dollar_volume) or args.min_avg_dollar_volume < 0.0:
        errors.append("min_avg_dollar_volume must be finite and nonnegative")
    category_change_min_score_improvement = getattr(args, "category_change_min_score_improvement", 0.0)
    if not math.isfinite(category_change_min_score_improvement) or category_change_min_score_improvement < 0.0:
        errors.append("category_change_min_score_improvement must be finite and nonnegative")
    category_exposure_cap = getattr(args, "category_exposure_cap", None)
    if category_exposure_cap is not None and (
        not math.isfinite(category_exposure_cap) or not 0.0 < category_exposure_cap <= 1.0
    ):
        errors.append("category_exposure_cap must be finite and between 0 and 1")
    errors.extend(validate_input_paths(args.prices, args.volume))
    return errors


def _unique_universe_tickers(universe: pd.DataFrame) -> list[str]:
    return list(dict.fromkeys(universe["ticker"].dropna().astype(str).str.upper()))


def _pct_of_requested(count: int, requested: int) -> float:
    return round((count / requested * 100.0), 2) if requested else 0.0


def build_fixed_reference_benchmarks(
    *,
    all_returns: pd.DataFrame,
    eligible_returns: pd.DataFrame,
    reference_returns: pd.DataFrame,
    report_index: pd.Index,
    rebalance_periods: int,
) -> dict[str, pd.Series]:
    """Build fixed reference benchmarks from the full raw return panel.

    Fixed market references such as SPY and 60/40 must remain comparable even when
    SPY or BND does not pass the ELECTRE eligibility funnel. Optimized strategies
    continue to use the eligible universe, but references come from all downloaded
    returns and are aligned to the out-of-sample report index.
    """
    references: dict[str, pd.Series] = {}
    benchmark_source = reference_returns.combine_first(all_returns).combine_first(eligible_returns)
    if "SPY" in benchmark_source.columns:
        references["SPY_buy_hold"] = benchmark_spy(benchmark_source).reindex(report_index)
    if {"SPY", "BND"}.issubset(benchmark_source.columns):
        references["60/40_SPY_BND_fixed_weight"] = benchmark_60_40(
            benchmark_source,
            rebalance_periods=rebalance_periods,
        ).reindex(report_index)
    return references


def fetch_reference_returns(
    tickers: list[str],
    *,
    start: str,
    end: str,
) -> pd.DataFrame:
    """Download monthly adjusted reference benchmark returns when absent from the universe panel."""
    if not tickers:
        return pd.DataFrame()
    try:
        import yfinance as yf

        data = yf.download(
            tickers,
            start=start,
            end=pd.Timestamp(end) + pd.Timedelta(days=1),
            progress=False,
            auto_adjust=False,
            threads=False,
        )
    except Exception as exc:  # pragma: no cover - network/provider failure path
        logger.warning("Could not download fixed reference benchmarks %s: %s", tickers, exc)
        return pd.DataFrame()
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        price_field = "Adj Close" if "Adj Close" in data.columns.get_level_values(0) else "Close"
        prices = data[price_field]
    else:
        prices = data[["Adj Close"]].rename(columns={"Adj Close": tickers[0]}) if "Adj Close" in data else data[["Close"]].rename(columns={"Close": tickers[0]})
    monthly_prices = prices.resample("ME").last()
    return returns_from_prices(monthly_prices)


def build_eligible_universe_outputs(
    universe: pd.DataFrame,
    coverage: pd.DataFrame,
    prices: pd.DataFrame,
    volume: pd.DataFrame | None,
    min_coverage_pct: float,
    min_avg_dollar_volume: float,
    min_first_valid: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Build final eligible-universe and filter-funnel output tables.

    The funnel is cumulative: each later stage is counted among tickers that passed
    the previous stages. Missing values are never filled with zeros; no volume data
    means no ticker can pass the liquidity gate.
    """
    requested_tickers = _unique_universe_tickers(universe)
    requested = len(requested_tickers)

    coverage_by_ticker = coverage.set_index("ticker", drop=False).reindex(requested_tickers)
    for column, default in {
        "ticker": None,
        "downloaded": False,
        "first_valid": None,
        "last_valid": None,
        "n_obs": 0,
        "expected_obs": 0,
        "coverage_pct": 0.0,
        "nan_pct": 1.0,
        "has_sufficient_history": False,
    }.items():
        if column not in coverage_by_ticker.columns:
            coverage_by_ticker[column] = default
    coverage_by_ticker["ticker"] = coverage_by_ticker["ticker"].fillna(pd.Series(requested_tickers, index=requested_tickers))
    coverage_by_ticker["downloaded"] = coverage_by_ticker["downloaded"].fillna(False).astype(bool)
    downloaded_mask = coverage_by_ticker["downloaded"]

    history_mask = filter_by_history(
        coverage_by_ticker,
        min_coverage_pct=min_coverage_pct,
        min_first_valid=min_first_valid,
    ).reindex(requested_tickers, fill_value=False)
    sufficient_history_mask = downloaded_mask & history_mask

    if volume is None:
        avg_dollar_volume = pd.Series(index=prices.columns, dtype="float64", name="avg_dollar_volume")
    else:
        avg_dollar_volume = compute_avg_dollar_volume(prices, volume)
    liquidity_mask = filter_by_liquidity(
        avg_dollar_volume.reindex(requested_tickers),
        min_avg_dollar_volume=min_avg_dollar_volume,
    ).reindex(requested_tickers, fill_value=False)
    liquidity_pass_mask = sufficient_history_mask & liquidity_mask
    final_mask = liquidity_pass_mask

    counts = {
        "requested": requested,
        "downloaded": int(downloaded_mask.sum()),
        "failed": requested - int(downloaded_mask.sum()),
        "sufficient_history": int(sufficient_history_mask.sum()),
        "liquidity_pass": int(liquidity_pass_mask.sum()),
        "final_eligible": int(final_mask.sum()),
    }
    funnel = pd.DataFrame(
        [
            {
                "stage": stage,
                "count": count,
                "pct_of_requested": _pct_of_requested(count, requested),
            }
            for stage, count in [
                ("requested", counts["requested"]),
                ("downloaded", counts["downloaded"]),
                ("sufficient_history", counts["sufficient_history"]),
                ("liquidity_pass", counts["liquidity_pass"]),
                ("final_eligible", counts["final_eligible"]),
            ]
        ]
    )

    final_tickers = set(final_mask[final_mask].index)
    eligible_universe = universe[universe["ticker"].astype(str).str.upper().isin(final_tickers)].copy()
    eligible_universe["ticker"] = eligible_universe["ticker"].astype(str).str.upper()
    eligible_universe = eligible_universe.merge(
        coverage_by_ticker[
            [
                "ticker",
                "downloaded",
                "first_valid",
                "last_valid",
                "n_obs",
                "expected_obs",
                "coverage_pct",
                "nan_pct",
                "has_sufficient_history",
            ]
        ].reset_index(drop=True),
        on="ticker",
        how="left",
    )
    eligible_universe["avg_dollar_volume"] = eligible_universe["ticker"].map(avg_dollar_volume)
    return eligible_universe, funnel, counts


def _sec_series_class_local_path(directory: Path, year: int) -> Path | None:
    candidates = [
        directory / f"investment_company_series_class_{year}.csv",
        directory / f"{year}_raw.csv",
        directory / f"{year}_universe_raw.csv",
        directory / f"{year}.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_point_in_time_provider_from_args(
    args: argparse.Namespace,
) -> tuple[object | None, pd.DataFrame, list[str]]:
    if args.universe_mode == "public_approximate_pit":
        provider = PublicApproximatePITUniverseProvider(args.investable_universe_dir)
        frames = []
        for source in provider.sources:
            frame = provider._read_snapshot(Path(source))
            frame["snapshot_source"] = source
            frames.append(frame)
        master = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["ticker"])
        return provider, master, provider.sources
    if args.universe_mode != "point_in_time":
        return None, pd.DataFrame(), []
    snapshots: list[pd.DataFrame] = []
    sources: list[str] = []
    for year in args.sec_series_class_years:
        local_path = _sec_series_class_local_path(args.sec_series_class_dir, int(year))
        if local_path is not None:
            snapshots.append(load_sec_series_class_snapshot(local_path, int(year)))
            sources.append(str(local_path))
        elif args.download_sec_snapshots:
            snapshots.append(download_sec_series_class_snapshot(int(year)))
            sources.append(f"sec_download:{year}")
        else:
            raise FileNotFoundError(
                f"SEC Series/Class snapshot for {year} was not found in {args.sec_series_class_dir}. "
                "Use --download-sec-snapshots to download it or place a local CSV there."
            )
    master = build_point_in_time_master(snapshots)
    return PointInTimeETFUniverseProvider(master), master, sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sprint experiment: broad universe backtest.")
    parser.add_argument(
        "--universe-mode",
        choices=["static_current", "static_start", "point_in_time", "public_approximate_pit", "regulatory_enriched_pit"],
        default="static_current",
        help="Universe construction mode. regulatory_enriched_pit is the thesis public/regulatory enriched mode with approximate PIT controls.",
    )
    parser.add_argument("--universe", type=Path, default=None, help="Path to static universe CSV")
    parser.add_argument(
        "--sec-series-class-years",
        nargs="*",
        type=int,
        default=[],
        help="SEC Investment Company Series/Class years used for --universe-mode point_in_time, e.g. 2018 2019 2020.",
    )
    parser.add_argument(
        "--sec-series-class-dir",
        type=Path,
        default=Path("data/universe/sec_series_class"),
        help="Directory containing annual SEC Series/Class CSV snapshots.",
    )
    parser.add_argument(
        "--download-sec-snapshots",
        action="store_true",
        help="Download missing SEC Series/Class snapshots instead of requiring local files.",
    )
    parser.add_argument(
        "--investable-universe-dir",
        type=Path,
        default=Path("data/universe_master/investable_universe/investable_universe_snapshots"),
        help="Directory of prebuilt investable snapshots for --universe-mode public_approximate_pit.",
    )
    parser.add_argument(
        "--universe-min-age-months",
        type=int,
        default=0,
        help="Minimum observable ETF age applied by the point-in-time universe provider at each rebalance.",
    )
    parser.add_argument("--prices", type=Path, default=None, help="Path to prices parquet (close)")
    parser.add_argument("--volume", type=Path, default=None, help="Path to volume parquet")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--rebalance", choices=["monthly", "quarterly", "annual"], default="annual")
    parser.add_argument(
        "--weight-drift",
        choices=["constant_mix", "buy_and_hold"],
        default="buy_and_hold",
        help="Portfolio accounting between rebalance dates: constant_mix keeps target weights; buy_and_hold lets weights drift.",
    )
    parser.add_argument(
        "--rebalance-policy",
        choices=["calendar", "threshold"],
        default="calendar",
        help="calendar only rebalances at fold starts; threshold also rebalances intrawindow when drift exceeds tolerance.",
    )
    parser.add_argument(
        "--drift-tolerance",
        type=float,
        default=0.05,
        help="Absolute weight drift tolerance for --rebalance-policy threshold, e.g. 0.03 = 3 percentage points.",
    )
    parser.add_argument(
        "--electre-assignment",
        choices=["pessimistic", "optimistic"],
        default="pessimistic",
        help="ELECTRE-TRI assignment variant from the cited paper.",
    )
    parser.add_argument(
        "--electre-backend",
        choices=["internal", "pydecision_tri_b"],
        default="internal",
        help="ELECTRE implementation backend; pydecision_tri_b uses the general pyDecision MCDA library.",
    )
    parser.add_argument(
        "--disable-veto",
        action="store_true",
        help="Run ELECTRE-TRI without veto thresholds for paper-style variant comparison.",
    )
    parser.add_argument(
        "--compare-electre-variants",
        action="store_true",
        help="Also run pessimistic/optimistic × with/without veto and write methodology_variant_comparison.csv.",
    )
    parser.add_argument(
        "--recategorization-policy",
        choices=["rebalance_only", "every_period"],
        default="rebalance_only",
        help="rebalance_only reclassifies on scheduled folds; every_period re-runs ELECTRE each return period and trades only on category changes/thresholds.",
    )
    parser.add_argument(
        "--turnover-penalty",
        type=float,
        default=0.0,
        help="Blend new every-period target with current weights: 0=no penalty, 1=no trade toward new target.",
    )
    parser.add_argument(
        "--category-confirmation-periods",
        type=int,
        default=1,
        help="Require a new every_period selected set to persist N periods before trading category_change.",
    )
    parser.add_argument(
        "--category-change-min-score-improvement",
        type=float,
        default=0.0,
        help="Minimum current-window ELECTRE credibility improvement required before trading a confirmed category_change.",
    )
    parser.add_argument(
        "--category-exposure-cap",
        type=float,
        default=None,
        help="Optional maximum portfolio exposure per transparent ETF risk bucket, e.g. 0.35.",
    )
    parser.add_argument(
        "--disable-optimizer-fallback",
        action="store_true",
        help="Fail fast if MaxSharpe optimization fails instead of falling back to MinVariance then EqualWeight.",
    )
    parser.add_argument("--cost-bps", type=float, default=10.0, help="Transaction cost in bps")
    parser.add_argument("--out", type=Path, default=Path("results/sprint_universe_v0"))
    parser.add_argument(
        "--min-coverage-pct",
        type=float,
        default=0.80,
        help="Minimum per-ticker observed price coverage required for eligibility",
    )
    parser.add_argument(
        "--min-avg-dollar-volume",
        type=float,
        default=0.0,
        help="Minimum average daily dollar volume required for eligibility",
    )
    args = parser.parse_args()

    input_errors = validate_cli_args(args)
    if input_errors:
        parser.error("; ".join(input_errors))

    rebalance_map = {"monthly": 1, "quarterly": 3, "annual": 12}
    test_size = rebalance_map[args.rebalance]

    point_in_time_provider, point_in_time_master, point_in_time_sources = build_point_in_time_provider_from_args(args)
    if args.universe_mode in {"point_in_time", "public_approximate_pit"}:
        universe = point_in_time_master.copy()
        args.out.mkdir(parents=True, exist_ok=True)
        master_name = "public_approximate_pit_universe_master.csv" if args.universe_mode == "public_approximate_pit" else "point_in_time_universe_master.csv"
        point_in_time_master.to_csv(args.out / master_name, index=False)
        logger.info(
            "%s universe master loaded: %d rows from %d snapshots",
            args.universe_mode,
            len(universe),
            len(point_in_time_sources),
        )
    elif args.universe is not None:
        universe = pd.read_csv(args.universe)
        logger.info("Universe loaded: %d funds", len(universe))
    else:
        parser.error("--universe is required unless --universe-mode point_in_time is used")

    if args.prices:
        raw_prices = pd.read_parquet(args.prices).loc[args.start : args.end]
        raw_volume = pd.read_parquet(args.volume).loc[args.start : args.end] if args.volume else None
        prices = raw_prices.resample("ME").last()
        volume = raw_volume.resample("ME").sum() if raw_volume is not None else None

        all_rets = returns_from_prices(prices)
        rets = all_rets.copy()
        universe_tickers = _unique_universe_tickers(universe)
        coverage = compute_price_coverage(universe_tickers, raw_prices, args.start, args.end)
        if args.universe_mode in {"point_in_time", "public_approximate_pit"}:
            available_tickers = [ticker for ticker in universe_tickers if ticker in rets.columns]
            eligible_universe = universe[universe["ticker"].astype(str).str.upper().isin(available_tickers)].copy()
            filter_counts = {
                "requested": len(universe_tickers),
                "downloaded": len(available_tickers),
                "failed": len(universe_tickers) - len(available_tickers),
                "sufficient_history": len(available_tickers),
                "liquidity_pass": len(available_tickers),
                "final_eligible": len(available_tickers),
            }
            filter_funnel = pd.DataFrame(
                [
                    {"stage": stage, "count": count, "pct_of_requested": _pct_of_requested(count, len(universe_tickers))}
                    for stage, count in filter_counts.items()
                ]
            )
            coverage_by_ticker = compute_ticker_coverage(
                universe_tickers,
                raw_prices,
                args.start,
                args.end,
                min_coverage=0.0,
            )
        else:
            coverage_by_ticker = compute_ticker_coverage(
                universe_tickers,
                raw_prices,
                args.start,
                args.end,
                min_coverage=args.min_coverage_pct,
            )
            eligible_universe, filter_funnel, filter_counts = build_eligible_universe_outputs(
                universe=universe,
                coverage=coverage_by_ticker,
                prices=raw_prices,
                volume=raw_volume,
                min_coverage_pct=args.min_coverage_pct,
                min_avg_dollar_volume=args.min_avg_dollar_volume,
                min_first_valid=args.start,
            )
            available_tickers = [t for t in rets.columns if t in set(eligible_universe["ticker"])]
        rets = rets[available_tickers]
        prices = prices[available_tickers]
        volume = volume[available_tickers] if volume is not None else None

        logger.info("Price coverage:\n%s", coverage.to_string(index=False))
    else:
        idx = pd.date_range(args.start, args.end, freq="ME")
        repeats = (len(idx) // 4) + 1
        synthetic_rets = pd.DataFrame(
            {
                "SPY": ([0.008, -0.004, 0.012, 0.006] * repeats)[: len(idx)],
                "BND": ([0.002, 0.001, -0.001, 0.003] * repeats)[: len(idx)],
                "QQQ": ([0.012, -0.008, 0.018, 0.004] * repeats)[: len(idx)],
                "IWM": ([0.006, -0.006, 0.010, 0.005] * repeats)[: len(idx)],
                "TLT": ([0.004, 0.006, -0.004, 0.002] * repeats)[: len(idx)],
            },
            index=idx,
        )
        prices = (1.0 + synthetic_rets).cumprod() * 100.0
        volume = pd.DataFrame(1_000_000, index=idx, columns=prices.columns)
        rets = returns_from_prices(prices)
        all_rets = rets.copy()
        available_tickers = list(rets.columns)
        coverage = pd.DataFrame()
        coverage_by_ticker = pd.DataFrame(
            {
                "ticker": available_tickers,
                "downloaded": True,
                "first_valid": [idx.min().strftime("%Y-%m-%d")] * len(available_tickers),
                "last_valid": [idx.max().strftime("%Y-%m-%d")] * len(available_tickers),
                "n_obs": [len(idx)] * len(available_tickers),
                "expected_obs": [len(idx)] * len(available_tickers),
                "coverage_pct": [1.0] * len(available_tickers),
                "nan_pct": [0.0] * len(available_tickers),
                "has_sufficient_history": True,
            }
        )
        synthetic_universe = pd.DataFrame({"ticker": available_tickers})
        eligible_universe, filter_funnel, filter_counts = build_eligible_universe_outputs(
            universe=synthetic_universe,
            coverage=coverage_by_ticker,
            prices=prices,
            volume=volume,
            min_coverage_pct=args.min_coverage_pct,
            min_avg_dollar_volume=args.min_avg_dollar_volume,
        )
        logger.info("No price file provided; using synthetic prices for structural test.")

    logger.info("Eligible universe: %d tickers with price data", len(available_tickers))
    logger.info(
        "Filter counts: requested=%d, downloaded=%d, failed=%d, "
        "sufficient_history=%d, liquidity_pass=%d, final_eligible=%d",
        filter_counts["requested"],
        filter_counts["downloaded"],
        filter_counts["failed"],
        filter_counts["sufficient_history"],
        filter_counts["liquidity_pass"],
        filter_counts["final_eligible"],
    )

    train_months = 36
    args.out.mkdir(parents=True, exist_ok=True)
    price_source = "yfinance" if args.prices else "synthetic structural test data"
    if args.universe_mode == "point_in_time":
        universe_type = PUBLIC_POINT_IN_TIME_UNIVERSE_TYPE
    elif args.universe_mode == "public_approximate_pit":
        universe_type = PUBLIC_APPROXIMATE_PIT_UNIVERSE_TYPE
    else:
        universe_type = PUBLIC_ACTIVE_UNIVERSE_TYPE
    fold_diagnostics = calculate_fold_diagnostics(
        prices,
        train_size=train_months,
        test_size=test_size,
        step_size=test_size,
    )
    fold_json_path, fold_csv_path = write_fold_diagnostics(args.out, fold_diagnostics)
    data_quality = classify_data_quality(price_source=price_source, universe_type=universe_type)
    data_quality_path = args.out / "data_quality_verdict.json"
    data_quality_path.write_text(json.dumps(data_quality, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if fold_diagnostics["warning"]:
        logger.warning("OOS sufficiency: %s", fold_diagnostics["warning"])
    logger.info(
        "Data quality verdict: %s — %s",
        data_quality["verdict"],
        data_quality["allowed_claims"],
    )
    if args.universe_mode in {"point_in_time", "public_approximate_pit"}:
        universe_parameters = {
            "universe_mode": args.universe_mode,
            "sec_series_class_years": args.sec_series_class_years,
            "sec_series_class_sources": point_in_time_sources if args.universe_mode == "point_in_time" else [],
            "investable_universe_dir": str(args.investable_universe_dir) if args.universe_mode == "public_approximate_pit" else None,
            "investable_universe_sources": point_in_time_sources if args.universe_mode == "public_approximate_pit" else [],
            "universe_min_age_months": args.universe_min_age_months,
        }
    else:
        universe_parameters = {}
    manifest_path = write_run_manifest(
        args.out / "run_manifest.json",
        universe_path=args.universe,
        prices_path=args.prices,
        volume_path=args.volume,
        output_dir=args.out,
        parameters={
            **universe_parameters,
            "start": args.start,
            "end": args.end,
            "rebalance": args.rebalance,
            "cost_bps": args.cost_bps,
            "min_coverage_pct": args.min_coverage_pct,
            "min_avg_dollar_volume": args.min_avg_dollar_volume,
            "train_size": train_months,
            "test_size": test_size,
            "step_size": test_size,
            "weight_drift": args.weight_drift,
            "rebalance_policy": args.rebalance_policy,
            "drift_tolerance": args.drift_tolerance,
            "electre_assignment": args.electre_assignment,
            "electre_use_veto": not args.disable_veto,
            "electre_backend": args.electre_backend,
            "optimizer_fallback": not args.disable_optimizer_fallback,
            "recategorization_policy": args.recategorization_policy,
            "turnover_penalty": args.turnover_penalty,
            "category_confirmation_periods": args.category_confirmation_periods,
            "category_change_min_score_improvement": args.category_change_min_score_improvement,
            "category_exposure_cap": args.category_exposure_cap,
        },
    )
    eligible_universe.to_csv(args.out / "eligible_universe.csv", index=False)
    filter_funnel.to_csv(args.out / "filter_funnel.csv", index=False)

    criteria = [
        Criterion("cagr", weight=0.35, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("volatility", weight=0.25, preference_direction="min", q=0.0, p=0.02, v=0.10),
        Criterion("sharpe", weight=0.25, preference_direction="max", q=0.0, p=0.10, v=0.30),
        Criterion("sortino", weight=0.15, preference_direction="max", q=0.0, p=0.10, v=0.30),
    ]
    profiles = [
        Profile("minimum", {"cagr": 0.03, "volatility": 0.25, "sharpe": 0.3, "sortino": 0.4}),
        Profile("preferred", {"cagr": 0.10, "volatility": 0.18, "sharpe": 0.8, "sortino": 1.0}),
    ]

    pipe_config = PipelineConfig(
        criteria=criteria,
        profiles=profiles,
        strategy="max_sharpe",
        train_size=train_months,
        test_size=test_size,
        step_size=test_size,
        cost_bps=args.cost_bps,
        periods_per_year=12,
        electre_assignment=args.electre_assignment,
        electre_use_veto=not args.disable_veto,
        electre_backend=args.electre_backend,
        weight_drift=args.weight_drift,
        rebalance_policy=args.rebalance_policy,
        drift_tolerance=args.drift_tolerance,
        optimizer_fallback=not args.disable_optimizer_fallback,
        recategorization_policy=args.recategorization_policy,
        turnover_penalty=args.turnover_penalty,
        category_confirmation_periods=args.category_confirmation_periods,
        category_change_min_score_improvement=args.category_change_min_score_improvement,
        asset_metadata=eligible_universe,
        category_exposure_cap=args.category_exposure_cap,
        universe_provider=point_in_time_provider,
        universe_min_age_months=args.universe_min_age_months,
        universe_min_coverage_pct=args.min_coverage_pct if args.universe_mode in {"point_in_time", "public_approximate_pit"} else None,
        universe_min_avg_dollar_volume=args.min_avg_dollar_volume if args.universe_mode in {"point_in_time", "public_approximate_pit"} else None,
        fold_artifacts_dir=args.out / "fold_stage_artifacts",
    )

    pipe_result = run_research_pipeline(
        prices,
        volume,
        pipe_config,
    )
    logger.info("ELECTRE selected %d assets", len(pipe_result.selected_assets))

    variant_comparison_path = args.out / "methodology_variant_comparison.csv"
    variant_rows: list[pd.DataFrame] = []
    if args.compare_electre_variants:
        for assignment in [cast(AssignmentName, "pessimistic"), cast(AssignmentName, "optimistic")]:
            for use_veto in [True, False]:
                for backend in [cast(SelectionBackend, "internal"), cast(SelectionBackend, "pydecision_tri_b")]:
                    variant_config = PipelineConfig(
                        criteria=criteria,
                        profiles=profiles,
                        strategy="max_sharpe",
                        train_size=train_months,
                        test_size=test_size,
                        step_size=test_size,
                        cost_bps=args.cost_bps,
                        periods_per_year=12,
                        electre_assignment=assignment,
                        electre_use_veto=use_veto,
                        electre_backend=backend,
                        weight_drift=args.weight_drift,
                        rebalance_policy=args.rebalance_policy,
                        drift_tolerance=args.drift_tolerance,
                        optimizer_fallback=not args.disable_optimizer_fallback,
                        recategorization_policy=args.recategorization_policy,
                        turnover_penalty=args.turnover_penalty,
                        category_confirmation_periods=args.category_confirmation_periods,
                        category_change_min_score_improvement=args.category_change_min_score_improvement,
                        asset_metadata=eligible_universe,
                        category_exposure_cap=args.category_exposure_cap,
                        universe_provider=point_in_time_provider,
                        universe_min_age_months=args.universe_min_age_months,
                        universe_min_coverage_pct=args.min_coverage_pct if args.universe_mode in {"point_in_time", "public_approximate_pit"} else None,
                        universe_min_avg_dollar_volume=args.min_avg_dollar_volume if args.universe_mode in {"point_in_time", "public_approximate_pit"} else None,
                    )
                    variant_result = run_research_pipeline(prices, volume, variant_config)
                    row = variant_result.summary.copy()
                    row.insert(
                        0,
                        "methodology_mode",
                        f"{backend}_{assignment}_{'with_veto' if use_veto else 'without_veto'}",
                    )
                    row.insert(1, "electre_assignment", assignment)
                    row.insert(2, "electre_use_veto", use_veto)
                    row.insert(3, "electre_backend", backend)
                    row.insert(4, "weight_drift", args.weight_drift)
                    row.insert(5, "rebalance_policy", args.rebalance_policy)
                    row.insert(6, "drift_tolerance", args.drift_tolerance)
                    row.insert(7, "optimizer_fallback", not args.disable_optimizer_fallback)
                    row.insert(8, "recategorization_policy", args.recategorization_policy)
                    row.insert(9, "turnover_penalty", args.turnover_penalty)
                    row.insert(10, "category_confirmation_periods", args.category_confirmation_periods)
                    row.insert(11, "category_change_min_score_improvement", args.category_change_min_score_improvement)
                    row.insert(12, "category_exposure_cap", args.category_exposure_cap)
                    variant_rows.append(row.reset_index(drop=True))
        pd.concat(variant_rows, ignore_index=True).to_csv(variant_comparison_path, index=False)
        logger.info("Methodology variant comparison written to %s", variant_comparison_path)

    electre_equal_result = run_research_pipeline(prices, volume, replace(pipe_config, strategy="equal_weight", fold_artifacts_dir=None))
    electre_minvar_result = run_research_pipeline(prices, volume, replace(pipe_config, strategy="min_variance", fold_artifacts_dir=None))
    strategy_returns: dict[str, pd.Series] = {
        "ELECTRE_EqualWeight_walk_forward": electre_equal_result.backtest.portfolio_returns,
        "ELECTRE_MinVariance_walk_forward": electre_minvar_result.backtest.portfolio_returns,
        "ELECTRE_MaxSharpe_walk_forward": pipe_result.backtest.portfolio_returns,
    }
    report_index = pipe_result.backtest.portfolio_returns.index

    missing_reference_tickers = [ticker for ticker in ["SPY", "BND"] if ticker not in all_rets.columns]
    reference_rets = fetch_reference_returns(missing_reference_tickers, start=args.start, end=args.end)
    fixed_references = build_fixed_reference_benchmarks(
        all_returns=all_rets,
        eligible_returns=rets,
        reference_returns=reference_rets,
        report_index=report_index,
        rebalance_periods=test_size,
    )
    strategy_returns.update(fixed_references)
    benchmark_available_tickers = [ticker for ticker in available_tickers if ticker in rets.columns and not rets[ticker].isna().any()]
    if len(benchmark_available_tickers) >= 3:
        benchmark_config = BacktestConfig(
            train_size=train_months,
            test_size=test_size,
            step_size=test_size,
            cost_bps=args.cost_bps,
            weight_drift=args.weight_drift,
            rebalance_policy=args.rebalance_policy,
            drift_tolerance=args.drift_tolerance,
        )
        benchmark_returns = rets[benchmark_available_tickers]
        strategy_returns["Universe_EqualWeight_walk_forward"] = benchmark_equal_weight_walk_forward(
            benchmark_returns,
            benchmark_config,
        ).portfolio_returns
        strategy_returns["MinVariance_walk_forward"] = benchmark_min_variance_walk_forward(
            benchmark_returns,
            benchmark_config,
            periods_per_year=12,
        ).portfolio_returns
        strategy_returns["MaxSharpe_walk_forward"] = benchmark_max_sharpe_walk_forward(
            benchmark_returns,
            benchmark_config,
            periods_per_year=12,
        ).portfolio_returns

    comparison = build_strategy_comparison(strategy_returns, periods_per_year=12)
    equity = build_equity_curves(strategy_returns)
    drawdowns = build_drawdowns(strategy_returns)
    fold_performance = fold_performance_table(strategy_returns, test_size=test_size, periods_per_year=12)
    fold_performance_path = args.out / "fold_performance.csv"
    fold_performance.to_csv(fold_performance_path, index=False)
    fold_holdings_attribution = fold_holdings_attribution_table(
        rets,
        pipe_result.backtest.effective_weights,
        test_size=test_size,
        metadata=eligible_universe,
    )
    fold_holdings_attribution_path = args.out / "fold_holdings_attribution.csv"
    fold_holdings_attribution.to_csv(fold_holdings_attribution_path, index=False)
    category_exposure = category_exposure_table(pipe_result.backtest.effective_weights, eligible_universe)
    category_exposure_path = args.out / "category_exposure_report.csv"
    category_exposure.to_csv(category_exposure_path, index=False)

    paths = write_comparison_tables(comparison, equity, drawdowns, args.out)
    cost_sensitivity = cost_sensitivity_table(
        pipe_result.backtest.portfolio_returns,
        pipe_result.backtest.turnover,
        base_cost_bps=args.cost_bps,
        cost_bps_grid=DEFAULT_COST_GRID_BPS,
        periods_per_year=12,
    )
    cost_sensitivity_path = args.out / "cost_sensitivity.csv"
    cost_sensitivity.to_csv(cost_sensitivity_path, index=False)
    bootstrap_intervals = bootstrap_metric_intervals(
        pipe_result.backtest.portfolio_returns,
        n_bootstrap=1_000,
        random_state=20260518,
        periods_per_year=12,
    )
    bootstrap_path = args.out / "bootstrap_metric_intervals.csv"
    bootstrap_intervals.to_csv(bootstrap_path, index=False)
    paired_benchmark_tests = paired_benchmark_tests_table(
        pipe_result.backtest.portfolio_returns,
        {name: series for name, series in strategy_returns.items() if name != "ELECTRE_MaxSharpe_walk_forward"},
        n_bootstrap=1_000,
        random_state=20260519,
        periods_per_year=12,
        min_observations=6,
    )
    paired_benchmark_tests_path = args.out / "paired_benchmark_tests.csv"
    paired_benchmark_tests.to_csv(paired_benchmark_tests_path, index=False)
    electre_sensitivity = electre_sensitivity_table(
        pipe_result.features,
        criteria,
        profiles,
        lambda_values=DEFAULT_ELECTRE_LAMBDAS,
        weight_multipliers=DEFAULT_ELECTRE_WEIGHT_MULTIPLIERS,
    )
    electre_sensitivity_path = args.out / "electre_sensitivity.csv"
    electre_sensitivity.to_csv(electre_sensitivity_path, index=False)
    pipe_result.features.to_csv(args.out / "features_table.csv")
    pipe_result.selection.to_csv(args.out / "electre_selection.csv")
    pipe_result.selection_by_rebalance.to_csv(args.out / "electre_selection_by_rebalance.csv", index=False)
    pipe_result.backtest.weights.to_csv(args.out / "electre_weights.csv")
    pipe_result.backtest.effective_weights.to_csv(args.out / "electre_effective_weights.csv")
    pipe_result.backtest.rebalance_events.to_csv(args.out / "rebalance_events.csv")
    methodology_path = write_methodology_report(
        args.out / "methodology_report.md",
        MethodologyReportConfig(
            universe_path=args.universe
            or (args.out / ("public_approximate_pit_universe_master.csv" if args.universe_mode == "public_approximate_pit" else "point_in_time_universe_master.csv")),
            prices_path=args.prices,
            volume_path=args.volume,
            start=args.start,
            end=args.end,
            rebalance=args.rebalance,
            train_size=train_months,
            test_size=test_size,
            step_size=test_size,
            cost_bps=args.cost_bps,
            min_coverage_pct=args.min_coverage_pct,
            min_avg_dollar_volume=args.min_avg_dollar_volume,
            price_source=price_source,
            universe_snapshot_date=(
                "Universe Master investable public-approximate PIT snapshots"
                if args.universe_mode == "public_approximate_pit"
                else (
                    "SEC Series/Class annual point-in-time snapshots"
                    if args.universe_mode == "point_in_time"
                    else "current Nasdaq active ETF snapshot"
                )
            ),
            fold_diagnostics=fold_diagnostics,
            data_quality=data_quality,
        ),
        universe=universe,
        filter_funnel=filter_funnel,
        criteria=criteria,
        profiles=profiles,
    )
    if not coverage.empty:
        coverage.to_csv(args.out / "coverage_report.csv", index=False)
    provenance_path = write_provenance_record(
        args.out / "provenance.json",
        code_paths=[
            REPO_ROOT / "scripts/run_sprint_experiment.py",
            REPO_ROOT / "src/etf_optimizer/pipeline.py",
            REPO_ROOT / "src/etf_optimizer/selection/electre_tri.py",
            REPO_ROOT / "src/etf_optimizer/backtesting/engine.py",
            REPO_ROOT / "src/etf_optimizer/optimization/exposure.py",
            REPO_ROOT / "src/etf_optimizer/reporting/fold_performance.py",
            REPO_ROOT / "src/etf_optimizer/reporting/holdings_attribution.py",
            REPO_ROOT / "src/etf_optimizer/reporting/robustness.py",
            REPO_ROOT / "src/etf_optimizer/reporting/statistical_tests.py",
        ],
        data_sources=[
            {
                "name": "Nasdaq ETF Screener",
                "type": "active_current_universe_snapshot",
                "url": "https://api.nasdaq.com/api/screener/etf?download=true",
                "license_or_access": "public endpoint; verify terms before redistribution",
                "survivorship_bias_free": False,
                "role": "broad active ETF candidate universe",
            },
            {
                "name": "SEC EDGAR company tickers/submissions",
                "type": "legal_identifier_enrichment",
                "url": "https://www.sec.gov/files/company_tickers.json",
                "license_or_access": "public SEC data",
                "survivorship_bias_free": False,
                "role": "CIK/exchange corroboration for public universe v0",
            },
            {
                "name": "Yahoo Finance via yfinance" if args.prices else "Synthetic structural test data",
                "type": "historical_ohlcv" if args.prices else "deterministic_test_fixture",
                "url": "https://pypi.org/project/yfinance/" if args.prices else None,
                "license_or_access": "public API; not guaranteed for redistribution" if args.prices else "generated locally",
                "survivorship_bias_free": False if args.prices else None,
                "role": "daily price and volume source" if args.prices else "pipeline smoke-test data",
            },
            {
                "name": "Local raw input files",
                "type": "file_hashes",
                "role": "reproducibility audit for exact local inputs",
                "inputs": [
                    _raw_input_source(args.universe, "universe_csv"),
                    _raw_input_source(args.prices, "close_prices_parquet"),
                    _raw_input_source(args.volume, "volume_parquet"),
                ],
            },
        ],
        methodology_sources=[
            MethodologySource(
                name="ELECTRE Tri",
                citation="Roy-style outranking method for multicriteria sorting; implemented as transparent ELECTRE Tri classification with concordance, discordance, and credibility traces.",
                role="ETF acceptability filtering before portfolio optimization",
            ),
            MethodologySource(
                name="Walk-forward backtesting",
                citation="Out-of-sample rolling train/test validation to avoid look-ahead bias.",
                role="Performance evaluation protocol",
            ),
            MethodologySource(
                name="Ledoit-Wolf covariance shrinkage",
                citation="Ledoit and Wolf covariance shrinkage estimator as exposed by scikit-learn.",
                role="Covariance estimation for optimized portfolios when observations permit",
            ),
        ],
        generated_artifacts=[
            *paths.values(),
            fold_performance_path,
            fold_holdings_attribution_path,
            category_exposure_path,
            args.out / "features_table.csv",
            args.out / "electre_selection.csv",
            args.out / "electre_selection_by_rebalance.csv",
            args.out / "electre_weights.csv",
            args.out / "electre_effective_weights.csv",
            args.out / "rebalance_events.csv",
            cost_sensitivity_path,
            bootstrap_path,
            paired_benchmark_tests_path,
            electre_sensitivity_path,
            methodology_path,
            manifest_path,
            args.out / "coverage_report.csv",
            fold_json_path,
            fold_csv_path,
            data_quality_path,
        ],
        limitations=[
            "The public Nasdaq universe is active-current and is not survivorship-bias-free.",
            "SEC EDGAR enrichment corroborates identifiers but is not yet a complete ETF-only historical membership database.",
            "Yahoo Finance/yfinance coverage for delisted ETFs is incomplete; final thesis claims require CRSP, Morningstar, Lipper, Bloomberg, Refinitiv, or equivalent institutional data for full survivorship-bias-free inference.",
            "Robustness artifacts are sensitivity diagnostics; final conclusions should cite the full parameter grid and confidence intervals.",
        ],
        run_metadata={
            "command": " ".join(sys.argv),
            "git_commit": _git_commit(),
            "git_dirty": _git_dirty(),
            "timezone": datetime.now().astimezone().tzname(),
            "bootstrap_random_state": 20260518,
            "package_versions": _package_versions(),
        },
        data_quality=data_quality,
    )
    logger.info("Results written to %s", args.out)
    logger.info("  run_manifest: %s", manifest_path)
    logger.info("  methodology_report: %s", methodology_path)
    logger.info("  provenance: %s", provenance_path)
    logger.info("  cost_sensitivity: %s", cost_sensitivity_path)
    logger.info("  bootstrap_metric_intervals: %s", bootstrap_path)
    logger.info("  paired_benchmark_tests: %s", paired_benchmark_tests_path)
    logger.info("  fold_performance: %s", fold_performance_path)
    logger.info("  fold_holdings_attribution: %s", fold_holdings_attribution_path)
    logger.info("  category_exposure_report: %s", category_exposure_path)
    logger.info("  electre_sensitivity: %s", electre_sensitivity_path)
    logger.info("  fold_diagnostics: %s", fold_json_path)
    logger.info("  data_quality_verdict: %s", data_quality_path)

    for name, p in paths.items():
        logger.info("  %s: %s", name, p)

    summary_text = plot_equity_curves(equity, "Sprint Universe v0 — Equity Curves")
    logger.info("Equity curve summary:\n%s", summary_text)

    if not coverage.empty:
        cov_summary = coverage_plot_summary(coverage)
        logger.info("Coverage summary:\n%s", cov_summary)


if __name__ == "__main__":
    main()
