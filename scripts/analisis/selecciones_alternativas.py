"""Controles de selección sobre el mismo universo, fechas, costos y motor walk-forward de una corrida ELECTRE.

Reutiliza, por rebalanceo, los ETFs clasificables y sus criterios guardados en fold_stage_artifacts de la
corrida de referencia, y cambia solo la regla de selección:
  electre        -> los ETFs que eligió ELECTRE (validación: debe reproducir la corrida)
  top_<criterio> -> los N mejores por un solo criterio (N = tamaño de la selección ELECTRE en esa fecha)
  aleatoria_<s>  -> N ETFs al azar entre los clasificables (semilla s)
La asignación (equiponderada o mínima varianza) y los costos usan el código del proyecto.

Uso: uv run python data/rerun/selecciones_alternativas.py <corrida_referencia> <close.parquet> <inicio> <fin> <salida.csv> [n_aleatorias]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from etf_optimizer.backtesting.engine import BacktestConfig, WalkForwardBacktester
from etf_optimizer.backtesting.metrics import performance_summary
from etf_optimizer.pipeline import PipelineConfig, _optimize_weights
from etf_optimizer.selection.electre_tri import Criterion

run_dir, close_path, start, end, out_path = sys.argv[1:6]
n_random = int(sys.argv[6]) if len(sys.argv) > 6 else 100
COSTS = [0.0, 10.0, 25.0, 50.0]

folds = {}
for fold in sorted(Path(run_dir, "fold_stage_artifacts").iterdir()):
    weights = pd.read_csv(fold / "portfolio_weights.csv")
    rebalance = pd.Timestamp(weights["rebalance_date"].iloc[0])
    folds[rebalance] = {
        "criteria": pd.read_csv(fold / "criteria_matrix.csv").set_index("ticker"),
        "electre": pd.read_csv(fold / "selected_etfs.csv")["ticker"].astype(str).tolist(),
    }

eligible = pd.read_csv(Path(run_dir, "eligible_universe.csv"))["ticker"].astype(str).unique().tolist()
prices = pd.read_parquet(close_path).loc[start:end].resample("ME").last()
prices = prices[[t for t in eligible if t in prices.columns]]
returns = prices.sort_index().pct_change().dropna(how="all")

# Mismos parámetros del corredor (run_sprint_experiment.py); criteria/profiles no se usan al asignar pesos.
dummy = [Criterion("cagr", weight=1.0)]


def selector(rule: str, seed: int | None):
    rng = np.random.default_rng(seed)

    def select(rebalance: pd.Timestamp) -> list[str]:
        fold = folds[rebalance]
        n = len(fold["electre"])
        if rule == "electre":
            return fold["electre"]
        if rule.startswith("top_"):
            criterion = rule[4:]
            ascending = criterion == "volatility"
            return fold["criteria"][criterion].sort_values(ascending=ascending, kind="mergesort").head(n).index.tolist()
        return rng.choice(fold["criteria"].index.to_numpy(), size=n, replace=False).tolist()

    return select


def backtest(rule: str, allocation: str, cost_bps: float, seed: int | None = None) -> pd.Series:
    config = PipelineConfig(criteria=dummy, profiles=[], strategy=allocation, test_size=3, step_size=3, periods_per_year=12)
    select = selector(rule, seed)

    def strategy(train_returns: pd.DataFrame) -> pd.Series:
        rebalance = returns.index[returns.index > train_returns.index[-1]][0]
        chosen = select(pd.Timestamp(rebalance))
        train = train_returns[chosen].dropna(axis=0, how="any")
        weights, _ = _optimize_weights(train, config)
        return weights

    engine = WalkForwardBacktester(
        BacktestConfig(train_size=36, test_size=3, step_size=3, cost_bps=cost_bps, weight_drift="buy_and_hold", rebalance_policy="calendar")
    )
    return engine.run(returns, strategy).portfolio_returns


rows = []
series_10pb = {}
rules = [("electre", None), ("top_cagr", None), ("top_sharpe", None), ("top_sortino", None), ("top_volatility", None)]
rules += [(f"aleatoria_{s}", s) for s in range(n_random)]
for rule, seed in rules:
    for allocation in ["equal_weight", "min_variance"]:
        costs = COSTS if not rule.startswith("aleatoria") else [10.0]
        for cost in costs:
            series = backtest(rule, allocation, cost, seed)
            summary = performance_summary(series, risk_free_rate=0.0, periods_per_year=12)
            rows.append({"regla": rule, "asignacion": allocation, "costo_pb": cost, "meses": len(series), **summary})
            if cost == 10.0:
                series_10pb[f"{rule}|{allocation}"] = series
    print(rule, flush=True)
pd.DataFrame(rows).to_csv(out_path, index=False)
pd.DataFrame(series_10pb).to_csv(out_path.replace(".csv", "_retornos_10pb.csv"))
