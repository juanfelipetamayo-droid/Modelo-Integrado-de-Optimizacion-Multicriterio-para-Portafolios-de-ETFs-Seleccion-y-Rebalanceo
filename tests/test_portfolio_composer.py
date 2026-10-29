from __future__ import annotations

import pandas as pd

from etf_optimizer.portfolio.composer import (
    compose_target_portfolio,
    compute_rebalance_orders,
)


def test_compose_target_portfolio_uses_latest_weights_and_caps_names_and_allocations():
    weights = pd.DataFrame(
        [
            {"date": "2024-01-31", "AAA": 0.50, "BBB": 0.30, "CCC": 0.20, "DDD": 0.0},
        ]
    ).set_index("date")
    universe = pd.DataFrame(
        [
            {"ticker": "AAA", "name": "Alpha ETF", "asset_class": "Equity", "category": "Large Cap"},
            {"ticker": "BBB", "name": "Bond ETF", "asset_class": "Fixed Income", "category": "Aggregate Bond"},
            {"ticker": "CCC", "name": "Commodity ETF", "asset_class": "Commodity", "category": "Broad Commodity"},
            {"ticker": "DDD", "name": "Zero ETF", "asset_class": "Equity", "category": "Unused"},
        ]
    )

    portfolio = compose_target_portfolio(
        weights,
        universe,
        capital=10_000,
        max_positions=2,
        max_weight=0.60,
        min_weight=0.01,
    )

    assert portfolio.as_of == "2024-01-31"
    assert portfolio.total_weight == 1.0
    assert [line.ticker for line in portfolio.lines] == ["AAA", "BBB"]
    assert [line.name for line in portfolio.lines] == ["Alpha ETF", "Bond ETF"]
    assert [round(line.weight, 4) for line in portfolio.lines] == [0.6, 0.4]
    assert [round(line.target_value, 2) for line in portfolio.lines] == [6000.0, 4000.0]
    assert "Cartera objetivo" in portfolio.summary_es


def test_compose_target_portfolio_applies_risk_profile_position_limits():
    weights = pd.DataFrame(
        [{"date": "2024-01-31", "AAA": 0.40, "BBB": 0.30, "CCC": 0.20, "DDD": 0.10}]
    ).set_index("date")
    universe = pd.DataFrame({"ticker": ["AAA", "BBB", "CCC", "DDD"]})

    conservative = compose_target_portfolio(weights, universe, capital=20_000, risk_profile="conservador")
    aggressive = compose_target_portfolio(weights, universe, capital=20_000, risk_profile="agresivo")

    assert len(conservative.lines) == 3
    assert len(aggressive.lines) == 4
    assert conservative.profile_es == "Conservador"
    assert aggressive.profile_es == "Agresivo"


def test_compute_rebalance_orders_generates_buy_sell_hold_with_threshold():
    target = pd.DataFrame(
        [
            {"ticker": "AAA", "weight": 0.50, "target_value": 5_000.0},
            {"ticker": "BBB", "weight": 0.30, "target_value": 3_000.0},
            {"ticker": "CCC", "weight": 0.20, "target_value": 2_000.0},
        ]
    )
    current = pd.DataFrame(
        [
            {"ticker": "AAA", "market_value": 4_000.0},
            {"ticker": "BBB", "market_value": 3_100.0},
            {"ticker": "DDD", "market_value": 1_000.0},
        ]
    )

    orders = compute_rebalance_orders(target, current, threshold_value=250.0)

    assert orders.loc[orders["ticker"] == "AAA", "accion"].item() == "Comprar"
    assert orders.loc[orders["ticker"] == "BBB", "accion"].item() == "Mantener"
    assert orders.loc[orders["ticker"] == "CCC", "accion"].item() == "Comprar"
    assert orders.loc[orders["ticker"] == "DDD", "accion"].item() == "Vender"
    assert orders.loc[orders["ticker"] == "AAA", "diferencia_valor"].item() == 1000.0
    assert orders.loc[orders["ticker"] == "DDD", "peso_objetivo"].item() == 0.0
