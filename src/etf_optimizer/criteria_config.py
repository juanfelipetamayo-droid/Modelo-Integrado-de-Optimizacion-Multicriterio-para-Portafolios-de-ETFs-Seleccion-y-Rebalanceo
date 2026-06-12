from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

CriterionOrientation = Literal["maximize", "minimize"]

_REQUIRED_FIELDS = {
    "criterion_name",
    "formula",
    "lookback_window",
    "orientation",
    "is_hard_filter",
    "missing_data_rule",
    "winsorization_rule",
    "normalization_rule",
    "source",
}


@dataclass(frozen=True)
class CriteriaConfigSpec:
    """Auditable ETF criterion/filter specification loaded from YAML.

    The config intentionally covers both pre-ELECTRE hard filters and MCDM
    criteria, but keeps them distinguishable through ``is_hard_filter`` so
    eligibility gates are not accidentally treated as outranking dimensions.
    """

    criterion_name: str
    formula: str
    lookback_window: str
    orientation: CriterionOrientation
    is_hard_filter: bool
    missing_data_rule: str
    winsorization_rule: str
    normalization_rule: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_criteria_config(path: str | Path) -> list[CriteriaConfigSpec]:
    """Load and validate ``configs/criteria_config.yaml`` style files."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    entries = raw.get("criteria")
    if not isinstance(entries, list) or not entries:
        raise ValueError("criteria config must contain a non-empty 'criteria' list")

    specs: list[CriteriaConfigSpec] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"criteria entry {index} must be a mapping")
        missing = _REQUIRED_FIELDS - entry.keys()
        if missing:
            raise ValueError(f"criteria entry {index} is missing fields: {sorted(missing)}")
        if entry["orientation"] not in {"maximize", "minimize"}:
            raise ValueError(f"criteria entry {index} has invalid orientation: {entry['orientation']}")
        if not isinstance(entry["is_hard_filter"], bool):
            raise ValueError(f"criteria entry {index} must set is_hard_filter as a boolean")
        specs.append(
            CriteriaConfigSpec(
                criterion_name=str(entry["criterion_name"]),
                formula=str(entry["formula"]),
                lookback_window=str(entry["lookback_window"]),
                orientation=entry["orientation"],
                is_hard_filter=entry["is_hard_filter"],
                missing_data_rule=str(entry["missing_data_rule"]),
                winsorization_rule=str(entry["winsorization_rule"]),
                normalization_rule=str(entry["normalization_rule"]),
                source=str(entry["source"]),
            )
        )
    return specs
