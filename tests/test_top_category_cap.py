import pandas as pd

from etf_optimizer.pipeline import _cap_top_category
from etf_optimizer.selection.electre_tri import Criterion


def test_cap_keeps_best_weighted_percentiles_and_respects_min_direction():
    matrix = pd.DataFrame(
        {"cagr": [0.30, 0.10, 0.20], "volatility": [0.30, 0.10, 0.10]},
        index=["HIGH_RET_HIGH_VOL", "LOW_RET_LOW_VOL", "MID_RET_LOW_VOL"],
    )
    criteria = [
        Criterion("cagr", weight=0.5, preference_direction="max"),
        Criterion("volatility", weight=0.5, preference_direction="min"),
    ]
    assert _cap_top_category(list(matrix.index), matrix, criteria, cap=1) == ["MID_RET_LOW_VOL"]
    assert _cap_top_category(["LOW_RET_LOW_VOL"], matrix, criteria, cap=1) == ["LOW_RET_LOW_VOL"]
