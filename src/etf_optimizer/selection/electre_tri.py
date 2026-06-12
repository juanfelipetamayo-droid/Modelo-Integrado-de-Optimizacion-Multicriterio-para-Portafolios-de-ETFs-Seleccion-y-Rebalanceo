from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np
import pandas as pd

Direction = Literal["max", "min"]
AssignmentMode = Literal["pessimistic", "optimistic"]
SelectionBackend = Literal["internal", "pydecision_tri_b"]


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
    """ELECTRE Tri classifier with paper-style assignment variants.

    Profiles must be ordered from worst to best. The default keeps the original
    pessimistic assignment, while ``assignment='optimistic'`` and ``use_veto=False``
    allow the four ELECTRE-TRI variants compared in portfolio-selection papers:
    pessimistic/optimistic × with/without veto.
    """

    def __init__(
        self,
        criteria: list[Criterion],
        profiles: list[Profile],
        lambda_cut: float = 0.75,
        *,
        assignment: AssignmentMode = "pessimistic",
        use_veto: bool = True,
        backend: SelectionBackend = "internal",
    ):
        if not 0 < lambda_cut <= 1:
            raise ValueError("lambda_cut must be in (0, 1]")
        if assignment not in {"pessimistic", "optimistic"}:
            raise ValueError("assignment must be 'pessimistic' or 'optimistic'")
        if backend not in {"internal", "pydecision_tri_b"}:
            raise ValueError("backend must be 'internal' or 'pydecision_tri_b'")
        if not criteria:
            raise ValueError("At least one criterion is required")
        self.criteria = criteria
        self.profiles = profiles
        self.lambda_cut = lambda_cut
        self.assignment = assignment
        self.use_veto = use_veto
        self.backend = backend
        total_weight = sum(c.weight for c in criteria)
        if total_weight <= 0:
            raise ValueError("Criterion weights must sum to a positive value")
        self._weights = {c.name: c.weight / total_weight for c in criteria}
        self._no_veto_criteria = [replace(c, v=None) for c in criteria]

    @property
    def active_criteria(self) -> list[Criterion]:
        return self.criteria if self.use_veto else self._no_veto_criteria

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
                for c in self.active_criteria
            )
        )

    def credibility(self, alternative: pd.Series, profile: Profile) -> float:
        concordance = self.concordance(alternative, profile)
        credibility = concordance
        for criterion in self.active_criteria:
            discordance = self.partial_discordance(alternative, profile, criterion)
            if discordance > concordance:
                if np.isclose(1.0 - concordance, 0.0):
                    return 0.0
                credibility *= (1.0 - discordance) / (1.0 - concordance)
        return float(np.clip(credibility, 0.0, 1.0))

    def outranks(self, alternative: pd.Series, profile: Profile) -> bool:
        return self.credibility(alternative, profile) >= self.lambda_cut

    def _profile_outranks(self, profile: Profile, alternative: pd.Series) -> bool:
        boundary_as_alternative = pd.Series(profile.values)
        alternative_as_profile = Profile(str(alternative.name or "alternative"), alternative.to_dict())
        return self.credibility(boundary_as_alternative, alternative_as_profile) >= self.lambda_cut

    def _category_from_boundary_index(self, boundary_index: int) -> str:
        """Map -1..len(profiles)-1 to ordered category labels."""
        if not self.profiles:
            return "unclassified"
        if boundary_index < 0:
            return f"below_{self.profiles[0].name}"
        if boundary_index >= len(self.profiles) - 1:
            return f"above_{self.profiles[-1].name}"
        return f"between_{self.profiles[boundary_index].name}_{self.profiles[boundary_index + 1].name}"

    def _pessimistic_boundary_index(self, alternative: pd.Series) -> int:
        best_outranked = -1
        for idx, profile in enumerate(self.profiles):
            if self.outranks(alternative, profile):
                best_outranked = idx
        return best_outranked

    def _optimistic_boundary_index(self, alternative: pd.Series) -> int:
        for idx in range(len(self.profiles) - 1, -1, -1):
            if not self._profile_outranks(self.profiles[idx], alternative):
                return idx
        return -1

    def _category_from_pydecision_class(self, class_index: int) -> str:
        # pyDecision returns 0 for the best class and len(profiles) for the worst.
        boundary_index = len(self.profiles) - 1 - class_index
        return self._category_from_boundary_index(boundary_index)

    def _pydecision_ready_matrix(self, alternatives: pd.DataFrame) -> tuple[pd.DataFrame, list[list[float]]]:
        transformed = alternatives[[c.name for c in self.criteria]].copy()
        transformed_profiles: list[list[float]] = []
        for criterion in self.criteria:
            if criterion.preference_direction == "min":
                transformed[criterion.name] = -transformed[criterion.name]
        for profile in self.profiles:
            values = []
            for criterion in self.criteria:
                value = profile.values[criterion.name]
                values.append(-value if criterion.preference_direction == "min" else value)
            transformed_profiles.append(values)
        return transformed, transformed_profiles

    def _assign_with_pydecision(self, alternatives: pd.DataFrame) -> pd.DataFrame:
        try:
            from pyDecision.algorithm import electre_tri_b
        except ImportError as exc:  # pragma: no cover - covered in environments without optional dep
            raise RuntimeError("pyDecision backend requested but pyDecision is not installed") from exc
        transformed, transformed_profiles = self._pydecision_ready_matrix(alternatives)
        q = [c.q for c in self.criteria]
        p = [c.p for c in self.criteria]
        veto = [c.v if c.v is not None and self.use_veto else 1e9 for c in self.criteria]
        weights = [self._weights[c.name] for c in self.criteria]
        rule = "pc" if self.assignment == "pessimistic" else "oc"
        classes = electre_tri_b(
            transformed.to_numpy(dtype=float),
            W=weights,
            Q=q,
            P=p,
            V=veto,
            B=transformed_profiles,
            cut_level=self.lambda_cut,
            verbose=False,
            rule=rule,
            graph=False,
        )
        rows = []
        for (name, alt), class_index in zip(alternatives.iterrows(), classes, strict=False):
            row: dict[str, float | str | bool] = {
                "assignment": self.assignment,
                "use_veto": self.use_veto,
                "backend": self.backend,
                "pydecision_class": int(class_index),
                "category": self._category_from_pydecision_class(int(class_index)),
            }
            for profile in self.profiles:
                row[f"credibility_{profile.name}"] = self.credibility(alt, profile)
                row[f"profile_outranks_{profile.name}"] = self._profile_outranks(profile, alt)
            rows.append((name, row))
        return pd.DataFrame.from_dict(dict(rows), orient="index")

    def assign(self, alternatives: pd.DataFrame) -> pd.DataFrame:
        """Assign alternatives to ordered categories.

        With one profile labels stay compatible with the original implementation:
        ``above_X`` / ``below_X``. With two profiles the labels correspond to the
        three groups used in the cited portfolio-selection paper:
        ``below_low``, ``between_low_high``, and ``above_high``.
        """
        if self.backend == "pydecision_tri_b":
            return self._assign_with_pydecision(alternatives)
        rows = []
        for name, alt in alternatives.iterrows():
            row: dict[str, float | str | bool] = {
                "assignment": self.assignment,
                "use_veto": self.use_veto,
                "backend": self.backend,
            }
            for profile in self.profiles:
                row[f"credibility_{profile.name}"] = self.credibility(alt, profile)
                row[f"profile_outranks_{profile.name}"] = self._profile_outranks(profile, alt)
            boundary_index = (
                self._pessimistic_boundary_index(alt)
                if self.assignment == "pessimistic"
                else self._optimistic_boundary_index(alt)
            )
            row["category"] = self._category_from_boundary_index(boundary_index)
            rows.append((name, row))
        return pd.DataFrame.from_dict(dict(rows), orient="index")
