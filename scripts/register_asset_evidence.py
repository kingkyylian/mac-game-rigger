#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "samples" / "manifest.json"
VALID_IMPORT_STATUSES = {"pass", "fail", "blocked", "not tested"}
VALID_VISUAL_REVIEW_STATUSES = {"pass", "fail", "not reviewed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register real asset metadata and evidence paths in samples/manifest.json."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Manifest JSON path.")
    parser.add_argument("--slot", required=True, help="Stable slot id, e.g. H-001.")
    parser.add_argument("--source-name", required=True, help="Human-readable source asset name.")
    parser.add_argument("--source-url", help="Source URL or ticket link.")
    parser.add_argument("--storage-reference", help="External storage reference for the source asset.")
    parser.add_argument("--license", required=True, help="Asset license or internal usage label.")
    parser.add_argument("--asset-path", help="Repo-relative asset path.")
    parser.add_argument("--external-path", help="Local or external asset path outside git.")
    parser.add_argument(
        "--can-commit-binary",
        action="store_true",
        help="Set true only when the source binary may be committed to git.",
    )
    parser.add_argument("--qa-report", required=True, help="QA report path or storage reference.")
    parser.add_argument("--preview-neutral", required=True, help="Neutral preview path or storage ref.")
    parser.add_argument("--preview-pose", help="Pose preview path or storage ref.")
    parser.add_argument("--preview-neutral-side", help="Side neutral preview path or storage ref.")
    parser.add_argument("--preview-pose-side", help="Side pose preview path or storage ref.")
    parser.add_argument("--export-fbx", help="Generic exported FBX path or storage ref.")
    parser.add_argument("--export-unity-fbx", help="Unity exported FBX path or storage ref.")
    parser.add_argument("--export-unreal-fbx", help="Unreal exported FBX path or storage ref.")
    parser.add_argument("--notes", required=True, help="Review notes path or storage reference.")
    parser.add_argument("--deformation-score", required=True, type=int, help="Integer score 1-5.")
    parser.add_argument("--unity-status", choices=sorted(VALID_IMPORT_STATUSES), default="not tested")
    parser.add_argument("--unreal-status", choices=sorted(VALID_IMPORT_STATUSES), default="not tested")
    parser.add_argument("--visual-review-status", choices=sorted(VALID_VISUAL_REVIEW_STATUSES))
    parser.add_argument("--visual-review-notes", help="Short manual review note for visual quality claims.")
    parser.add_argument("--failure-type", help="Optional failure classification from the protocol.")
    parser.add_argument(
        "--evidence-root",
        default=str(REPO_ROOT),
        help="Root used to resolve relative local evidence paths.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Require local evidence files to exist before writing.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an already registered slot.")
    parser.add_argument("--dry-run", action="store_true", help="Print updated manifest without writing.")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def non_empty(value: str | None) -> bool:
    return bool(value and value.strip())


def looks_external(value: str) -> bool:
    return "://" in value


def evidence_value(value: str) -> str | dict[str, str]:
    return {"storageReference": value} if looks_external(value) else value


def require(condition: bool, message: str) -> None:
    if not condition:
        print(message, file=sys.stderr)
        raise SystemExit(64)


def resolve_local_path(evidence_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else evidence_root / path


def assert_existing_files(evidence_root: Path, values: list[tuple[str, str | None]]) -> None:
    missing: list[str] = []
    for label, value in values:
        if not non_empty(value) or looks_external(value):
            continue
        path = resolve_local_path(evidence_root, value or "")
        if not path.exists():
            missing.append(f"{label}: {value}")
    if missing:
        print("Missing evidence files:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
        raise SystemExit(66)


def find_slot(manifest: dict[str, Any], slot_id: str) -> dict[str, Any]:
    for slot in manifest.get("slots", []):
        if slot.get("id") == slot_id:
            return slot
    print(f"Slot not found: {slot_id}", file=sys.stderr)
    raise SystemExit(2)


def build_real_asset(args: argparse.Namespace) -> dict[str, Any]:
    require(
        non_empty(args.source_url) or non_empty(args.storage_reference),
        "Pass --source-url or --storage-reference.",
    )
    require(non_empty(args.asset_path) or non_empty(args.external_path), "Pass --asset-path or --external-path.")
    real_asset: dict[str, Any] = {
        "sourceName": args.source_name,
        "license": args.license,
        "canCommitBinary": bool(args.can_commit_binary),
    }
    if non_empty(args.source_url):
        real_asset["sourceUrl"] = args.source_url
    if non_empty(args.storage_reference):
        real_asset["storageReference"] = args.storage_reference
    if non_empty(args.asset_path):
        real_asset["assetPath"] = args.asset_path
    if non_empty(args.external_path):
        real_asset["externalPath"] = args.external_path
    return real_asset


def build_evidence(args: argparse.Namespace) -> dict[str, Any]:
    require(1 <= args.deformation_score <= 5, "--deformation-score must be 1-5.")
    require(
        non_empty(args.export_fbx)
        or non_empty(args.export_unity_fbx)
        or non_empty(args.export_unreal_fbx),
        "Pass at least one of --export-fbx, --export-unity-fbx, or --export-unreal-fbx.",
    )
    evidence: dict[str, Any] = {
        "qaReport": evidence_value(args.qa_report),
        "previewNeutral": evidence_value(args.preview_neutral),
        "notes": evidence_value(args.notes),
        "deformationScore": args.deformation_score,
        "unityImport": {"status": args.unity_status},
        "unrealImport": {"status": args.unreal_status},
    }
    if non_empty(args.preview_pose):
        evidence["previewPose"] = evidence_value(args.preview_pose)
    if non_empty(args.preview_neutral_side):
        evidence["previewNeutralSide"] = evidence_value(args.preview_neutral_side)
    if non_empty(args.preview_pose_side):
        evidence["previewPoseSide"] = evidence_value(args.preview_pose_side)
    if non_empty(args.export_fbx):
        evidence["exportFbx"] = evidence_value(args.export_fbx)
    if non_empty(args.export_unity_fbx):
        evidence["exportUnityFbx"] = evidence_value(args.export_unity_fbx)
    if non_empty(args.export_unreal_fbx):
        evidence["exportUnrealFbx"] = evidence_value(args.export_unreal_fbx)
    if non_empty(args.visual_review_status):
        evidence["visualReview"] = {"status": args.visual_review_status}
        if non_empty(args.visual_review_notes):
            evidence["visualReview"]["notes"] = args.visual_review_notes
    if non_empty(args.failure_type):
        evidence["failureType"] = args.failure_type
    return evidence


def run_validator(manifest_path: Path, evidence_root: Path, check_files: bool) -> None:
    command = [
        str(REPO_ROOT / "scripts" / "validate_asset_evidence.py"),
        "--manifest",
        str(manifest_path),
        "--evidence-root",
        str(evidence_root),
        "--quiet",
    ]
    if check_files:
        command.append("--check-evidence-files")
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    evidence_root = Path(args.evidence_root)
    manifest = load_manifest(manifest_path)
    slot = find_slot(manifest, args.slot)

    if not args.force and (slot.get("realAsset") is not None or slot.get("evidence")):
        print(f"{args.slot} already has realAsset or evidence. Pass --force to overwrite.", file=sys.stderr)
        return 73

    local_values = [
        ("qaReport", args.qa_report),
        ("previewNeutral", args.preview_neutral),
        ("previewPose", args.preview_pose),
        ("previewNeutralSide", args.preview_neutral_side),
        ("previewPoseSide", args.preview_pose_side),
        ("exportFbx", args.export_fbx),
        ("exportUnityFbx", args.export_unity_fbx),
        ("exportUnrealFbx", args.export_unreal_fbx),
        ("notes", args.notes),
    ]
    if args.check_files:
        assert_existing_files(evidence_root, local_values)

    slot["realAsset"] = build_real_asset(args)
    slot["evidence"] = build_evidence(args)

    payload = json.dumps(manifest, indent=2)
    if args.dry_run:
        print(payload)
        return 0

    manifest_path.write_text(f"{payload}\n", encoding="utf-8")
    run_validator(manifest_path, evidence_root, args.check_files)
    print(json.dumps({"status": "registered", "slot": args.slot}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
