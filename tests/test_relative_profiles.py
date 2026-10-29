import pandas as pd

from etf_optimizer.pipeline import _relative_profiles
from etf_optimizer.selection.electre_tri import Criterion


def test_relative_profiles_mirror_quantile_for_min_criteria():
    matrix = pd.DataFrame({"cagr": [0.0, 0.1, 0.2, 0.3, 0.4], "volatility": [0.1, 0.2, 0.3, 0.4, 0.5]})
    criteria = [
        Criterion("cagr", weight=0.5, preference_direction="max", q=0.0, p=0.02, v=0.05),
        Criterion("volatility", weight=0.5, preference_direction="min", q=0.0, p=0.02, v=0.10),
    ]
    minimum, preferred = _relative_profiles(matrix, criteria, (0.5, 0.75))
    assert minimum.values == {"cagr": 0.2, "volatility": 0.3}
    # preferred is stricter: higher return, lower volatility
    assert preferred.values == {"cagr": 0.3, "volatility": 0.2}
