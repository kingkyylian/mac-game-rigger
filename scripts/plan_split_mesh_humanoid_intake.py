#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys
from typing import Any


DEFAULT_MANIFEST = "samples/manifest.json"
DEFAULT_EVIDENCE_ROOT = "."
DEFAULT_CANDIDATES = "samples/split_mesh_humanoid_candidates.json"
DEFAULT_BLENDER = "blender"
DEFAULT_TIMEOUT_SECONDS = 300


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates")
    return [candidate for candidate in candidates if isinstance(candidate, dict)] if isinstance(candidates, list) else []


def find_candidate(candidates: list[dict[str, Any]], candidate_id: str) -> dict[str, Any]:
    for candidate in candidates:
        if candidate.get("id") == candidate_id:
            return candidate
    raise ValueError(f"Candidate not found: {candidate_id}")


def is_empty_slot(slot: dict[str, Any]) -> bool:
    evidence = slot.get("evidence")
    return slot.get("realAsset") is None and (not isinstance(evidence, dict) or not evidence)


def find_open_humanoid_slots(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for slot in manifest.get("slots", []):
        if not isinstance(slot, dict):
            continue
        if slot.get("category") != "humanoid":
            continue
        slot_id = slot.get("id")
        if not isinstance(slot_id, str) or not slot_id:
            continue
        if is_empty_slot(slot):
            slots.append(slot)
    return slots


def slot_ids(slots: list[dict[str, Any]]) -> list[str]:
    return [str(slot["id"]) for slot in slots]


def find_slot(manifest: dict[str, Any], slot_id: str) -> dict[str, Any]:
    for slot in manifest.get("slots", []):
        if isinstance(slot, dict) and slot.get("id") == slot_id:
            return slot
    raise ValueError(f"Slot not found: {slot_id}")


def build_intake_plan(
    manifest: dict[str, Any],
    *,
    slot_id: str,
    asset: Path,
    source_name: str,
    source_url: str,
    license_name: str,
    blender: str = DEFAULT_BLENDER,
    manifest_path: str = DEFAULT_MANIFEST,
    evidence_root: Path = Path(DEFAULT_EVIDENCE_ROOT),
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    slot = find_slot(manifest, slot_id)
    if slot.get("category") != "humanoid":
        raise ValueError(f"Slot {slot_id} is not humanoid")

    evidence_dir = evidence_root / "evidence" / slot_id
    asset_text = str(asset)
    source_import_smoke = [
        blender,
        "--background",
        "--factory-startup",
        "--python",
        "tools/blender_asset_import_smoke.py",
        "--",
        "--slot",
        slot_id,
        "--asset",
        asset_text,
        "--output",
        str(evidence_dir / "asset-import-smoke.json"),
        "--source-name",
        source_name,
        "--source-url",
        source_url,
        "--license",
        license_name,
    ]
    workflow = [
        blender,
        "--background",
        "--factory-startup",
        "--python",
        "tools/blender_asset_workflow.py",
        "--",
        "--asset",
        asset_text,
        "--evidence-dir",
        str(evidence_dir),
        "--summary",
        str(evidence_dir / "workflow-summary.json"),
        "--template",
        "humanoid",
        "--camera-axis",
        "x",
    ]
    register_evidence = [
        "scripts/register_asset_evidence.py",
        "--slot",
        slot_id,
        "--source-name",
        source_name,
        "--source-url",
        source_url,
        "--license",
        license_name,
        "--external-path",
        asset_text,
        "--qa-report",
        str(evidence_dir / "qa-report.json"),
        "--preview-neutral",
        str(evidence_dir / "preview-neutral.png"),
        "--preview-pose",
        str(evidence_dir / "preview-pose.png"),
        "--preview-neutral-side",
        str(evidence_dir / "preview-neutral-side.png"),
        "--preview-pose-side",
        str(evidence_dir / "preview-pose-side.png"),
        "--export-unity-fbx",
        str(evidence_dir / "export-unity.fbx"),
        "--notes",
        str(evidence_dir / "notes.md"),
        "--deformation-score",
        "<score-1-5>",
        "--unity-status",
        "not tested",
        "--unreal-status",
        "blocked",
        "--visual-review-status",
        "not reviewed",
        "--failure-type",
        "deformation quality issue",
        "--check-files",
    ]
    generate_report = [
        "scripts/generate_asset_evidence_report.py",
        "--manifest",
        manifest_path,
        "--evidence-root",
        str(evidence_root),
        "--check-evidence-files",
        "--output",
        "docs/asset-evidence-progress.md",
    ]
    plan = {
        "slot": slot_id,
        "asset": asset_text,
        "evidenceDir": str(evidence_dir),
        "commands": {
            "sourceImportSmoke": source_import_smoke,
            "workflow": workflow,
            "registerEvidence": register_evidence,
            "generateEvidenceReport": generate_report,
        },
        "acceptance": {
            "sourceImportMeshCount": ">1",
            "rigWorkflowMeshCount": ">1",
            "deformationScore": ">=3",
            "visualReview": "pass with notes or explicit cleanup limitation",
            "strictGate": "realSeparateMeshHumanoidEvidence pass",
        },
        "notes": [
            "Create evidence/<slot>/notes.md before running registerEvidence.",
            f"Workflow command timeout should stay under {timeout_seconds} seconds in manual runs.",
            "Keep source binary out of git unless its license explicitly allows committing it.",
        ],
    }
    if candidate is not None:
        plan["commands"]["candidatePreflight"] = [
            "scripts/preflight_split_mesh_candidate.py",
            "--candidate",
            str(candidate.get("id")),
            "--source-smoke",
            str(evidence_dir / "asset-import-smoke.json"),
            "--json",
        ]
        plan["candidate"] = {
            "id": candidate.get("id"),
            "sourceName": candidate.get("sourceName"),
            "sourceUrl": candidate.get("sourceUrl"),
            "license": candidate.get("license"),
            "verificationRequired": candidate.get("verificationRequired", []),
        }
    return plan


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan intake commands for a real split-mesh humanoid evidence slot."
    )
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--candidates", default=DEFAULT_CANDIDATES)
    parser.add_argument("--evidence-root", default=DEFAULT_EVIDENCE_ROOT)
    parser.add_argument("--slot", help="Humanoid manifest slot to use. Defaults to first empty humanoid slot.")
    parser.add_argument("--asset", type=Path, help="Candidate split-mesh humanoid asset path.")
    parser.add_argument("--candidate", help="Candidate id from samples/split_mesh_humanoid_candidates.json.")
    parser.add_argument("--source-name", default="Split-mesh humanoid candidate")
    parser.add_argument("--source-url", default="manual-intake")
    parser.add_argument("--license", dest="license_name", default="manual-review-required")
    parser.add_argument("--blender", default=DEFAULT_BLENDER)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def response_without_asset(manifest: dict[str, Any]) -> dict[str, Any]:
    open_slots = find_open_humanoid_slots(manifest)
    open_slot_ids = slot_ids(open_slots)
    return {
        "status": "needs_asset",
        "openHumanoidSlots": open_slot_ids,
        "recommendedSlot": open_slot_ids[0] if open_slot_ids else None,
        "requiredAssetProperties": [
            "real humanoid character",
            "source import mesh count > 1",
            "separate hair, clothing, accessory, or body-part mesh",
            "license reviewed for local product evidence use",
        ],
    }


def print_text_payload(payload: dict[str, Any]) -> None:
    if payload["status"] == "needs_asset":
        print("Split-mesh humanoid asset is still needed.")
        print(f"Open humanoid slots: {', '.join(payload['openHumanoidSlots']) or 'none'}")
        print(f"Recommended slot: {payload['recommendedSlot'] or 'none'}")
        return

    print(f"Slot: {payload['slot']}")
    print(f"Asset: {payload['asset']}")
    for label, command in payload["commands"].items():
        print(f"{label}: {shlex.join(command)}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    manifest = load_manifest(Path(args.manifest))
    candidate = None
    source_name = args.source_name
    source_url = args.source_url
    license_name = args.license_name
    if args.candidate:
        candidate = find_candidate(load_candidate_registry(Path(args.candidates)), args.candidate)
        source_name = str(candidate.get("sourceName") or source_name)
        source_url = str(candidate.get("sourceUrl") or source_url)
        license_name = str(candidate.get("license") or license_name)
    if args.asset is None:
        payload = response_without_asset(manifest)
        if candidate is not None:
            payload["candidate"] = candidate
    else:
        open_slots = find_open_humanoid_slots(manifest)
        slot_id = args.slot or (str(open_slots[0]["id"]) if open_slots else "")
        if not slot_id:
            print("No open humanoid slot is available.", file=sys.stderr)
            return 2
        payload = build_intake_plan(
            manifest,
            slot_id=slot_id,
            asset=args.asset,
            source_name=source_name,
            source_url=source_url,
            license_name=license_name,
            blender=args.blender,
            manifest_path=args.manifest,
            evidence_root=Path(args.evidence_root),
            timeout_seconds=args.timeout_seconds,
            candidate=candidate,
        )
        payload["status"] = "ready"

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_text_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
