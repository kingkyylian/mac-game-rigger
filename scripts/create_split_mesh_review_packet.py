#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def nested_dict(payload: dict[str, Any] | None, key: str) -> dict[str, Any]:
    value = payload.get(key) if isinstance(payload, dict) else None
    return value if isinstance(value, dict) else {}


def mesh_count_from_source(source_smoke: dict[str, Any] | None) -> int | None:
    value = nested_dict(source_smoke, "metrics").get("meshCount")
    return value if isinstance(value, int) else None


def mesh_count_from_workflow(workflow_summary: dict[str, Any] | None) -> int | None:
    if not isinstance(workflow_summary, dict):
        return None
    value = workflow_summary.get("meshCount")
    if isinstance(value, int):
        return value
    value = nested_dict(workflow_summary, "qa").get("mesh_count")
    return value if isinstance(value, int) else None


def status_from(payload: dict[str, Any] | None, *keys: str) -> str:
    current: Any = payload
    for key in keys:
        current = current.get(key) if isinstance(current, dict) else None
    return current if isinstance(current, str) else "unknown"


def source_value(source_smoke: dict[str, Any] | None, key: str) -> str:
    value = nested_dict(source_smoke, "source").get(key)
    return value if isinstance(value, str) and value else "unknown"


def build_markdown(
    *,
    slot_id: str,
    source_smoke: dict[str, Any] | None,
    workflow_summary: dict[str, Any] | None,
    source_count: int,
    rig_count: int,
) -> str:
    qa_status = status_from(workflow_summary, "qa", "status")
    pose_status = status_from(workflow_summary, "poseDeformation", "status")
    suggested_category = nested_dict(source_smoke, "metrics").get("suggestedCategory") or "unknown"
    return "\n".join(
        [
            f"# {slot_id} Split-Mesh Humanoid Review Packet",
            "",
            "## Source",
            "",
            f"- Source name: {source_value(source_smoke, 'name')}",
            f"- Source URL: {source_value(source_smoke, 'url')}",
            f"- License: {source_value(source_smoke, 'license')}",
            f"- Source mesh count: {source_count}",
            f"- Suggested category: {suggested_category}",
            "",
            "## Workflow",
            "",
            f"- Rig workflow mesh count: {rig_count}",
            f"- QA status: {qa_status}",
            f"- Pose deformation status: {pose_status}",
            "",
            "## Manual Review",
            "",
            "- Manual review status: not reviewed",
            "- Deformation score: not set",
            "- Visual review notes: TODO",
            "- Cleanup limitations: TODO",
            "",
            "Do not register this slot until deformation score and visual review are set manually.",
            "",
        ]
    )


def build_review_packet(*, slot_id: str, source_smoke: Path, workflow_summary: Path) -> dict[str, Any]:
    source_payload = read_json(source_smoke)
    workflow_payload = read_json(workflow_summary)
    source_count = mesh_count_from_source(source_payload)
    rig_count = mesh_count_from_workflow(workflow_payload)
    issues = []
    if not isinstance(source_count, int):
        issues.append("source import mesh count is missing")
    elif source_count <= 1:
        issues.append("source import mesh count must be > 1")
    if not isinstance(rig_count, int):
        issues.append("rig workflow mesh count is missing")
    elif rig_count <= 1:
        issues.append("rig workflow mesh count must be > 1")

    return {
        "status": "pass" if not issues else "blocked",
        "slot": slot_id,
        "sourceSmoke": str(source_smoke),
        "workflowSummary": str(workflow_summary),
        "sourceMeshCount": source_count,
        "rigMeshCount": rig_count,
        "issues": issues,
        "markdown": None
        if issues
        else build_markdown(
            slot_id=slot_id,
            source_smoke=source_payload,
            workflow_summary=workflow_payload,
            source_count=source_count,
            rig_count=rig_count,
        ),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create split-mesh humanoid manual review notes from evidence JSON.")
    parser.add_argument("--slot", required=True)
    parser.add_argument("--source-smoke", required=True, type=Path)
    parser.add_argument("--workflow-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = build_review_packet(
        slot_id=args.slot,
        source_smoke=args.source_smoke,
        workflow_summary=args.workflow_summary,
    )
    if result["status"] == "pass":
        if args.output.exists() and not args.force:
            print(f"Output already exists: {args.output}", file=sys.stderr)
            return 2
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(str(result["markdown"]), encoding="utf-8")
        result["output"] = str(args.output)
    if args.json:
        payload = {key: value for key, value in result.items() if key != "markdown"}
        print(json.dumps(payload, indent=2))
    elif result["status"] == "pass":
        print(f"Wrote {args.output}")
    else:
        print(f"Status: {result['status']}")
        for issue in result["issues"]:
            print(f"- {issue}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
