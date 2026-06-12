from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

RiskProfile = Literal["conservador", "moderado", "agresivo"]

PROFILE_LIMITS: dict[str, tuple[str, int, float]] = {
    "conservador": ("Conservador", 3, 0.40),
    "moderado": ("Moderado", 5, 0.35),
    "agresivo": ("Agresivo", 8, 0.50),
}


@dataclass(frozen=True)
class PortfolioLine:
    ticker: str
    name: str
    asset_class: str
    category: str
    weight: float
    target_value: float


@dataclass(frozen=True)
class TargetPortfolio:
    as_of: str
    profile_es: str
    capital: float
    lines: list[PortfolioLine]
    total_weight: float
    summary_es: str

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "ticker": line.ticker,
                    "nombre": line.name,
                    "clase de activo": line.asset_class,
                    "categoría": line.category,
                    "peso": line.weight,
                    "valor objetivo": line.target_value,
                }
                for line in self.lines
            ]
        )


def _latest_weight_row(weights: pd.DataFrame) -> tuple[str, pd.Series]:
    if weights.empty:
        raise ValueError("weights must contain at least one rebalance row")
    latest_index = weights.index[-1]
    row = weights.iloc[-1].astype(float)
    return str(latest_index), row


def _metadata_by_ticker(universe: pd.DataFrame) -> dict[str, dict[str, object]]:
    if universe.empty or "ticker" not in universe.columns:
        return {}
    return universe.drop_duplicates("ticker").set_index("ticker").to_dict(orient="index")


def _normalize_with_cap(weights: pd.Series, max_weight: float) -> pd.Series:
    selected = weights[weights > 0].sort_values(ascending=False).astype(float)
    if selected.empty:
        return selected
    normalized = selected / selected.sum()
    capped = pd.Series(0.0, index=normalized.index, dtype=float)
    remaining_names = list(normalized.index)
    remaining_weight = 1.0
    remaining_source = normalized.copy()

    while remaining_names:
        allocation = remaining_source.loc[remaining_names] / remaining_source.loc[remaining_names].sum() * remaining_weight
        over_cap = allocation[allocation > max_weight]
        if over_cap.empty:
            capped.loc[allocation.index] = allocation
            break
        for name in over_cap.index:
            capped.loc[name] = max_weight
            remaining_names.remove(name)
        remaining_weight = 1.0 - capped.sum()
        if remaining_weight <= 0:
            break

    if capped.sum() <= 0:
        return capped
    return capped / capped.sum()


def compose_target_portfolio(
    weights: pd.DataFrame,
    universe: pd.DataFrame,
    *,
    capital: float,
    risk_profile: RiskProfile | str = "moderado",
    max_positions: int | None = None,
    max_weight: float | None = None,
    min_weight: float = 0.005,
) -> TargetPortfolio:
    """Convert optimizer weights into a user-facing target portfolio."""
    as_of, latest = _latest_weight_row(weights)
    profile_es, profile_positions, profile_cap = PROFILE_LIMITS.get(
        risk_profile, PROFILE_LIMITS["moderado"]
    )
    position_limit = max_positions or profile_positions
    cap = max_weight or profile_cap

    candidate_weights = latest[latest >= min_weight].sort_values(ascending=False).head(position_limit)
    normalized = _normalize_with_cap(candidate_weights, cap)
    metadata = _metadata_by_ticker(universe)

    lines: list[PortfolioLine] = []
    for ticker, weight in normalized.items():
        meta = metadata.get(str(ticker), {})
        raw_name = meta.get("name")
        raw_asset_class = meta.get("asset_class")
        raw_category = meta.get("category")
        name = str(raw_name) if raw_name is not None and not pd.isna(raw_name) else str(ticker)
        asset_class = (
            str(raw_asset_class)
            if raw_asset_class is not None and not pd.isna(raw_asset_class)
            else "No especificado"
        )
        category = str(raw_category) if raw_category is not None and not pd.isna(raw_category) else "No especificada"
        lines.append(
            PortfolioLine(
                ticker=str(ticker),
                name=name,
                asset_class=asset_class,
                category=category,
                weight=round(float(weight), 10),
                target_value=round(float(weight) * float(capital), 2),
            )
        )

    total_weight = round(sum(line.weight for line in lines), 10)
    summary = (
        f"Cartera objetivo {profile_es.lower()} con {len(lines)} ETF, "
        f"capital asignado de {capital:,.2f} y fecha de pesos {as_of}."
    )
    return TargetPortfolio(
        as_of=as_of,
        profile_es=profile_es,
        capital=float(capital),
        lines=lines,
        total_weight=total_weight,
        summary_es=summary,
    )


def compute_rebalance_orders(
    target: pd.DataFrame,
    current: pd.DataFrame,
    *,
    threshold_value: float = 0.0,
) -> pd.DataFrame:
    """Compare current holdings against target values and produce Spanish order intents."""
    target_values = target.set_index("ticker") if not target.empty else pd.DataFrame()
    current_values = current.set_index("ticker") if not current.empty else pd.DataFrame()
    tickers = sorted(set(target_values.index).union(set(current_values.index)))

    rows: list[dict[str, object]] = []
    for ticker in tickers:
        target_value = float(target_values.loc[ticker, "target_value"]) if ticker in target_values.index else 0.0
        target_weight = float(target_values.loc[ticker, "weight"]) if ticker in target_values.index else 0.0
        current_value = float(current_values.loc[ticker, "market_value"]) if ticker in current_values.index else 0.0
        difference = round(target_value - current_value, 2)
        if abs(difference) < threshold_value:
            action = "Mantener"
        elif difference > 0:
            action = "Comprar"
        else:
            action = "Vender"
        rows.append(
            {
                "ticker": ticker,
                "peso_objetivo": target_weight,
                "valor_actual": current_value,
                "valor_objetivo": target_value,
                "diferencia_valor": difference,
                "accion": action,
            }
        )
    return pd.DataFrame(rows)
