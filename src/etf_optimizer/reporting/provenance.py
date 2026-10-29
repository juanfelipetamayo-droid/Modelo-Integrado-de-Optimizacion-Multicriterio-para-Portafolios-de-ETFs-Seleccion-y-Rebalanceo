from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MethodologySource:
    name: str
    citation: str
    role: str
    url: str | None = None


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _code_source(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "exists": path.exists(),
    }


def write_provenance_record(
    output_path: Path,
    *,
    code_paths: list[Path],
    data_sources: list[dict[str, Any]],
    methodology_sources: list[MethodologySource],
    generated_artifacts: list[Path],
    limitations: list[str],
    run_metadata: dict[str, Any] | None = None,
    data_quality: dict[str, Any] | None = None,
) -> Path:
    """Write an audit record for code, data, methods, outputs, and limitations.

    The record is intentionally machine-readable so a thesis appendix or external
    reviewer can trace which local source files, public databases, and academic
    methodologies were used to create a result directory.
    """
    record = {
        "schema_version": "1.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "code_sources": [_code_source(path) for path in code_paths],
        "data_sources": data_sources,
        "methodology_sources": [asdict(source) for source in methodology_sources],
        "generated_artifacts": [
            {
                "path": str(path),
                "sha256": _sha256(path),
                "exists": path.exists(),
            }
            for path in generated_artifacts
        ],
        "limitations": limitations,
        "run_metadata": run_metadata or {},
        "data_quality": data_quality or {},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
