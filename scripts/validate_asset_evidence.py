#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
from typing import Any
import zlib


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
    parser.add_argument(
        "--evidence-root",
        default=str(REPO_ROOT),
        help="Root used to resolve relative evidence file paths.",
    )
    parser.add_argument("--output", help="Write JSON report to this path.")
    parser.add_argument("--quiet", action="store_true", help="Do not print JSON to stdout.")
    parser.add_argument(
        "--check-evidence-files",
        action="store_true",
        help="Check that local evidence file paths exist.",
    )
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


def evidence_references(evidence: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, str]]:
    references: list[dict[str, str]] = []
    for key in keys:
        value = evidence.get(key)
        if non_empty_string(value):
            references.append({"key": key, "path": value})
        elif isinstance(value, dict):
            path = value.get("path") or value.get("filePath")
            storage_reference = value.get("storageReference")
            url = value.get("url")
            if non_empty_string(path):
                references.append({"key": key, "path": path})
            elif non_empty_string(storage_reference):
                references.append({"key": key, "storageReference": storage_reference})
            elif non_empty_string(url):
                references.append({"key": key, "url": url})
    return references


def evidence_file_issues(
    slot_id: str,
    evidence: dict[str, Any],
    keys: tuple[str, ...],
    label: str,
    evidence_root: Path,
) -> list[str]:
    issues: list[str] = []
    for reference in evidence_references(evidence, keys):
        path_value = reference.get("path")
        if not path_value:
            continue
        path = Path(path_value)
        resolved_path = path if path.is_absolute() else evidence_root / path
        if not resolved_path.exists():
            issues.append(f"{slot_id}: {label} evidence file not found: {path_value}")
    return issues


def _png_channel_info(color_type: int) -> tuple[int, tuple[int, ...]]:
    if color_type == 0:
        return 1, (0,)
    if color_type == 2:
        return 3, (0, 1, 2)
    if color_type == 4:
        return 2, (0,)
    if color_type == 6:
        return 4, (0, 1, 2)
    raise ValueError(f"unsupported PNG color type {color_type}")


def _unfilter_png_row(filter_type: int, row: bytes, previous: bytes, bpp: int) -> bytes:
    result = bytearray(row)
    for index, value in enumerate(row):
        left = result[index - bpp] if index >= bpp else 0
        up = previous[index] if previous else 0
        up_left = previous[index - bpp] if previous and index >= bpp else 0
        if filter_type == 0:
            predictor = 0
        elif filter_type == 1:
            predictor = left
        elif filter_type == 2:
            predictor = up
        elif filter_type == 3:
            predictor = (left + up) // 2
        elif filter_type == 4:
            pa = abs(up - up_left)
            pb = abs(left - up_left)
            pc = abs(left + up - (2 * up_left))
            if pa <= pb and pa <= pc:
                predictor = left
            elif pb <= pc:
                predictor = up
            else:
                predictor = up_left
        else:
            raise ValueError(f"unsupported PNG filter type {filter_type}")
        result[index] = (value + predictor) & 0xFF
    return bytes(result)


def png_luma_stats(path: Path) -> dict[str, float | tuple[int, int]]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG file")

    width = height = bit_depth = color_type = None
    compressed = bytearray()
    offset = 8
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        payload = data[payload_start:payload_end]
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if bit_depth != 8 or compression != 0 or filter_method != 0 or interlace != 0:
                raise ValueError("unsupported PNG encoding")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
        offset = payload_end + 4

    if width is None or height is None or bit_depth is None or color_type is None:
        raise ValueError("missing PNG header")
    channels, luma_channels = _png_channel_info(color_type)
    row_length = width * channels
    raw = zlib.decompress(bytes(compressed))
    expected_length = height * (1 + row_length)
    if len(raw) != expected_length:
        raise ValueError("unexpected PNG data length")

    values: list[int] = []
    previous = b"\x00" * row_length
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        row = _unfilter_png_row(filter_type, raw[offset : offset + row_length], previous, channels)
        offset += row_length
        previous = row
        for pixel_start in range(0, row_length, channels):
            samples = [row[pixel_start + channel] for channel in luma_channels]
            values.append(sum(samples) // len(samples))

    minimum = min(values)
    maximum = max(values)
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {
        "extrema": (minimum, maximum),
        "stddev": variance ** 0.5,
    }


def preview_image_issues(
    slot_id: str,
    evidence: dict[str, Any],
    evidence_root: Path,
) -> list[str]:
    issues: list[str] = []
    for reference in evidence_references(evidence, ("previewNeutral", "previewPose", "previewPath")):
        path_value = reference.get("path")
        if not path_value or not path_value.lower().endswith(".png"):
            continue
        path = Path(path_value)
        resolved_path = path if path.is_absolute() else evidence_root / path
        if not resolved_path.exists():
            continue
        try:
            stats = png_luma_stats(resolved_path)
        except (OSError, ValueError, zlib.error) as exc:
            issues.append(f"{slot_id}: preview image unreadable: {path_value} ({exc})")
            continue
        if stats["stddev"] < 1.0:
            issues.append(f"{slot_id}: preview image appears blank: {path_value}")
    return issues


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


def validate_evidence(
    slot: dict[str, Any],
    *,
    evidence_root: Path,
    check_files: bool,
) -> tuple[bool, list[str]]:
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

    if check_files:
        issues.extend(
            evidence_file_issues(
                slot_id,
                evidence,
                ("qaReport", "qaReportPath"),
                "QA report",
                evidence_root,
            )
        )
        issues.extend(
            evidence_file_issues(
                slot_id,
                evidence,
                ("previewNeutral", "previewPose", "previewPath"),
                "preview",
                evidence_root,
            )
        )
        issues.extend(preview_image_issues(slot_id, evidence, evidence_root))
        issues.extend(
            evidence_file_issues(
                slot_id,
                evidence,
                ("exportUnityFbx", "exportUnrealFbx", "exportFbx"),
                "exported FBX",
                evidence_root,
            )
        )
        issues.extend(
            evidence_file_issues(
                slot_id,
                evidence,
                ("notes", "notesPath"),
                "review notes",
                evidence_root,
            )
        )

    return not issues, issues


def classify_slot(slot: dict[str, Any], *, evidence_root: Path, check_files: bool) -> dict[str, Any]:
    complete, evidence_issues = validate_evidence(
        slot,
        evidence_root=evidence_root,
        check_files=check_files,
    )
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


def validate_manifest(
    manifest: dict[str, Any],
    *,
    evidence_root: Path,
    check_files: bool,
) -> dict[str, Any]:
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
            classified_slots.append(
                classify_slot(slot, evidence_root=evidence_root, check_files=check_files)
            )

    real_asset_slots = [slot for slot in classified_slots if slot["hasRealAsset"]]
    complete_slots = [slot for slot in classified_slots if slot["evidenceComplete"]]
    incomplete_real_assets = [
        slot for slot in real_asset_slots if slot["hasRealAsset"] and not slot["evidenceComplete"]
    ]

    return {
        "schemaStatus": "pass" if not structural_issues else "fail",
        "evidenceFileCheck": "enabled" if check_files else "disabled",
        "evidenceRoot": str(evidence_root),
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
    evidence_root = Path(args.evidence_root)
    check_files = bool(args.check_evidence_files or args.require_production_trial)
    try:
        report = validate_manifest(
            load_manifest(manifest_path),
            evidence_root=evidence_root,
            check_files=check_files,
        )
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
