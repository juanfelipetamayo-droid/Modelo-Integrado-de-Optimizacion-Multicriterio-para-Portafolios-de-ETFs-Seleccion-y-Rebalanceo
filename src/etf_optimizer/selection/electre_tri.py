from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

Direction = Literal["max", "min"]


@dataclass(frozen=True)
class Criterion:
    """ELECTRE Tri criterion definition.

    q, p and v are the indifference, preference and veto thresholds described in the
    ELECTRE outranking literature. They must be expressed in the same units as the
    criterion values.
    """

    name: str
    weight: float
    preference_direction: Direction = "max"
    q: float = 0.0
    p: float = 0.0
    v: float | None = None


@dataclass(frozen=True)
class Profile:
    """Boundary/reference profile separating ordered categories."""

    name: str
    values: dict[str, float]


class ElectreTri:
    """Minimal ELECTRE Tri classifier using pessimistic boundary assignment.

    The implementation follows the concordance/discordance/credibility structure of
    ELECTRE Tri (Yu, 1992; Roy, 1991; Mousseau, Slowinski & Zielniewicz, 2000).
    """

    def __init__(self, criteria: list[Criterion], profiles: list[Profile], lambda_cut: float = 0.75):
        if not 0 < lambda_cut <= 1:
            raise ValueError("lambda_cut must be in (0, 1]")
        if not criteria:
            raise ValueError("At least one criterion is required")
        self.criteria = criteria
        self.profiles = profiles
        self.lambda_cut = lambda_cut
        total_weight = sum(c.weight for c in criteria)
        if total_weight <= 0:
            raise ValueError("Criterion weights must sum to a positive value")
        self._weights = {c.name: c.weight / total_weight for c in criteria}

    def _advantage_over_profile(self, alternative_value: float, profile_value: float, criterion: Criterion) -> float:
        """Positive values mean the alternative is better than the profile."""
        if criterion.preference_direction == "max":
            return alternative_value - profile_value
        return profile_value - alternative_value

    def partial_concordance(self, alternative: pd.Series, profile: Profile, criterion: Criterion) -> float:
        advantage = self._advantage_over_profile(alternative[criterion.name], profile.values[criterion.name], criterion)
        disadvantage = -advantage
        q, p = criterion.q, criterion.p
        if disadvantage <= q:
            return 1.0
        if disadvantage >= p:
            return 0.0
        if np.isclose(p, q):
            return 0.0
        return float((p - disadvantage) / (p - q))

    def partial_discordance(self, alternative: pd.Series, profile: Profile, criterion: Criterion) -> float:
        if criterion.v is None:
            return 0.0
        advantage = self._advantage_over_profile(alternative[criterion.name], profile.values[criterion.name], criterion)
        disadvantage = -advantage
        p, v = criterion.p, criterion.v
        if disadvantage <= p:
            return 0.0
        if disadvantage >= v:
            return 1.0
        if np.isclose(v, p):
            return 1.0
        return float((disadvantage - p) / (v - p))

    def concordance(self, alternative: pd.Series, profile: Profile) -> float:
        return float(
            sum(
                self._weights[c.name] * self.partial_concordance(alternative, profile, c)
                for c in self.criteria
            )
        )

    def credibility(self, alternative: pd.Series, profile: Profile) -> float:
        concordance = self.concordance(alternative, profile)
        credibility = concordance
        for criterion in self.criteria:
            discordance = self.partial_discordance(alternative, profile, criterion)
            if discordance > concordance:
                if np.isclose(1.0 - concordance, 0.0):
                    return 0.0
                credibility *= (1.0 - discordance) / (1.0 - concordance)
        return float(np.clip(credibility, 0.0, 1.0))

    def outranks(self, alternative: pd.Series, profile: Profile) -> bool:
        return self.credibility(alternative, profile) >= self.lambda_cut

    def assign(self, alternatives: pd.DataFrame) -> pd.DataFrame:
        """Pessimistic ELECTRE Tri assignment.

        Profiles must be ordered from worst to best (index 0 = lowest boundary).
        For one profile X labels are ``above_X`` / ``below_X``.
        For multiple profiles the alternative is assigned to the category above
        the best profile it outranks, or ``below_{profiles[0].name}`` if none.
        """
        rows = []
        for name, alt in alternatives.iterrows():
            row: dict[str, float | str] = {}
            outranked: list[str] = []
            for profile in self.profiles:
                sigma = self.credibility(alt, profile)
                row[f"credibility_{profile.name}"] = sigma
                if sigma >= self.lambda_cut:
                    outranked.append(profile.name)
            if len(self.profiles) == 1:
                profile_name = self.profiles[0].name
                row["category"] = f"above_{profile_name}" if outranked else f"below_{profile_name}"
            else:
                row["category"] = f"above_{outranked[-1]}" if outranked else f"below_{self.profiles[0].name}"
            rows.append((name, row))
        return pd.DataFrame.from_dict(dict(rows), orient="index")
