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
VISUAL_REVIEW_STATUSES = {"pass", "fail", "not reviewed"}
PREVIEW_EVIDENCE_KEYS = (
    "previewNeutral",
    "previewPose",
    "previewNeutralSide",
    "previewPoseSide",
    "previewPath",
)
UNITY_MAX_DIMENSION_WARNING_LIMITS = {
    "humanoid": 10,
    "quadruped": 12,
    "tail creature": 30,
    "wing creature": 30,
    "prop": 5,
}
UNITY_MAX_DIMENSION_SEVERE_LIMITS = {
    "humanoid": 100,
    "quadruped": 120,
    "tail creature": 300,
    "wing creature": 300,
    "prop": 50,
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
    parser.add_argument(
        "--require-configured-animator-smoke",
        action="store_true",
        help="Block humanoid score >=3 Unity-pass evidence missing configuredAnimatorSmoke.",
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


def _png_luma_values(path: Path) -> tuple[int, int, list[int]]:
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
    return width, height, values


def png_luma_stats(path: Path) -> dict[str, float | tuple[int, int]]:
    _, _, values = _png_luma_values(path)
    minimum = min(values)
    maximum = max(values)
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {
        "extrema": (minimum, maximum),
        "stddev": variance ** 0.5,
    }


def png_foreground_stats(path: Path, *, threshold: int = 128) -> dict[str, Any]:
    width, height, values = _png_luma_values(path)
    foreground_points: list[tuple[int, int]] = []
    for index, value in enumerate(values):
        if value >= threshold:
            foreground_points.append((index % width, index // width))

    total_pixels = width * height
    if not foreground_points:
        return {
            "imageSize": {"width": width, "height": height},
            "foregroundPixelRatio": 0.0,
            "foregroundBounds": None,
            "foregroundFillRatio": 0.0,
        }

    min_x = min(point[0] for point in foreground_points)
    max_x = max(point[0] for point in foreground_points)
    min_y = min(point[1] for point in foreground_points)
    max_y = max(point[1] for point in foreground_points)
    bounds_width = max_x - min_x + 1
    bounds_height = max_y - min_y + 1
    bounds_area = bounds_width * bounds_height
    foreground_count = len(foreground_points)
    top_center_x = _band_center_x(
        foreground_points,
        min_y=min_y,
        max_y=max_y,
        band="top",
    )
    bottom_center_x = _band_center_x(
        foreground_points,
        min_y=min_y,
        max_y=max_y,
        band="bottom",
    )
    vertical_center_shift_ratio = 0.0
    if top_center_x is not None and bottom_center_x is not None:
        vertical_center_shift_ratio = abs(top_center_x - bottom_center_x) / bounds_height
    return {
        "imageSize": {"width": width, "height": height},
        "foregroundPixelRatio": round(foreground_count / total_pixels, 4),
        "foregroundBounds": {
            "x": min_x,
            "y": min_y,
            "width": bounds_width,
            "height": bounds_height,
        },
        "foregroundFillRatio": round(foreground_count / bounds_area, 4),
        "verticalCenterShiftRatio": round(vertical_center_shift_ratio, 4),
    }


def _band_center_x(
    points: list[tuple[int, int]],
    *,
    min_y: int,
    max_y: int,
    band: str,
) -> float | None:
    height = max_y - min_y + 1
    band_height = max(1, round(height * 0.25))
    if band == "top":
        y_limit = min_y + band_height - 1
        band_points = [point for point in points if point[1] <= y_limit]
    elif band == "bottom":
        y_limit = max_y - band_height + 1
        band_points = [point for point in points if point[1] >= y_limit]
    else:
        raise ValueError(f"unsupported band: {band}")
    if not band_points:
        return None
    return sum(point[0] for point in band_points) / len(band_points)


def preview_image_issues(
    slot_id: str,
    evidence: dict[str, Any],
    evidence_root: Path,
) -> list[str]:
    issues: list[str] = []
    for reference in evidence_references(evidence, PREVIEW_EVIDENCE_KEYS):
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


def preview_image_diagnostics(
    evidence: dict[str, Any],
    evidence_root: Path,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for reference in evidence_references(evidence, PREVIEW_EVIDENCE_KEYS):
        key = reference["key"]
        path_value = reference.get("path")
        if not path_value or not path_value.lower().endswith(".png"):
            continue
        path = Path(path_value)
        resolved_path = path if path.is_absolute() else evidence_root / path
        if not resolved_path.exists():
            continue
        try:
            diagnostics[key] = png_foreground_stats(resolved_path)
        except (OSError, ValueError, zlib.error):
            continue
    return diagnostics


def pose_quality_issues(
    slot_id: str,
    category: Any,
    score: Any,
    evidence_root: Path,
) -> list[str]:
    if not isinstance(score, int) or score < 3:
        return []

    summary_path = evidence_root / "evidence" / slot_id / "workflow-summary.json"
    if not summary_path.exists():
        return [f"{slot_id}: workflow summary with poseDeformation is required for score >=3"]
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{slot_id}: workflow summary unreadable: {summary_path} ({exc})"]

    pose_deformation = summary.get("poseDeformation")
    if not isinstance(pose_deformation, dict):
        return [f"{slot_id}: poseDeformation summary is required for score >=3"]
    status = pose_deformation.get("status")
    if status == "fail":
        max_ratio = pose_deformation.get("maxAxisExpansionRatio")
        expanded_axes = pose_deformation.get("expandedAxes")
        suffix_parts = []
        if isinstance(max_ratio, (int, float)):
            suffix_parts.append(f"maxAxisExpansionRatio={max_ratio:g}")
        if isinstance(expanded_axes, list) and expanded_axes:
            suffix_parts.append(f"expandedAxes={','.join(str(axis) for axis in expanded_axes)}")
        suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
        return [f"{slot_id}: poseDeformation.status=fail is not allowed for score >=3{suffix}"]
    if status not in {"pass", "warn"}:
        return [f"{slot_id}: poseDeformation.status must be pass or warn for score >=3"]
    humanoid_diagnostic_issue = humanoid_quality_issue_for_score(
        slot_id,
        category,
        summary.get("humanoidDiagnostics"),
    )
    if humanoid_diagnostic_issue:
        return [humanoid_diagnostic_issue]
    return []


def unity_import_quality_issues(
    slot_id: str,
    category: Any,
    score: Any,
    evidence: dict[str, Any],
    evidence_root: Path,
    *,
    require_configured_animator_smoke: bool = False,
) -> list[str]:
    if evidence_status(evidence.get("unityImport")) != "pass":
        return []

    unity_import_path = evidence_root / "evidence" / slot_id / "unity-import.json"
    if not unity_import_path.is_file():
        return [f"{slot_id}: Unity import pass requires evidence/{slot_id}/unity-import.json"]

    try:
        payload = json.loads(unity_import_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{slot_id}: Unity import evidence unreadable: {unity_import_path} ({exc})"]

    issues: list[str] = []
    if payload.get("status") != "pass":
        issues.append(f"{slot_id}: Unity import evidence status must be pass")

    result = payload.get("result")
    if not isinstance(result, dict):
        issues.append(f"{slot_id}: Unity import evidence result object is required")
        return issues

    if result.get("instantiated") is not True:
        issues.append(f"{slot_id}: Unity import instantiated must be true")

    if isinstance(score, int) and score >= 3:
        skinned_count = result.get("skinnedMeshRendererCount")
        if not isinstance(skinned_count, int) or skinned_count < 1:
            issues.append(f"{slot_id}: Unity import skinnedMeshRendererCount must be >= 1 for score >=3")

        bone_transform_smoke = result.get("boneTransformSmoke")
        if not isinstance(bone_transform_smoke, dict) or bone_transform_smoke.get("passed") is not True:
            issues.append(f"{slot_id}: Unity import boneTransformSmoke.passed must be true for score >=3")
        else:
            bone_candidate_count = bone_transform_smoke.get("boneCandidateCount")
            if not isinstance(bone_candidate_count, int) or bone_candidate_count < 1:
                issues.append(f"{slot_id}: Unity import boneCandidateCount must be >= 1 for score >=3")
            rotation_delta = bone_transform_smoke.get("rotationDeltaDegrees")
            if not isinstance(rotation_delta, (int, float)) or rotation_delta <= 0:
                issues.append(f"{slot_id}: Unity import rotationDeltaDegrees must be > 0 for score >=3")

        animation_clip_smoke = result.get("animationClipSmoke")
        if not isinstance(animation_clip_smoke, dict) or animation_clip_smoke.get("passed") is not True:
            issues.append(f"{slot_id}: Unity import animationClipSmoke.passed must be true for score >=3")
        else:
            sampled_bone = animation_clip_smoke.get("sampledBone")
            if not non_empty_string(sampled_bone):
                issues.append(f"{slot_id}: Unity import sampledBone is required for score >=3")
            sampled_rotation_delta = animation_clip_smoke.get("sampledRotationDeltaDegrees")
            if not isinstance(sampled_rotation_delta, (int, float)) or sampled_rotation_delta <= 0:
                issues.append(f"{slot_id}: Unity import sampledRotationDeltaDegrees must be > 0 for score >=3")

        configured_animator_smoke = result.get("configuredAnimatorSmoke")
        if (
            category == "humanoid"
            and configured_animator_smoke is None
            and require_configured_animator_smoke
        ):
            issues.append(f"{slot_id}: Unity import configuredAnimatorSmoke is required for humanoid score >=3")
        if category == "humanoid" and configured_animator_smoke is not None:
            if not isinstance(configured_animator_smoke, dict) or configured_animator_smoke.get("passed") is not True:
                issues.append(f"{slot_id}: Unity import configuredAnimatorSmoke.passed must be true for humanoid score >=3")
            else:
                animator_count = configured_animator_smoke.get("animatorCount")
                if not isinstance(animator_count, int) or animator_count < 1:
                    issues.append(f"{slot_id}: Unity import configured animatorCount must be >= 1 for humanoid score >=3")
                if configured_animator_smoke.get("controllerAssigned") is not True:
                    issues.append(f"{slot_id}: Unity import configured Animator controllerAssigned must be true for humanoid score >=3")
                state_count = configured_animator_smoke.get("stateCount")
                if not isinstance(state_count, int) or state_count < 1:
                    issues.append(f"{slot_id}: Unity import configured Animator stateCount must be >= 1 for humanoid score >=3")
                sampled_bone = configured_animator_smoke.get("sampledBone")
                if not non_empty_string(sampled_bone):
                    issues.append(f"{slot_id}: Unity import configured Animator sampledBone is required for humanoid score >=3")
                sampled_rotation_delta = configured_animator_smoke.get("sampledRotationDeltaDegrees")
                if not isinstance(sampled_rotation_delta, (int, float)) or sampled_rotation_delta <= 0:
                    issues.append(
                        f"{slot_id}: Unity import configured Animator sampledRotationDeltaDegrees must be > 0 for humanoid score >=3"
                    )

        humanoid_avatar_smoke = result.get("humanoidAvatarSmoke")
        if category == "humanoid" and humanoid_avatar_smoke is not None:
            if not isinstance(humanoid_avatar_smoke, dict) or humanoid_avatar_smoke.get("passed") is not True:
                issues.append(f"{slot_id}: Unity import humanoidAvatarSmoke.passed must be true for humanoid score >=3")
            else:
                if humanoid_avatar_smoke.get("avatarIsValid") is not True:
                    issues.append(f"{slot_id}: Unity import humanoid Avatar avatarIsValid must be true for humanoid score >=3")
                if humanoid_avatar_smoke.get("avatarIsHuman") is not True:
                    issues.append(f"{slot_id}: Unity import humanoid Avatar avatarIsHuman must be true for humanoid score >=3")
                if humanoid_avatar_smoke.get("retargetReady") is not True:
                    issues.append(f"{slot_id}: Unity import humanoid Avatar retargetReady must be true for humanoid score >=3")
                mapped_human_bone_count = humanoid_avatar_smoke.get("mappedHumanBoneCount")
                required_human_bone_count = humanoid_avatar_smoke.get("requiredHumanBoneCount")
                if not isinstance(mapped_human_bone_count, int) or mapped_human_bone_count < 1:
                    issues.append(f"{slot_id}: Unity import mappedHumanBoneCount must be >= 1 for humanoid score >=3")
                if not isinstance(required_human_bone_count, int) or required_human_bone_count < 1:
                    issues.append(f"{slot_id}: Unity import requiredHumanBoneCount must be >= 1 for humanoid score >=3")
                if (
                    isinstance(mapped_human_bone_count, int)
                    and isinstance(required_human_bone_count, int)
                    and mapped_human_bone_count < required_human_bone_count
                ):
                    issues.append(
                        f"{slot_id}: Unity import mappedHumanBoneCount must cover requiredHumanBoneCount for humanoid score >=3"
                    )

        bounds_smoke = result.get("boundsSmoke")
        if not isinstance(bounds_smoke, dict) or bounds_smoke.get("passed") is not True:
            issues.append(f"{slot_id}: Unity import boundsSmoke.passed must be true for score >=3")
        else:
            max_dimension = bounds_smoke.get("maxDimension")
            if not isinstance(max_dimension, (int, float)) or max_dimension <= 0:
                issues.append(f"{slot_id}: Unity import maxDimension must be > 0 for score >=3")
            else:
                severe_limit = UNITY_MAX_DIMENSION_SEVERE_LIMITS.get(category)
                if severe_limit is not None and max_dimension > severe_limit:
                    issues.append(
                        f"{slot_id}: Unity import maxDimension {max_dimension:g} exceeds {category} severe limit {severe_limit:g}"
                    )
            bounds_height = bounds_smoke.get("boundsHeight")
            if not isinstance(bounds_height, (int, float)) or bounds_height <= 0:
                issues.append(f"{slot_id}: Unity import boundsHeight must be > 0 for score >=3")

    model_importer = result.get("modelImporter")
    if not isinstance(model_importer, dict) or model_importer.get("available") is not True:
        issues.append(f"{slot_id}: Unity ModelImporter metadata must be available")

    return issues


def unity_import_scale_warnings(
    slot_id: str,
    category: Any,
    evidence: dict[str, Any],
    evidence_root: Path,
) -> list[str]:
    if evidence_status(evidence.get("unityImport")) != "pass":
        return []
    if not isinstance(category, str):
        return []

    warning_limit = UNITY_MAX_DIMENSION_WARNING_LIMITS.get(category)
    if warning_limit is None:
        return []

    unity_import_path = evidence_root / "evidence" / slot_id / "unity-import.json"
    if not unity_import_path.is_file():
        return []

    try:
        payload = json.loads(unity_import_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    bounds_smoke = result.get("boundsSmoke")
    if not isinstance(bounds_smoke, dict):
        return []
    max_dimension = bounds_smoke.get("maxDimension")
    if not isinstance(max_dimension, (int, float)):
        return []
    if max_dimension <= warning_limit:
        return []

    return [
        f"{slot_id}: Unity import maxDimension {max_dimension:g} exceeds {category} warning limit {warning_limit:g}"
    ]


def unity_import_animator_migration_warnings(
    slot_id: str,
    category: Any,
    score: Any,
    evidence: dict[str, Any],
    evidence_root: Path,
) -> list[str]:
    if category != "humanoid":
        return []
    if not isinstance(score, int) or score < 3:
        return []
    if evidence_status(evidence.get("unityImport")) != "pass":
        return []

    unity_import_path = evidence_root / "evidence" / slot_id / "unity-import.json"
    if not unity_import_path.is_file():
        return []

    try:
        payload = json.loads(unity_import_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    if "configuredAnimatorSmoke" in result:
        return []
    return [f"{slot_id}: Unity import configuredAnimatorSmoke is not recorded yet"]


def unity_import_humanoid_avatar_migration_warnings(
    slot_id: str,
    category: Any,
    score: Any,
    evidence: dict[str, Any],
    evidence_root: Path,
) -> list[str]:
    if category != "humanoid":
        return []
    if not isinstance(score, int) or score < 3:
        return []
    if evidence_status(evidence.get("unityImport")) != "pass":
        return []

    unity_import_path = evidence_root / "evidence" / slot_id / "unity-import.json"
    if not unity_import_path.is_file():
        return []

    try:
        payload = json.loads(unity_import_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    if "humanoidAvatarSmoke" in result:
        return []
    return [f"{slot_id}: Unity import humanoidAvatarSmoke is not recorded yet"]


def humanoid_quality_issue_for_score(
    slot_id: str,
    category: Any,
    humanoid_diagnostics: object,
) -> str | None:
    if category != "humanoid":
        return None
    if not isinstance(humanoid_diagnostics, dict):
        return f"{slot_id}: humanoidDiagnostics summary is required for humanoid score >=3"
    status = humanoid_diagnostics.get("status")
    if status == "pass":
        return None
    warnings = humanoid_diagnostics.get("warnings")
    warning_suffix = ""
    if isinstance(warnings, list) and warnings:
        warning_suffix = f" ({','.join(str(warning) for warning in warnings)})"
    if status in {"warn", "fail"}:
        return f"{slot_id}: humanoidDiagnostics.status={status} is not allowed for score >=3{warning_suffix}"
    return f"{slot_id}: humanoidDiagnostics.status must be pass for humanoid score >=3"


def score_quality_support_issues(
    slot_id: str,
    score: Any,
    evidence: dict[str, Any],
) -> list[str]:
    if not isinstance(score, int) or score < 3:
        return []

    if evidence_status(evidence.get("unityImport")) == "pass" or evidence_status(evidence.get("unrealImport")) == "pass":
        return []
    if evidence_status(evidence.get("visualReview")) == "pass":
        visual_review = evidence.get("visualReview")
        notes = visual_review.get("notes") if isinstance(visual_review, dict) else None
        if not non_empty_string(notes):
            return [f"{slot_id}: visualReview.notes is required when visualReview.status=pass supports score >=3"]
        if not (
            has_non_empty_evidence(evidence, ("previewNeutralSide",))
            and has_non_empty_evidence(evidence, ("previewPoseSide",))
        ):
            return [f"{slot_id}: side preview evidence is required when visualReview.status=pass supports score >=3"]
        return []
    return [f"{slot_id}: visualReview.status=pass or engine import pass is required for score >=3"]


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
    require_configured_animator_smoke: bool = False,
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
    if not has_non_empty_evidence(evidence, PREVIEW_EVIDENCE_KEYS):
        issues.append(f"{slot_id}: preview evidence is required")
    if not has_non_empty_evidence(evidence, ("exportUnityFbx", "exportUnrealFbx", "exportFbx")):
        issues.append(f"{slot_id}: exported FBX evidence is required")
    if not has_non_empty_evidence(evidence, ("notes", "notesPath")):
        issues.append(f"{slot_id}: review notes evidence is required")

    failure_type = evidence.get("failureType")
    if failure_type is not None and failure_type not in FAILURE_TYPES:
        issues.append(f"{slot_id}: invalid failureType {failure_type!r}")
    visual_review_status = evidence_status(evidence.get("visualReview"))
    if visual_review_status is not None and visual_review_status not in VISUAL_REVIEW_STATUSES:
        issues.append(f"{slot_id}: invalid visualReview.status {visual_review_status!r}")
    issues.extend(score_quality_support_issues(slot_id, score, evidence))

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
                PREVIEW_EVIDENCE_KEYS,
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
        issues.extend(pose_quality_issues(slot_id, slot.get("category"), score, evidence_root))
        issues.extend(
            unity_import_quality_issues(
                slot_id,
                slot.get("category"),
                score,
                evidence,
                evidence_root,
                require_configured_animator_smoke=require_configured_animator_smoke,
            )
        )

    return not issues, issues


def classify_slot(
    slot: dict[str, Any],
    *,
    evidence_root: Path,
    check_files: bool,
    require_configured_animator_smoke: bool = False,
) -> dict[str, Any]:
    complete, evidence_issues = validate_evidence(
        slot,
        evidence_root=evidence_root,
        check_files=check_files,
        require_configured_animator_smoke=require_configured_animator_smoke,
    )
    evidence = slot.get("evidence", {})
    score = evidence.get("deformationScore")
    visual_review_status = evidence_status(evidence.get("visualReview"))
    unity_status = evidence_status(evidence.get("unityImport"))
    unreal_status = evidence_status(evidence.get("unrealImport"))
    warnings: list[str] = []
    if check_files:
        warnings.extend(unity_import_scale_warnings(slot["id"], slot.get("category"), evidence, evidence_root))
        warnings.extend(
            unity_import_animator_migration_warnings(
                slot["id"],
                slot.get("category"),
                score,
                evidence,
                evidence_root,
            )
        )
        warnings.extend(
            unity_import_humanoid_avatar_migration_warnings(
                slot["id"],
                slot.get("category"),
                score,
                evidence,
                evidence_root,
            )
        )
    classified = {
        "id": slot["id"],
        "category": slot["category"],
        "hasRealAsset": slot.get("realAsset") is not None,
        "evidenceComplete": complete,
        "deformationScore": score if isinstance(score, int) else None,
        "visualReviewStatus": visual_review_status,
        "unityImportStatus": unity_status,
        "unrealImportStatus": unreal_status,
        "issues": evidence_issues,
        "warnings": warnings,
    }
    if check_files:
        diagnostics = preview_image_diagnostics(evidence, evidence_root)
        if diagnostics:
            classified["previewDiagnostics"] = diagnostics
    return classified


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
    require_configured_animator_smoke: bool = False,
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
                classify_slot(
                    slot,
                    evidence_root=evidence_root,
                    check_files=check_files,
                    require_configured_animator_smoke=require_configured_animator_smoke,
                )
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
    check_files = bool(
        args.check_evidence_files
        or args.require_production_trial
        or args.require_configured_animator_smoke
    )
    try:
        report = validate_manifest(
            load_manifest(manifest_path),
            evidence_root=evidence_root,
            check_files=check_files,
            require_configured_animator_smoke=args.require_configured_animator_smoke,
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
    if args.require_configured_animator_smoke:
        strict_issues = [
            issue
            for slot in report["slots"]
            for issue in slot.get("issues", [])
            if "configuredAnimatorSmoke is required" in issue
        ]
        if strict_issues:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
