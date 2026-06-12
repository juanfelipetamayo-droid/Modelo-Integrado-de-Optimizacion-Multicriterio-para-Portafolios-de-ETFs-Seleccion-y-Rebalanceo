from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from etf_optimizer.selection.electre_tri import Criterion, Profile

FlowSortPreference = Literal["usual", "v_shape", "level"]


@dataclass(frozen=True)
class FlowSort:
    """Small PROMETHEE/FlowSort-style classifier for MCDA stage comparison.

    This implementation is intentionally transparent for thesis diagnostics: alternatives
    are scored by weighted preference flows against ordered boundary profiles and assigned
    to the same category labels used by ELECTRE Tri. It is a sorting/classification stage,
    not an allocation or rebalance method.
    """

    criteria: list[Criterion]
    profiles: list[Profile]
    preference_function: FlowSortPreference = "v_shape"
    use_net_flow: bool = True

    def __post_init__(self) -> None:
        if not self.criteria:
            raise ValueError("At least one criterion is required")
        if self.preference_function not in {"usual", "v_shape", "level"}:
            raise ValueError("preference_function must be usual, v_shape or level")
        total_weight = sum(c.weight for c in self.criteria)
        if total_weight <= 0:
            raise ValueError("Criterion weights must sum to a positive value")

    @property
    def weights(self) -> dict[str, float]:
        total_weight = sum(c.weight for c in self.criteria)
        return {c.name: c.weight / total_weight for c in self.criteria}

    def _advantage(self, left: pd.Series, right: pd.Series, criterion: Criterion) -> float:
        if criterion.preference_direction == "max":
            return float(left[criterion.name] - right[criterion.name])
        return float(right[criterion.name] - left[criterion.name])

    def _preference_degree(self, advantage: float, criterion: Criterion) -> float:
        if self.preference_function == "usual":
            return 1.0 if advantage > 0 else 0.0
        q = max(float(criterion.q), 0.0)
        p = max(float(criterion.p), q)
        if advantage <= q:
            return 0.0
        if self.preference_function == "level":
            return 0.5 if advantage <= p else 1.0
        if np.isclose(p, q):
            return 1.0
        if advantage >= p:
            return 1.0
        return float((advantage - q) / (p - q))

    def preference(self, left: pd.Series, right: pd.Series) -> float:
        weights = self.weights
        return float(
            sum(
                weights[criterion.name] * self._preference_degree(self._advantage(left, right, criterion), criterion)
                for criterion in self.criteria
            )
        )

    def flow_components_against_profiles(self, alternative: pd.Series) -> tuple[float, float, float]:
        if not self.profiles:
            return 0.0, 0.0, 0.0
        leaving = []
        entering = []
        for profile in self.profiles:
            profile_series = pd.Series(profile.values)
            leaving.append(self.preference(alternative, profile_series))
            entering.append(self.preference(profile_series, alternative))
        leaving_flow = float(np.mean(leaving))
        entering_flow = float(np.mean(entering))
        return leaving_flow, entering_flow, leaving_flow - entering_flow

    def net_flow_against_profiles(self, alternative: pd.Series) -> float:
        leaving_flow, _entering_flow, net_flow = self.flow_components_against_profiles(alternative)
        return net_flow if self.use_net_flow else leaving_flow

    def profile_flow(self, profile: Profile) -> float:
        profile_series = pd.Series(profile.values)
        if not self.profiles:
            return 0.0
        peers = [pd.Series(other.values) for other in self.profiles if other.name != profile.name]
        if not peers:
            return 0.0
        leaving = [self.preference(profile_series, peer) for peer in peers]
        entering = [self.preference(peer, profile_series) for peer in peers]
        leaving_flow = float(np.mean(leaving))
        entering_flow = float(np.mean(entering))
        return leaving_flow - entering_flow if self.use_net_flow else leaving_flow

    def _category_from_boundary_index(self, boundary_index: int) -> str:
        if not self.profiles:
            return "unclassified"
        if boundary_index < 0:
            return f"below_{self.profiles[0].name}"
        if boundary_index >= len(self.profiles) - 1:
            return f"above_{self.profiles[-1].name}"
        return f"between_{self.profiles[boundary_index].name}_{self.profiles[boundary_index + 1].name}"

    def assign(self, alternatives: pd.DataFrame) -> pd.DataFrame:
        profile_flows = [self.profile_flow(profile) for profile in self.profiles]
        rows: list[tuple[object, dict[str, float | str | bool]]] = []
        for name, alternative in alternatives.iterrows():
            leaving_flow, entering_flow, net_flow = self.flow_components_against_profiles(alternative)
            flow = net_flow if self.use_net_flow else leaving_flow
            boundary_index = -1
            for idx, profile_flow in enumerate(profile_flows):
                if flow >= profile_flow:
                    boundary_index = idx
            row: dict[str, float | str | bool] = {
                "category": self._category_from_boundary_index(boundary_index),
                "flowsort_leaving_flow": leaving_flow,
                "flowsort_entering_flow": entering_flow,
                "flowsort_net_flow": net_flow,
                "ranking_flow": flow,
                "flowsort_preference_function": self.preference_function,
                "flowsort_use_net_flow": self.use_net_flow,
            }
            for profile, profile_flow in zip(self.profiles, profile_flows, strict=False):
                row[f"profile_flow_{profile.name}"] = profile_flow
            rows.append((name, row))
        return pd.DataFrame.from_dict(dict(rows), orient="index")
