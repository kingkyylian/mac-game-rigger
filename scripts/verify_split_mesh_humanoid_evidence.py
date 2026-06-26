#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_MANIFEST = "samples/manifest.json"
DEFAULT_EVIDENCE_ROOT = "."


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def source_mesh_count(evidence_root: Path, slot_id: str) -> int | None:
    payload = read_json(evidence_root / "evidence" / slot_id / "asset-import-smoke.json")
    metrics = payload.get("metrics") if isinstance(payload, dict) else None
    mesh_count = metrics.get("meshCount") if isinstance(metrics, dict) else None
    return mesh_count if isinstance(mesh_count, int) else None


def rig_mesh_count(evidence_root: Path, slot_id: str) -> int | None:
    payload = read_json(evidence_root / "evidence" / slot_id / "workflow-summary.json")
    if not isinstance(payload, dict):
        return None
    mesh_count = payload.get("meshCount")
    if isinstance(mesh_count, int):
        return mesh_count
    qa = payload.get("qa")
    mesh_count = qa.get("mesh_count") if isinstance(qa, dict) else None
    return mesh_count if isinstance(mesh_count, int) else None


def candidate_slots(manifest: dict[str, Any], slot_id: str | None) -> list[dict[str, Any]]:
    slots = [slot for slot in manifest.get("slots", []) if isinstance(slot, dict)]
    if slot_id is not None:
        return [slot for slot in slots if slot.get("id") == slot_id]
    return [
        slot
        for slot in slots
        if slot.get("category") == "humanoid"
        and isinstance(slot.get("realAsset"), dict)
        and isinstance(slot.get("evidence"), dict)
    ]


def verify_slot(slot: dict[str, Any], evidence_root: Path) -> dict[str, Any]:
    slot_id = str(slot.get("id") or "")
    evidence = slot.get("evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    source_count = source_mesh_count(evidence_root, slot_id)
    rig_count = rig_mesh_count(evidence_root, slot_id)
    score = evidence.get("deformationScore")
    issues: list[str] = []

    if slot.get("category") != "humanoid":
        issues.append("slot must be humanoid")
    if not isinstance(slot.get("realAsset"), dict):
        issues.append("realAsset metadata is required")
    if not isinstance(score, int) or score < 3:
        issues.append("deformation score must be >= 3")
    if not isinstance(source_count, int):
        issues.append("source import mesh count is missing")
    elif source_count <= 1:
        issues.append("source import mesh count must be > 1")
    if not isinstance(rig_count, int):
        issues.append("rig workflow mesh count is missing")
    elif rig_count <= 1:
        issues.append("rig workflow mesh count must be > 1")

    return {
        "slot": slot_id,
        "status": "pass" if not issues else "blocked",
        "sourceMeshCount": source_count,
        "rigMeshCount": rig_count,
        "deformationScore": score,
        "issues": issues,
    }


def verify_slots(
    manifest: dict[str, Any],
    evidence_root: Path,
    *,
    slot_id: str | None = None,
) -> dict[str, Any]:
    slots = candidate_slots(manifest, slot_id)
    slot_results = [verify_slot(slot, evidence_root) for slot in slots]
    passing_slots = [result["slot"] for result in slot_results if result["status"] == "pass"]
    status = "pass" if passing_slots else "blocked"
    if slot_id is not None and not slot_results:
        slot_results.append(
            {
                "slot": slot_id,
                "status": "blocked",
                "sourceMeshCount": None,
                "rigMeshCount": None,
                "deformationScore": None,
                "issues": ["slot not found"],
            }
        )
    return {
        "status": status,
        "passingSlots": passing_slots,
        "slotResults": slot_results,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify real split-mesh humanoid evidence for product-readiness gates."
    )
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--evidence-root", default=DEFAULT_EVIDENCE_ROOT)
    parser.add_argument("--slot", help="Verify a single manifest slot.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def print_text(result: dict[str, Any]) -> None:
    print(f"Status: {result['status']}")
    if result["passingSlots"]:
        print(f"Passing slots: {', '.join(result['passingSlots'])}")
    for slot_result in result["slotResults"]:
        if slot_result["status"] == "pass":
            continue
        print(f"{slot_result['slot']}: {', '.join(slot_result['issues'])}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = verify_slots(
        load_manifest(Path(args.manifest)),
        Path(args.evidence_root),
        slot_id=args.slot,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
