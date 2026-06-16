#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "samples" / "manifest.json"
VALID_CATEGORIES = {
    "humanoid",
    "quadruped",
    "tail creature",
    "wing creature",
    "prop",
}
FAILURE_TYPES = {
    "import failure",
    "template mismatch",
    "landmark ambiguity",
    "armature generation issue",
    "weight bind issue",
    "deformation quality issue",
    "export failure",
    "engine import failure",
    "performance issue",
    "out of scope asset type",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Mac Game Rigger sample asset evidence and production-trial gates."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to manifest JSON.")
    parser.add_argument("--output", help="Write JSON report to this path.")
    parser.add_argument("--quiet", action="store_true", help="Do not print JSON to stdout.")
    parser.add_argument(
        "--require-production-trial",
        action="store_true",
        help="Exit non-zero unless the production trial gate is satisfied.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evidence_status(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        status = value.get("status")
        return status if isinstance(status, str) else None
    return None


def has_non_empty_evidence(evidence: dict[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        value = evidence.get(key)
        if non_empty_string(value):
            return True
        if isinstance(value, dict) and any(non_empty_string(item) for item in value.values()):
            return True
    return False


def validate_base_slot(slot: dict[str, Any], index: int, seen_ids: set[str]) -> list[str]:
    issues: list[str] = []
    slot_id = slot.get("id")
    if not non_empty_string(slot_id):
        issues.append(f"slots[{index}] missing id")
    elif slot_id in seen_ids:
        issues.append(f"{slot_id}: duplicate id")
    else:
        seen_ids.add(slot_id)

    category = slot.get("category")
    if category not in VALID_CATEGORIES:
        issues.append(f"{slot_id or f'slots[{index}]'}: invalid category {category!r}")

    target_filename = slot.get("targetFilename")
    if non_empty_string(slot_id) and (
        not non_empty_string(target_filename) or not target_filename.startswith(f"{slot_id}-")
    ):
        issues.append(f"{slot_id}: targetFilename must start with slot id")

    for key in ("preferredFormat", "rigTarget"):
        if not non_empty_string(slot.get(key)):
            issues.append(f"{slot_id or f'slots[{index}]'}: missing {key}")

    if not isinstance(slot.get("expectedRisks"), list):
        issues.append(f"{slot_id or f'slots[{index}]'}: expectedRisks must be a list")
    if "realAsset" not in slot:
        issues.append(f"{slot_id or f'slots[{index}]'}: missing realAsset field")
    if not isinstance(slot.get("evidence"), dict):
        issues.append(f"{slot_id or f'slots[{index}]'}: evidence must be an object")
    return issues


def validate_real_asset(slot: dict[str, Any]) -> list[str]:
    slot_id = slot["id"]
    real_asset = slot.get("realAsset")
    if real_asset is None:
        return []
    if not isinstance(real_asset, dict):
        return [f"{slot_id}: realAsset must be null or object"]

    issues: list[str] = []
    for key in ("sourceName", "license"):
        if not non_empty_string(real_asset.get(key)):
            issues.append(f"{slot_id}: realAsset.{key} is required")
    if not (
        non_empty_string(real_asset.get("sourceUrl"))
        or non_empty_string(real_asset.get("storageReference"))
    ):
        issues.append(f"{slot_id}: realAsset.sourceUrl or storageReference is required")
    if not (
        non_empty_string(real_asset.get("assetPath"))
        or non_empty_string(real_asset.get("externalPath"))
    ):
        issues.append(f"{slot_id}: realAsset.assetPath or externalPath is required")
    if not isinstance(real_asset.get("canCommitBinary"), bool):
        issues.append(f"{slot_id}: realAsset.canCommitBinary must be boolean")
    return issues


def validate_evidence(slot: dict[str, Any]) -> tuple[bool, list[str]]:
    slot_id = slot["id"]
    real_asset = slot.get("realAsset")
    evidence = slot.get("evidence", {})
    if real_asset is None:
        return False, []

    issues: list[str] = []
    score = evidence.get("deformationScore")
    if not isinstance(score, int) or not 1 <= score <= 5:
        issues.append(f"{slot_id}: evidence.deformationScore must be integer 1-5")

    if not has_non_empty_evidence(evidence, ("qaReport", "qaReportPath")):
        issues.append(f"{slot_id}: QA report evidence is required")
    if not has_non_empty_evidence(evidence, ("previewNeutral", "previewPose", "previewPath")):
        issues.append(f"{slot_id}: preview evidence is required")
    if not has_non_empty_evidence(evidence, ("exportUnityFbx", "exportUnrealFbx", "exportFbx")):
        issues.append(f"{slot_id}: exported FBX evidence is required")
    if not has_non_empty_evidence(evidence, ("notes", "notesPath")):
        issues.append(f"{slot_id}: review notes evidence is required")

    failure_type = evidence.get("failureType")
    if failure_type is not None and failure_type not in FAILURE_TYPES:
        issues.append(f"{slot_id}: invalid failureType {failure_type!r}")

    return not issues, issues


def classify_slot(slot: dict[str, Any]) -> dict[str, Any]:
    complete, evidence_issues = validate_evidence(slot)
    evidence = slot.get("evidence", {})
    score = evidence.get("deformationScore")
    unity_status = evidence_status(evidence.get("unityImport"))
    unreal_status = evidence_status(evidence.get("unrealImport"))
    return {
        "id": slot["id"],
        "category": slot["category"],
        "hasRealAsset": slot.get("realAsset") is not None,
        "evidenceComplete": complete,
        "deformationScore": score if isinstance(score, int) else None,
        "unityImportStatus": unity_status,
        "unrealImportStatus": unreal_status,
        "issues": evidence_issues,
    }


def production_trial_gate(classified_slots: list[dict[str, Any]]) -> dict[str, Any]:
    complete_slots = [slot for slot in classified_slots if slot["evidenceComplete"]]
    score_3_plus = [slot for slot in complete_slots if (slot["deformationScore"] or 0) >= 3]
    category_counts = Counter(slot["category"] for slot in complete_slots)
    complete_ids = {slot["id"] for slot in complete_slots}

    requirements = {
        "completeRealAssetsAtLeast10": len(complete_slots) >= 10,
        "humanoidsAtLeast3": category_counts["humanoid"] >= 3,
        "quadrupedsAtLeast2": category_counts["quadruped"] >= 2,
        "lowPolyHumanoidIncluded": "H-006" in complete_ids,
        "thinLimbHumanoidIncluded": "H-010" in complete_ids,
        "wideShoulderOrBulkyIncluded": bool({"H-003", "H-009"} & complete_ids),
        "tailCreatureIncluded": category_counts["tail creature"] >= 1,
        "propOrAccessoryIncluded": category_counts["prop"] >= 1 or bool({"H-003", "H-005"} & complete_ids),
        "score3PlusAtLeast70Percent": (
            len(complete_slots) > 0 and len(score_3_plus) / len(complete_slots) >= 0.7
        ),
        "unityImportPassesAtLeast3": sum(
            1 for slot in complete_slots if slot["unityImportStatus"] == "pass"
        )
        >= 3,
        "unrealPassOrExplicitBlocker": any(
            slot["unrealImportStatus"] == "pass" for slot in complete_slots
        )
        or any(slot["unrealImportStatus"] == "blocked" for slot in complete_slots),
    }
    missing = [key for key, passed in requirements.items() if not passed]
    return {
        "status": "pass" if not missing else "blocked",
        "requirements": requirements,
        "missing": missing,
        "completeRealAssetCount": len(complete_slots),
        "score3PlusCount": len(score_3_plus),
        "score3PlusRatio": round(len(score_3_plus) / len(complete_slots), 3)
        if complete_slots
        else 0,
        "categoryCounts": dict(category_counts),
    }


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    structural_issues: list[str] = []
    if manifest.get("schemaVersion") != 1:
        structural_issues.append("schemaVersion must be 1")

    slots = manifest.get("slots")
    if not isinstance(slots, list):
        return {
            "schemaStatus": "fail",
            "structuralIssues": structural_issues + ["slots must be a list"],
            "slots": [],
            "productionTrialGate": production_trial_gate([]),
        }

    seen_ids: set[str] = set()
    classified_slots: list[dict[str, Any]] = []
    for index, slot in enumerate(slots):
        if not isinstance(slot, dict):
            structural_issues.append(f"slots[{index}] must be an object")
            continue
        base_issues = validate_base_slot(slot, index, seen_ids)
        real_asset_issues = validate_real_asset(slot) if not base_issues else []
        structural_issues.extend(base_issues)
        structural_issues.extend(real_asset_issues)
        if not base_issues and not real_asset_issues:
            classified_slots.append(classify_slot(slot))

    real_asset_slots = [slot for slot in classified_slots if slot["hasRealAsset"]]
    complete_slots = [slot for slot in classified_slots if slot["evidenceComplete"]]
    incomplete_real_assets = [
        slot for slot in real_asset_slots if slot["hasRealAsset"] and not slot["evidenceComplete"]
    ]

    return {
        "schemaStatus": "pass" if not structural_issues else "fail",
        "structuralIssues": structural_issues,
        "slotCount": len(slots),
        "realAssetCount": len(real_asset_slots),
        "completeEvidenceCount": len(complete_slots),
        "incompleteRealAssets": incomplete_real_assets,
        "slots": classified_slots,
        "productionTrialGate": production_trial_gate(classified_slots),
    }


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    try:
        report = validate_manifest(load_manifest(manifest_path))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to read manifest: {exc}", file=sys.stderr)
        return 66

    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(f"{payload}\n", encoding="utf-8")
    if not args.quiet:
        print(payload)

    if report["schemaStatus"] != "pass":
        return 1
    if args.require_production_trial and report["productionTrialGate"]["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
