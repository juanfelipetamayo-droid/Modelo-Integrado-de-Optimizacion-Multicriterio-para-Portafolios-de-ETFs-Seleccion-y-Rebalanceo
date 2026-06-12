from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from etf_optimizer.backtesting.engine import BacktestConfig, WalkForwardBacktester
from etf_optimizer.backtesting.metrics import performance_summary
from etf_optimizer.reporting.robustness import bootstrap_metric_intervals
from etf_optimizer.reporting.classification_diagnostics import default_electre_criteria, default_electre_profiles
from etf_optimizer.reporting.selection_allocation_ablation import _allocate, _load_fold_maps
from etf_optimizer.reporting.tables import build_strategy_comparison, build_equity_curves, build_drawdowns
from etf_optimizer.selection.flowsort import FlowSort

DEFAULT_FINAL_MODELS = [
    "SPY_buy_hold",
    "60/40_SPY_AGG_fixed_weight",
    "Universe_EqualWeight_walk_forward",
    "Universe_MinVariance_walk_forward",
    "ELECTRE_EqualWeight_walk_forward",
    "ELECTRE_MinVariance_walk_forward",
    "ELECTRE_InverseVol_walk_forward",
    "FlowSort_EqualWeight_walk_forward",
    "FlowSort_MinVariance_walk_forward",
    "FlowSort_InverseVol_walk_forward",
]
DEFAULT_EXPERIMENTAL_MODELS = ["ELECTRE_MaxSharpe_walk_forward"]
REQUIRED_SUBDIRS = ["tables", "figures", "diagnostics", "configs", "logs", "manuscript_outputs"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_config(config_path: Path) -> dict[str, Any]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("thesis final config must be a YAML mapping")
    return data


def _ensure_layout(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {name: output_dir / name for name in REQUIRED_SUBDIRS}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _normalize_strategy_name(strategy: str) -> str:
    mapping = {
        "SPY_buy_hold": "SPY_buy_hold",
        "60/40_SPY_BND_fixed_weight": "60/40_SPY_AGG_fixed_weight",
        "MinVariance_walk_forward": "Universe_MinVariance_walk_forward",
        "MaxSharpe_walk_forward": "Universe_MaxSharpe_walk_forward",
        "ELECTRE_pessimistic_with_veto_InverseVol_walk_forward": "ELECTRE_InverseVol_walk_forward",
        "ELECTRE_pessimistic_with_veto_EqualWeight_walk_forward": "ELECTRE_EqualWeight_walk_forward",
        "ELECTRE_pessimistic_with_veto_MinVariance_walk_forward": "ELECTRE_MinVariance_walk_forward",
        "ELECTRE_pessimistic_with_veto_MaxSharpe_walk_forward": "ELECTRE_MaxSharpe_walk_forward",
    }
    return mapping.get(strategy, strategy)


def _run_subprocess(command: list[str], cwd: Path, log_path: Path) -> None:
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("$ " + " ".join(command) + "\n\n")
        log_file.flush()
        completed = subprocess.run(command, cwd=cwd, text=True, stdout=log_file, stderr=subprocess.STDOUT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}); see {log_path}: {' '.join(command)}")


def _sprint_command(config: dict[str, Any], base_run_dir: Path) -> list[str]:
    period = config.get("period", {})
    rebalance = str(config.get("rebalance", "quarterly"))
    cmd = [
        sys.executable,
        "scripts/run_sprint_experiment.py",
        "--universe-mode",
        str(config.get("universe_mode", "public_approximate_pit")),
        "--start",
        str(period.get("start", "2015-01-01")),
        "--end",
        str(period.get("end", "2025-12-31")),
        "--rebalance",
        rebalance,
        "--cost-bps",
        str(config.get("cost_bps", 10.0)),
        "--weight-drift",
        str(config.get("weight_drift", "buy_and_hold")),
        "--rebalance-policy",
        str(config.get("rebalance_policy", "calendar")),
        "--out",
        str(base_run_dir),
    ]
    for option, key in [
        ("--prices", "prices_path"),
        ("--volume", "volume_path"),
        ("--investable-universe-dir", "investable_universe_dir"),
    ]:
        if config.get(key):
            cmd.extend([option, str(config[key])])
    if config.get("min_coverage_pct") is not None:
        cmd.extend(["--min-coverage-pct", str(config["min_coverage_pct"])])
    if config.get("min_avg_dollar_volume") is not None:
        cmd.extend(["--min-avg-dollar-volume", str(config["min_avg_dollar_volume"])])
    if config.get("category_exposure_cap") is not None:
        cmd.extend(["--category-exposure-cap", str(config["category_exposure_cap"])])
    return cmd


def _ablation_command(config: dict[str, Any], base_run_dir: Path, ablation_dir: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/build_selection_allocation_ablation.py",
        "--prices",
        str(config.get("prices_path", "data/raw/yfinance_pilot_2015_2025/close.parquet")),
        "--baseline-results-dir",
        str(base_run_dir),
        "--out",
        str(ablation_dir),
    ]


def _flowsort_command(config: dict[str, Any], base_run_dir: Path, flowsort_dir: Path, report_path: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/build_flowsort_comparison.py",
        "--results-dir",
        str(base_run_dir),
        "--prices",
        str(config.get("prices_path", "data/raw/yfinance_pilot_2015_2025/close.parquet")),
        "--out",
        str(flowsort_dir),
        "--report",
        str(report_path),
    ]


def _smoke_strategy_returns() -> pd.DataFrame:
    idx = pd.date_range("2020-01-31", periods=72, freq="ME")
    base = pd.Series([0.006, -0.002, 0.009, 0.003] * 18, index=idx)
    data: dict[str, pd.Series] = {}
    for i, name in enumerate(DEFAULT_FINAL_MODELS + DEFAULT_EXPERIMENTAL_MODELS, start=1):
        data[name] = base + (i - 5) * 0.0002
    return pd.DataFrame(data)


def _write_smoke_inputs(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    returns = _smoke_strategy_returns()
    comparison = build_strategy_comparison({col: returns[col] for col in returns.columns}, periods_per_year=12).reset_index()
    equity = build_equity_curves({col: returns[col] for col in returns.columns})
    drawdowns = build_drawdowns({col: returns[col] for col in returns.columns})
    diagnostics = output_dir / "diagnostics" / "base_run"
    diagnostics.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(diagnostics / "strategy_comparison.csv", index=False)
    equity.to_csv(diagnostics / "equity_curves.csv")
    drawdowns.to_csv(diagnostics / "drawdowns.csv")
    return comparison, equity, drawdowns


def _flowsort_strategy_name(allocation: str) -> str:
    return {
        "equal_weight": "FlowSort_EqualWeight_walk_forward",
        "min_variance": "FlowSort_MinVariance_walk_forward",
        "inverse_vol": "FlowSort_InverseVol_walk_forward",
    }[allocation]


def _write_flowsort_allocation_tables(config: dict[str, Any], base_run_dir: Path, output_dir: Path) -> None:
    prices_path = Path(config.get("prices_path", "data/raw/yfinance_pilot_2015_2025/close.parquet"))
    if not prices_path.exists() or not (base_run_dir / "fold_stage_artifacts").exists():
        return
    prices = pd.read_parquet(prices_path).sort_index()
    prices.index = pd.to_datetime(prices.index)
    prices = prices.resample("ME").last()
    returns = prices.pct_change(fill_method=None).dropna(how="all")
    universe_by_date, criteria_by_date = _load_fold_maps(base_run_dir)
    criteria = default_electre_criteria()
    profiles = default_electre_profiles()
    returns_index = returns.index
    test_size = {"monthly": 1, "quarterly": 3, "annual": 12}.get(str(config.get("rebalance", "quarterly")), 3)
    backtester = WalkForwardBacktester(
        BacktestConfig(
            train_size=int(config.get("lookback_months", 36)),
            test_size=test_size,
            step_size=test_size,
            cost_bps=float(config.get("cost_bps", 10.0)),
            weight_drift=str(config.get("weight_drift", "buy_and_hold")),  # type: ignore[arg-type]
            rebalance_policy=str(config.get("rebalance_policy", "calendar")),  # type: ignore[arg-type]
        )
    )
    model = FlowSort(criteria, profiles, preference_function="v_shape", use_net_flow=True)
    strategy_returns: dict[str, pd.Series] = {}
    turnover_rows: list[dict[str, Any]] = []

    def make_strategy(allocation: str):
        def strategy(train_returns: pd.DataFrame) -> pd.Series:
            future_return_dates = returns_index[returns_index > train_returns.index[-1]]
            if future_return_dates.empty:
                raise ValueError("cannot infer rebalance date after training window")
            rebalance_date = pd.Timestamp(future_return_dates[0])
            candidate_tickers = [ticker for ticker in universe_by_date.get(rebalance_date, []) if ticker in train_returns.columns]
            matrix = criteria_by_date[rebalance_date]
            matrix = matrix.loc[[ticker for ticker in matrix.index.astype(str) if ticker in candidate_tickers]]
            assigned = model.assign(matrix)
            selected = [ticker for ticker, row in assigned.iterrows() if str(row["category"]).startswith("above_")]
            if not selected:
                selected = assigned["ranking_flow"].sort_values(ascending=False).head(5).index.astype(str).tolist()
            train_subset = train_returns[[ticker for ticker in selected if ticker in train_returns.columns]].dropna(axis=0, how="any")
            if train_subset.empty or train_subset.shape[1] == 0:
                raise ValueError(f"no FlowSort assets available at {rebalance_date.date()}")
            return _allocate(train_subset, allocation, periods_per_year=12, max_weight=0.25)  # type: ignore[arg-type]

        return strategy

    for allocation in ["equal_weight", "min_variance", "inverse_vol"]:
        name = _flowsort_strategy_name(allocation)
        backtest = backtester.run(returns, make_strategy(allocation))
        strategy_returns[name] = backtest.portfolio_returns
        turnover_rows.append(
            {
                "strategy": name,
                "avg_turnover": float(backtest.turnover.mean()) if not backtest.turnover.empty else None,
                "total_turnover": float(backtest.turnover.sum()) if not backtest.turnover.empty else None,
                "rebalance_events": int(backtest.rebalance_events.shape[0]),
            }
        )
    comparison = build_strategy_comparison(strategy_returns, periods_per_year=12).reset_index()
    comparison = comparison.merge(pd.DataFrame(turnover_rows), on="strategy", how="left")
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(output_dir / "flowsort_allocation_strategy_comparison.csv", index=False)
    pd.DataFrame(strategy_returns).to_csv(output_dir / "flowsort_allocation_strategy_returns.csv")


def _compute_spy_agg_reference(config: dict[str, Any], base: Path) -> pd.DataFrame | None:
    try:
        import yfinance as yf
    except Exception:
        return None
    period = config.get("period", {})
    start = str(period.get("start", "2015-01-01"))
    end = str(period.get("end", "2025-12-31"))
    try:
        downloaded = yf.download(["SPY", "AGG"], start=start, end=end, auto_adjust=True, progress=False, threads=False)
    except Exception:
        return None
    if downloaded.empty:
        return None
    close = downloaded["Close"] if isinstance(downloaded.columns, pd.MultiIndex) else downloaded
    if not {"SPY", "AGG"} <= set(close.columns):
        return None
    monthly = close[["SPY", "AGG"]].resample("ME").last()
    returns = monthly.pct_change(fill_method=None).dropna(how="any")
    equity_path = base / "equity_curves.csv"
    if equity_path.exists():
        base_equity = pd.read_csv(equity_path, index_col=0)
        report_index = pd.to_datetime(base_equity.index)
        returns = returns.reindex(report_index).dropna(how="any")
    if returns.empty:
        return None
    weights = pd.Series({"SPY": 0.6, "AGG": 0.4})
    out = []
    for i, (_date, row) in enumerate(returns.iterrows()):
        if i % 3 == 0:
            weights = pd.Series({"SPY": 0.6, "AGG": 0.4})
        period_return = float((row[weights.index] * weights).sum())
        out.append(period_return)
        weights = weights * (1.0 + row[weights.index]) / (1.0 + period_return)
    series = pd.Series(out, index=returns.index, name="60/40_SPY_AGG_fixed_weight")
    return build_strategy_comparison({"60/40_SPY_AGG_fixed_weight": series}, periods_per_year=12).reset_index()


def _load_final_tables(output_dir: Path, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame | None, pd.DataFrame | None]:
    if config.get("smoke_test"):
        return _write_smoke_inputs(output_dir)

    base = output_dir / "diagnostics" / "base_run"
    ablation = output_dir / "diagnostics" / "selection_allocation_ablation"
    comparison_parts: list[pd.DataFrame] = []
    for path in [
        base / "strategy_comparison.csv",
        ablation / "strategy_comparison.csv",
        output_dir / "diagnostics" / "electre_vs_flowsort" / "flowsort_allocation_strategy_comparison.csv",
    ]:
        if path.exists():
            df = pd.read_csv(path)
            if "index" in df.columns and "strategy" not in df.columns:
                df = df.rename(columns={"index": "strategy"})
            comparison_parts.append(df)
    if not comparison_parts:
        raise FileNotFoundError("no strategy comparison tables found after final thesis run")
    spy_agg = _compute_spy_agg_reference(config, base)
    if spy_agg is not None:
        comparison_parts.append(spy_agg)
    comparison = pd.concat(comparison_parts, ignore_index=True)
    comparison["strategy"] = comparison["strategy"].map(_normalize_strategy_name)
    comparison = comparison.drop_duplicates("strategy", keep="last")

    # FlowSort allocation rows should come from diagnostics/electre_vs_flowsort/flowsort_allocation_strategy_comparison.csv.
    # If missing, keep explicit rows with NaN metrics so the report fails visibly instead of silently omitting a required model.
    for strategy in ["FlowSort_EqualWeight_walk_forward", "FlowSort_MinVariance_walk_forward", "FlowSort_InverseVol_walk_forward"]:
        if strategy not in set(comparison["strategy"]):
            comparison = pd.concat([comparison, pd.DataFrame([{"strategy": strategy}])], ignore_index=True)

    equity = pd.read_csv(base / "equity_curves.csv") if (base / "equity_curves.csv").exists() else None
    drawdowns = pd.read_csv(base / "drawdowns.csv") if (base / "drawdowns.csv").exists() else None
    return comparison, equity, drawdowns


def _returns_from_equity(equity: pd.DataFrame | None) -> pd.DataFrame:
    if equity is None or equity.empty:
        return pd.DataFrame()
    df = equity.copy()
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.sort_index()
    else:
        date_col = "Date" if "Date" in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
    df = df.apply(pd.to_numeric, errors="coerce")
    period_returns = df.pct_change(fill_method=None)
    period_returns.iloc[0] = df.iloc[0] - 1.0
    return period_returns.dropna(how="all")


def _load_return_series(output_dir: Path, equity: pd.DataFrame | None, config: dict[str, Any]) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    from_equity = _returns_from_equity(equity)
    if not from_equity.empty:
        parts.append(from_equity)
    for path in [
        output_dir / "diagnostics" / "selection_allocation_ablation" / "strategy_returns.csv",
        output_dir / "diagnostics" / "electre_vs_flowsort" / "flowsort_allocation_strategy_returns.csv",
    ]:
        if path.exists():
            df = pd.read_csv(path)
            date_col = "Date" if "Date" in df.columns else df.columns[0]
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col).sort_index().apply(pd.to_numeric, errors="coerce")
            parts.append(df)
    if config.get("smoke_test"):
        parts.append(_smoke_strategy_returns())
    if not parts:
        return pd.DataFrame()
    returns = pd.concat(parts, axis=1, sort=True)
    returns = returns.rename(columns={col: _normalize_strategy_name(str(col)) for col in returns.columns})
    returns = returns.loc[:, ~returns.columns.duplicated(keep="last")]
    return returns.sort_index()


def _ci_text(row: pd.Series) -> str:
    lower = row.get("ci_lower", np.nan)
    upper = row.get("ci_upper", np.nan)
    if pd.isna(lower) or pd.isna(upper):
        return ""
    return f"[{float(lower):.6f}, {float(upper):.6f}]"


def _statistical_note(delta: float | None, lower: float | None, upper: float | None, *, metric: str) -> str:
    if lower is None or upper is None or pd.isna(lower) or pd.isna(upper):
        return "sin evidencia estadística suficiente"
    if lower > 0.0:
        return "presenta mejor desempeño en la muestra con intervalo positivo frente al benchmark"
    if upper < 0.0:
        return "presenta peor desempeño en la muestra con intervalo negativo frente al benchmark"
    if delta is not None and not pd.isna(delta):
        if metric == "max_drawdown" and delta > 0.0:
            return "mejora drawdown pero no presenta evidencia robusta de superioridad"
        if delta > 0.0:
            return "presenta mejor desempeño en la muestra; no presenta evidencia robusta de superioridad"
    return "no presenta evidencia robusta de superioridad"


def _write_statistical_outputs(
    returns: pd.DataFrame,
    comparison: pd.DataFrame,
    config: dict[str, Any],
    paths: dict[str, Path],
) -> pd.DataFrame:
    n_bootstrap = int(config.get("statistical_n_bootstrap", 1_000 if not config.get("smoke_test") else 200))
    block_length = int(config.get("statistical_block_length", 3))
    benchmark = str(config.get("statistical_benchmark", "SPY_buy_hold"))
    metrics = ["cagr", "sharpe", "max_drawdown"]
    rows: list[dict[str, Any]] = []
    benchmark_estimates: dict[str, float] = {}
    benchmark_cis: dict[str, tuple[float, float]] = {}
    report_strategies = comparison.loc[
        comparison["model_role"].isin(["final", "experimental"]), "strategy"
    ].astype(str)
    for strategy in report_strategies:
        if strategy not in returns.columns:
            continue
        intervals = bootstrap_metric_intervals(
            returns[strategy],
            n_bootstrap=n_bootstrap,
            random_state=20260610 + len(rows),
            periods_per_year=12,
            block_length=block_length,
        )
        for metric in metrics:
            match = intervals.loc[intervals["metric"].eq(metric)]
            if match.empty:
                continue
            row = match.iloc[0]
            if strategy == benchmark:
                benchmark_estimates[metric] = float(row["estimate"])
                benchmark_cis[metric] = (float(row["ci_lower"]), float(row["ci_upper"]))
            rows.append(
                {
                    "strategy": strategy,
                    "metric": metric,
                    "estimate": float(row["estimate"]),
                    "confidence_interval": _ci_text(row),
                    "ci_lower": float(row["ci_lower"]),
                    "ci_upper": float(row["ci_upper"]),
                    "benchmark": benchmark,
                    "benchmark_delta": np.nan,
                    "statistical_note": "benchmark de comparación" if strategy == benchmark else "pendiente de delta bootstrap pareado",
                    "n_observations": int(returns[strategy].dropna().shape[0]),
                    "n_bootstrap": n_bootstrap,
                    "block_length_months": block_length,
                    "method": "monthly_moving_block_bootstrap",
                }
            )
    intervals_table = pd.DataFrame(rows)
    if intervals_table.empty:
        return comparison

    diff_rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(20260611)
    for strategy in intervals_table["strategy"].drop_duplicates():
        if strategy == benchmark or strategy not in returns.columns or benchmark not in returns.columns:
            continue
        paired = returns[[strategy, benchmark]].dropna()
        if paired.empty:
            continue
        estimates = performance_summary(paired[strategy], 0.0, 12)
        bench = performance_summary(paired[benchmark], 0.0, 12)
        values = paired.to_numpy(dtype="float64")
        for metric in metrics + ["mean_return_annualized"]:
            if metric == "mean_return_annualized":
                estimate = float(paired[strategy].mean() * 12.0)
                bench_estimate = float(paired[benchmark].mean() * 12.0)
            else:
                estimate = float(estimates[metric])
                bench_estimate = float(bench[metric])
            draws: list[float] = []
            for _ in range(n_bootstrap):
                idx = []
                starts = rng.integers(0, len(values), size=int(np.ceil(len(values) / block_length)))
                for start in starts:
                    idx.extend((int(start) + offset) % len(values) for offset in range(block_length))
                    if len(idx) >= len(values):
                        break
                sample = pd.DataFrame(values[idx[: len(values)]], columns=["strategy", "benchmark"])
                if metric == "mean_return_annualized":
                    draws.append(float((sample["strategy"].mean() - sample["benchmark"].mean()) * 12.0))
                else:
                    sm = performance_summary(sample["strategy"], 0.0, 12)
                    bm = performance_summary(sample["benchmark"], 0.0, 12)
                    draws.append(float(sm[metric] - bm[metric]))
            arr = np.asarray(draws, dtype="float64")
            lower, upper = np.quantile(arr[~np.isnan(arr)], [0.025, 0.975])
            delta = estimate - bench_estimate
            diff_rows.append(
                {
                    "strategy": strategy,
                    "benchmark": benchmark,
                    "metric": metric,
                    "estimate": estimate,
                    "benchmark_delta": delta,
                    "confidence_interval": f"[{float(lower):.6f}, {float(upper):.6f}]",
                    "ci_lower": float(lower),
                    "ci_upper": float(upper),
                    "statistical_note": _statistical_note(delta, float(lower), float(upper), metric=metric),
                    "n_observations": int(len(paired)),
                    "n_bootstrap": n_bootstrap,
                    "block_length_months": block_length,
                    "method": "paired_monthly_moving_block_bootstrap",
                }
            )
    diff_table = pd.DataFrame(diff_rows)
    if not diff_table.empty:
        for idx, row in intervals_table.iterrows():
            if row["strategy"] == benchmark:
                intervals_table.at[idx, "benchmark_delta"] = 0.0
                intervals_table.at[idx, "statistical_note"] = "benchmark de comparación"
                continue
            match = diff_table.loc[diff_table["strategy"].eq(row["strategy"]) & diff_table["metric"].eq(row["metric"])]
            if not match.empty:
                intervals_table.at[idx, "benchmark_delta"] = float(match.iloc[0]["benchmark_delta"])
                intervals_table.at[idx, "statistical_note"] = str(match.iloc[0]["statistical_note"])

    intervals_table.to_csv(paths["tables"] / "final_statistical_intervals.csv", index=False)
    diff_table.to_csv(paths["tables"] / "final_return_difference_tests.csv", index=False)
    drawdown = intervals_table.loc[intervals_table["metric"].eq("max_drawdown")].copy()
    drawdown.to_csv(paths["tables"] / "final_drawdown_comparison.csv", index=False)

    cagr_rows = intervals_table.loc[intervals_table["metric"].eq("cagr"), ["strategy", "estimate", "confidence_interval", "benchmark_delta", "statistical_note"]]
    comparison = comparison.merge(cagr_rows, on="strategy", how="left")
    return comparison


def _cap_label(cap: Any) -> str:
    return "none" if cap is None else str(cap).replace(".", "p")


def _run_parameter_sensitivity(config: dict[str, Any], paths: dict[str, Path], repo: Path, base_run_dir: Path) -> None:
    if not config.get("run_parameter_sensitivity", True):
        return
    sensitivity_root = paths["diagnostics"] / "parameter_sensitivity"
    sensitivity_root.mkdir(parents=True, exist_ok=True)
    current_cap = config.get("category_exposure_cap")
    current_rebalance = str(config.get("rebalance", "quarterly"))

    for cap in config.get("cap_sensitivity_grid", [None, 0.25, 0.35, 0.50]):
        label = _cap_label(cap)
        target = sensitivity_root / f"cap_{label}"
        if cap == current_cap:
            if not target.exists():
                shutil.copytree(base_run_dir, target, dirs_exist_ok=True)
            continue
        cfg = dict(config)
        cfg["category_exposure_cap"] = cap
        try:
            _run_subprocess(_sprint_command(cfg, target), repo, paths["logs"] / f"sensitivity_cap_{label}.log")
        except RuntimeError as exc:
            _write_json(target / "sensitivity_status.json", {"status": "failed", "reason": str(exc), "cap": cap})

    for freq in config.get("rebalance_sensitivity_grid", ["monthly", "quarterly", "annual"]):
        freq = str(freq)
        target = sensitivity_root / f"rebalance_{freq}"
        if freq == current_rebalance:
            if not target.exists():
                shutil.copytree(base_run_dir, target, dirs_exist_ok=True)
            continue
        cfg = dict(config)
        cfg["rebalance"] = freq
        try:
            _run_subprocess(_sprint_command(cfg, target), repo, paths["logs"] / f"sensitivity_rebalance_{freq}.log")
        except RuntimeError as exc:
            _write_json(target / "sensitivity_status.json", {"status": "failed", "reason": str(exc), "rebalance_frequency": freq})


def _write_sensitivity_outputs(config: dict[str, Any], output_dir: Path, paths: dict[str, Path]) -> None:
    base = output_dir / "diagnostics" / "base_run"
    electre_path = base / "electre_sensitivity.csv"
    if electre_path.exists():
        electre = pd.read_csv(electre_path)
        summary = (
            electre.groupby(["lambda_cut", "weight_multipliers"], dropna=False)["selected"]
            .mean()
            .reset_index(name="estimate")
        )
        summary["metric"] = "selection_rate"
        summary["confidence_interval"] = ""
        summary["benchmark_delta"] = ""
        summary["statistical_note"] = "sensitivity por λ y pesos; estabilidad de selección, no claim de retorno"
        summary.to_csv(paths["tables"] / "sensitivity_lambda_weights.csv", index=False)
        _copy_if_exists(electre_path, paths["diagnostics"] / "electre_sensitivity.csv")

    sensitivity_root = output_dir / "diagnostics" / "parameter_sensitivity"
    cap_rows = []
    for cap in config.get("cap_sensitivity_grid", [None, 0.25, 0.35, 0.50]):
        label = _cap_label(cap)
        comparison_path = sensitivity_root / f"cap_{label}" / "strategy_comparison.csv"
        row_data: dict[str, Any] = {
            "cap": label,
            "metric": "cagr",
            "estimate": np.nan,
            "confidence_interval": "",
            "benchmark_delta": "",
            "statistical_note": "sensitivity por cap ejecutada; no afirmar superioridad sin IC pareado específico",
        }
        status_path = sensitivity_root / f"cap_{label}" / "sensitivity_status.json"
        if status_path.exists():
            row_data["statistical_note"] = "sensitivity por cap falló por restricción/inviabilidad; ver diagnostics/parameter_sensitivity"
        if comparison_path.exists():
            table = pd.read_csv(comparison_path).reset_index()
            strategy_col = "strategy" if "strategy" in table.columns else "index"
            table[strategy_col] = table[strategy_col].map(_normalize_strategy_name)
            electre = table.loc[table[strategy_col].eq("ELECTRE_EqualWeight_walk_forward")]
            spy = table.loc[table[strategy_col].eq("SPY_buy_hold")]
            if not electre.empty:
                row_data["estimate"] = float(electre.iloc[0].get("cagr", np.nan))
                if not spy.empty:
                    row_data["benchmark_delta"] = float(electre.iloc[0].get("cagr", np.nan) - spy.iloc[0].get("cagr", np.nan))
        cap_rows.append(row_data)
    pd.DataFrame(cap_rows).to_csv(paths["tables"] / "sensitivity_cap.csv", index=False)

    rebalance_rows = []
    for freq in config.get("rebalance_sensitivity_grid", ["monthly", "quarterly", "annual"]):
        freq = str(freq)
        comparison_path = sensitivity_root / f"rebalance_{freq}" / "strategy_comparison.csv"
        row_data = {
            "rebalance_frequency": freq,
            "metric": "cagr",
            "estimate": np.nan,
            "confidence_interval": "",
            "benchmark_delta": "",
            "statistical_note": "sensitivity por frecuencia de rebalanceo ejecutada; no afirmar superioridad sin IC pareado específico",
        }
        status_path = sensitivity_root / f"rebalance_{freq}" / "sensitivity_status.json"
        if status_path.exists():
            row_data["statistical_note"] = "sensitivity por frecuencia falló; ver diagnostics/parameter_sensitivity"
        if comparison_path.exists():
            table = pd.read_csv(comparison_path).reset_index()
            strategy_col = "strategy" if "strategy" in table.columns else "index"
            table[strategy_col] = table[strategy_col].map(_normalize_strategy_name)
            electre = table.loc[table[strategy_col].eq("ELECTRE_EqualWeight_walk_forward")]
            spy = table.loc[table[strategy_col].eq("SPY_buy_hold")]
            if not electre.empty:
                row_data["estimate"] = float(electre.iloc[0].get("cagr", np.nan))
                if not spy.empty:
                    row_data["benchmark_delta"] = float(electre.iloc[0].get("cagr", np.nan) - spy.iloc[0].get("cagr", np.nan))
        rebalance_rows.append(row_data)
    pd.DataFrame(rebalance_rows).to_csv(paths["tables"] / "sensitivity_rebalance_frequency.csv", index=False)


def _finalize_outputs(config_path: Path, config: dict[str, Any], output_dir: Path, paths: dict[str, Path]) -> Path:
    comparison, equity, drawdowns = _load_final_tables(output_dir, config)
    final_models = list(config.get("models_final", DEFAULT_FINAL_MODELS))
    experimental_models = list(config.get("experimental_models", DEFAULT_EXPERIMENTAL_MODELS))
    ordered = final_models + experimental_models
    comparison["model_role"] = comparison["strategy"].apply(
        lambda s: "experimental" if s in experimental_models else ("final" if s in final_models else "diagnostic")
    )
    comparison["strategy_order"] = comparison["strategy"].apply(lambda s: ordered.index(s) if s in ordered else len(ordered))
    comparison = comparison.sort_values(["strategy_order", "strategy"]).drop(columns=["strategy_order"])
    returns = _load_return_series(output_dir, equity, config)
    if not returns.empty:
        comparison = _write_statistical_outputs(returns, comparison, config, paths)
    _write_sensitivity_outputs(config, output_dir, paths)
    comparison.to_csv(paths["tables"] / "final_strategy_comparison.csv", index=False)
    if equity is not None:
        equity.to_csv(paths["tables"] / "final_equity_curves.csv", index=False)
    if drawdowns is not None:
        drawdowns.to_csv(paths["tables"] / "final_drawdowns.csv", index=False)

    shutil.copy2(config_path, paths["configs"] / "thesis_final.yaml")
    data_flags = {
        "period_requested": config.get("period", {"start": "2015-01-01", "end": "2025-12-31"}),
        "rebalance": config.get("rebalance", "quarterly"),
        "lookback_months": int(config.get("lookback_months", 36)),
        "minimum_oos_months": int(config.get("minimum_oos_months", 60)),
        "costs_included": float(config.get("cost_bps", 10.0)) > 0,
        "cost_bps": float(config.get("cost_bps", 10.0)),
        "turnover_included": True,
        "universe_mode": config.get("universe_mode", "public_approximate_pit"),
        "claim_boundary": "public_approximate_pit reduces static-universe bias but is still public-data/pilot unless institutional survivorship-free prices are used.",
        "max_sharpe_role": "experimental_only",
    }
    _write_json(paths["diagnostics"] / "data_flags.json", data_flags)

    report = _summary_markdown(comparison, data_flags, final_models, experimental_models)
    (paths["manuscript_outputs"] / "thesis_final_summary.md").write_text(report, encoding="utf-8")
    (paths["figures"] / "README.md").write_text(
        "# Figures\n\nEquity/drawdown figure generation is deterministic from `tables/final_equity_curves.csv` and `tables/final_drawdowns.csv`.\n",
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "required_layout": REQUIRED_SUBDIRS,
        "final_models": final_models,
        "experimental_models": experimental_models,
        "artifacts": {
            "tables": sorted(p.name for p in paths["tables"].iterdir()),
            "diagnostics": sorted(p.name for p in paths["diagnostics"].iterdir()),
            "configs": sorted(p.name for p in paths["configs"].iterdir()),
            "logs": sorted(p.name for p in paths["logs"].iterdir()),
            "manuscript_outputs": sorted(p.name for p in paths["manuscript_outputs"].iterdir()),
        },
        "data_flags": data_flags,
    }
    manifest_path = output_dir / "run_manifest.json"
    _write_json(manifest_path, manifest)
    return manifest_path


def _summary_markdown(
    comparison: pd.DataFrame,
    data_flags: dict[str, Any],
    final_models: list[str],
    experimental_models: list[str],
) -> str:
    cols = [
        col
        for col in [
            "strategy",
            "model_role",
            "cagr",
            "sharpe",
            "max_drawdown",
            "avg_turnover",
            "estimate",
            "confidence_interval",
            "benchmark_delta",
            "statistical_note",
        ]
        if col in comparison.columns
    ]
    table_df = comparison[cols] if cols else comparison
    try:
        table = table_df.to_markdown(index=False)
    except ImportError:
        table = _markdown_table_without_tabulate(table_df)
    return f"""# Backtest final congelado — GOAL 13

## Configuración defendible

- Periodo solicitado: `{data_flags['period_requested']}`.
- Rebalanceo: `{data_flags['rebalance']}`.
- Lookback: `{data_flags['lookback_months']}` meses.
- Mínimo OOS exigido: `{data_flags['minimum_oos_months']}` meses.
- Costos incluidos: `{data_flags['costs_included']}` (`{data_flags['cost_bps']}` bps).
- Turnover incluido: `{data_flags['turnover_included']}`.
- Universe: `{data_flags['universe_mode']}`.

## Modelos finales

{chr(10).join(f'- `{model}`' for model in final_models)}

## Modelos experimentales

{chr(10).join(f'- `{model}`' for model in experimental_models)}

**MaxSharpe solo como experimental**: no se usa como especificación principal de tesis.

## Data flags / claim boundary

{data_flags['claim_boundary']}

## Redacción metodológica defendible — GOAL 15

Frase recomendada:

> Dado que no fue posible acceder a una base institucional survivor-bias-free como CRSP, se construyó un universo ETF público aproximado point-in-time a partir de fuentes regulatorias y de mercado, incorporando fechas de disponibilidad de información y etiquetas de calidad. Esta reconstrucción no elimina por completo el riesgo de sesgo de supervivencia, pero permite reducirlo y hacerlo explícito dentro del protocolo de backtesting.

Claims permitidos: universo ETF público aproximado point-in-time; control explícito de look-ahead mediante `source_available_date`; etiquetas de calidad; separación selección/asignación/rebalanceo; comparación ELECTRE Tri frente a FlowSort; evaluación de clasificación previa al portafolio; ablations.

Claims prohibidos: base completamente survivor-bias-free; modelo con victoria de mercado; ELECTRE como optimizador de portafolios; FlowSort como motor de rebalanceo; 18% CAGR como evidencia final.

## Inferencia estadística y robustez — GOAL 14

- `tables/final_statistical_intervals.csv`: block bootstrap mensual para CAGR, Sharpe y drawdown.
- `tables/final_return_difference_tests.csv`: tests bootstrap pareados de diferencias contra benchmark.
- `tables/final_drawdown_comparison.csv`: comparación específica de drawdown.
- `tables/sensitivity_lambda_weights.csv`: sensibilidad por λ y pesos ELECTRE.
- `tables/sensitivity_cap.csv`: grid de sensibilidad por cap.
- `tables/sensitivity_rebalance_frequency.csv`: grid de sensibilidad por frecuencia de rebalanceo.

Regla de redacción: no escribir “supera a SPY” salvo que el intervalo pareado excluya cero favorablemente. Usar: “presenta mejor desempeño en la muestra”, “no presenta evidencia robusta de superioridad”, “mejora drawdown pero no CAGR” o “mejora estabilidad pero no retorno absoluto”.

## Tabla principal

{table}
"""


def _markdown_table_without_tabulate(df: pd.DataFrame) -> str:
    """Render a small markdown table without pandas' optional tabulate dependency."""
    if df.empty:
        return "_(sin filas)_"
    text = df.astype(object).where(pd.notna(df), "")
    columns = [str(col) for col in text.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in text.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def run_thesis_final(config_path: Path | str) -> Path:
    config_path = Path(config_path)
    config = _load_config(config_path)
    output_dir = Path(config.get("output_dir", "results/thesis_final"))
    paths = _ensure_layout(output_dir)

    if not config.get("smoke_test"):
        repo = _repo_root()
        base_run_dir = paths["diagnostics"] / "base_run"
        ablation_dir = paths["diagnostics"] / "selection_allocation_ablation"
        flowsort_dir = paths["diagnostics"] / "electre_vs_flowsort"
        _run_subprocess(_sprint_command(config, base_run_dir), repo, paths["logs"] / "base_run.log")
        _run_parameter_sensitivity(config, paths, repo, base_run_dir)
        _run_subprocess(_ablation_command(config, base_run_dir, ablation_dir), repo, paths["logs"] / "selection_allocation_ablation.log")
        _write_flowsort_allocation_tables(config, base_run_dir, flowsort_dir)
        _run_subprocess(
            _flowsort_command(config, base_run_dir, flowsort_dir, paths["manuscript_outputs"] / "electre_vs_flowsort.md"),
            repo,
            paths["logs"] / "flowsort_comparison.log",
        )
        for name in [
            "fold_diagnostics.csv",
            "fold_diagnostics.json",
            "data_quality_verdict.json",
            "paired_benchmark_tests.csv",
            "fold_performance.csv",
            "cost_sensitivity.csv",
            "bootstrap_metric_intervals.csv",
            "electre_sensitivity.csv",
            "coverage_report.csv",
        ]:
            _copy_if_exists(base_run_dir / name, paths["diagnostics"] / name)
    return _finalize_outputs(config_path, config, output_dir, paths)
