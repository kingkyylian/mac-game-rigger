from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class RigQAReport:
    mesh_count: int
    vertex_count: int
    bone_count: int
    unweighted_vertices: int
    over_limit_vertices: int
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def save_qa_report(report: RigQAReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    payload["warnings"] = list(report.warnings)
    payload["errors"] = list(report.errors)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
