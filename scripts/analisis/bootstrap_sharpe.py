"""Bootstrap pareado por bloques móviles (3 meses, 1000 remuestreos) de la diferencia de razón de Sharpe
anualizada (rf = 0) entre una estrategia ELECTRE (por defecto la equiponderada) y cada referente, a partir de equity_curves.csv.

Uso: [ESTRATEGIA=ELECTRE_MinVariance_walk_forward] uv run python data/rerun/bootstrap_sharpe.py <carpeta_resultados> [...]
"""
import os
import sys

import numpy as np
import pandas as pd

STRATEGY = os.environ.get("ESTRATEGIA", "ELECTRE_EqualWeight_walk_forward")
REFERENCES = ["SPY_buy_hold", "60/40_SPY_BND_fixed_weight", "Universe_EqualWeight_walk_forward"]


def monthly_returns(folder: str) -> pd.DataFrame:
    equity = pd.read_csv(f"{folder}/equity_curves.csv", index_col=0, parse_dates=True)
    returns = equity.pct_change()
    returns.iloc[0] = equity.iloc[0] - 1.0  # las curvas parten de 1.0 antes del primer mes
    return returns


def sharpe(x: np.ndarray) -> float:
    return float(x.mean() / x.std(ddof=1) * np.sqrt(12))


def block_bootstrap(pair: np.ndarray, n_boot: int = 1000, block: int = 3, seed: int = 20260518) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = len(pair)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n, int(np.ceil(n / block)))
        idx = np.concatenate([np.arange(s, s + block) % n for s in starts])[:n]
        sample = pair[idx]
        diffs[i] = sharpe(sample[:, 0]) - sharpe(sample[:, 1])
    return diffs


for folder in sys.argv[1:]:
    returns = monthly_returns(folder)
    for ref in REFERENCES:
        pair = returns[[STRATEGY, ref]].dropna().to_numpy()
        diffs = block_bootstrap(pair)
        low, high = np.percentile(diffs, [2.5, 97.5])
        point = sharpe(pair[:, 0]) - sharpe(pair[:, 1])
        print(f"{folder} | {ref}: dif={point:.3f} IC95=[{low:.3f}, {high:.3f}] n={len(pair)}")
