#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = REPO_ROOT / "addon"

UNITY_EXPORT_WARNING_MAX_DIMENSIONS = {
    "humanoid": 10.0,
    "quadruped": 12.0,
    "tail creature": 30.0,
    "wing creature": 30.0,
    "prop": 5.0,
}
UNITY_EXPORT_SEVERE_MAX_DIMENSIONS = {
    "humanoid": 100.0,
    "quadruped": 120.0,
    "tail creature": 300.0,
    "wing creature": 300.0,
    "prop": 50.0,
}
UNITY_EXPORT_TARGET_HEADROOM_RATIO = 0.95
NON_EXPORT_COLLECTION_NAMES = frozenset({"glTF_not_exported"})


def humanoid_landmarks_from_bbox(bbox: dict[str, float]) -> dict[str, tuple[float, float, float]]:
    min_x = bbox["min_x"]
    max_x = bbox["max_x"]
    min_y = bbox["min_y"]
    max_y = bbox["max_y"]
    min_z = bbox["min_z"]
    max_z = bbox["max_z"]
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    width = max(max_x - min_x, 0.1)
    depth = max(max_y - min_y, 0.1)
    height = max(max_z - min_z, 0.1)
    arm_lateral_axis = "y" if depth > (width * 1.5) else "x"
    arm_lateral_extent = depth if arm_lateral_axis == "y" else width
    leg_forward_extent = width if arm_lateral_axis == "y" else depth

    def z(factor: float) -> float:
        return min_z + (height * factor)

    def arm_landmark(lateral_factor: float, z_factor: float) -> tuple[float, float, float]:
        if arm_lateral_axis == "y":
            return (
                center_x,
                center_y + (arm_lateral_extent * lateral_factor),
                z(z_factor),
            )
        return (
            center_x + (width * lateral_factor),
            center_y,
            z(z_factor),
        )

    def leg_landmark(lateral_factor: float, z_factor: float, forward_factor: float = 0.0) -> tuple[float, float, float]:
        return (
            center_x + (width * lateral_factor),
            center_y - (leg_forward_extent * forward_factor),
            z(z_factor),
        )

    return {
        "hips": (center_x, center_y, z(0.48)),
        "spine": (center_x, center_y, z(0.58)),
        "chest": (center_x, center_y, z(0.70)),
        "neck": (center_x, center_y, z(0.84)),
        "head": (center_x, center_y, z(0.95)),
        "hip.L": leg_landmark(0.12, 0.48),
        "hip.R": leg_landmark(-0.12, 0.48),
        "shoulder.L": arm_landmark(0.34, 0.75),
        "upper_arm.L": arm_landmark(0.22, 0.73),
        "lower_arm.L": arm_landmark(0.38, 0.72),
        "hand.L": arm_landmark(0.48, 0.71),
        "shoulder.R": arm_landmark(-0.34, 0.75),
        "upper_arm.R": arm_landmark(-0.22, 0.73),
        "lower_arm.R": arm_landmark(-0.38, 0.72),
        "hand.R": arm_landmark(-0.48, 0.71),
        "upper_leg.L": leg_landmark(0.22, 0.29),
        "lower_leg.L": leg_landmark(0.22, 0.14),
        "foot.L": leg_landmark(0.22, 0.03, 0.12),
        "toe.L": leg_landmark(0.22, 0.03, 0.35),
        "upper_leg.R": leg_landmark(-0.22, 0.29),
        "lower_leg.R": leg_landmark(-0.22, 0.14),
        "foot.R": leg_landmark(-0.22, 0.03, 0.12),
        "toe.R": leg_landmark(-0.22, 0.03, 0.35),
    }


def quadruped_landmarks_from_bbox(bbox: dict[str, float]) -> dict[str, tuple[float, float, float]]:
    min_x = bbox["min_x"]
    max_x = bbox["max_x"]
    min_y = bbox["min_y"]
    max_y = bbox["max_y"]
    min_z = bbox["min_z"]
    max_z = bbox["max_z"]
    center_x = (min_x + max_x) / 2.0
    width = max(max_x - min_x, 0.1)
    depth = max(max_y - min_y, 0.1)
    height = max(max_z - min_z, 0.1)

    def x(factor: float) -> float:
        return center_x + (width * factor)

    def y(factor: float) -> float:
        return min_y + (depth * factor)

    def z(factor: float) -> float:
        return min_z + (height * factor)

    def leg(side_factor: float, body_factor: float, height_factor: float) -> tuple[float, float, float]:
        return (x(side_factor), y(body_factor), z(height_factor))

    return {
        "pelvis": (center_x, y(0.66), z(0.58)),
        "spine": (center_x, y(0.52), z(0.64)),
        "chest": (center_x, y(0.36), z(0.66)),
        "neck": (center_x, y(0.24), z(0.73)),
        "head": (center_x, y(0.14), z(0.76)),
        "muzzle": (center_x, y(0.05), z(0.70)),
        "front_leg.L": leg(0.22, 0.34, 0.46),
        "front_knee.L": leg(0.22, 0.35, 0.28),
        "front_ankle.L": leg(0.22, 0.36, 0.12),
        "front_paw.L": leg(0.22, 0.31, 0.03),
        "front_leg.R": leg(-0.22, 0.34, 0.46),
        "front_knee.R": leg(-0.22, 0.35, 0.28),
        "front_ankle.R": leg(-0.22, 0.36, 0.12),
        "front_paw.R": leg(-0.22, 0.31, 0.03),
        "rear_leg.L": leg(0.22, 0.66, 0.46),
        "rear_knee.L": leg(0.22, 0.67, 0.28),
        "rear_ankle.L": leg(0.22, 0.68, 0.12),
        "rear_paw.L": leg(0.22, 0.61, 0.03),
        "rear_leg.R": leg(-0.22, 0.66, 0.46),
        "rear_knee.R": leg(-0.22, 0.67, 0.28),
        "rear_ankle.R": leg(-0.22, 0.68, 0.12),
        "rear_paw.R": leg(-0.22, 0.61, 0.03),
        "tail_base": (center_x, y(0.72), z(0.58)),
        "tail_mid": (center_x, y(0.88), z(0.56)),
        "tail_tip": (center_x, y(1.00), z(0.52)),
    }


def tail_creature_landmarks_from_bbox(bbox: dict[str, float]) -> dict[str, tuple[float, float, float]]:
    min_x = bbox["min_x"]
    max_x = bbox["max_x"]
    min_y = bbox["min_y"]
    max_y = bbox["max_y"]
    min_z = bbox["min_z"]
    max_z = bbox["max_z"]
    center_x = (min_x + max_x) / 2.0
    width = max(max_x - min_x, 0.1)
    depth = max(max_y - min_y, 0.1)
    height = max(max_z - min_z, 0.1)

    def x(factor: float) -> float:
        return center_x + (width * factor)

    def y(factor: float) -> float:
        return min_y + (depth * factor)

    def z(factor: float) -> float:
        return min_z + (height * factor)

    def leg(side_factor: float, body_factor: float, height_factor: float) -> tuple[float, float, float]:
        return (x(side_factor), y(body_factor), z(height_factor))

    return {
        "pelvis": (center_x, y(0.60), z(0.42)),
        "spine": (center_x, y(0.48), z(0.50)),
        "chest": (center_x, y(0.34), z(0.56)),
        "neck_base": (center_x, y(0.24), z(0.66)),
        "neck_mid": (center_x, y(0.14), z(0.84)),
        "head": (center_x, y(0.07), z(0.88)),
        "muzzle": (center_x, y(0.02), z(0.82)),
        "front_leg.L": leg(0.18, 0.34, 0.36),
        "front_knee.L": leg(0.18, 0.35, 0.22),
        "front_ankle.L": leg(0.18, 0.36, 0.10),
        "front_paw.L": leg(0.18, 0.31, 0.03),
        "front_leg.R": leg(-0.18, 0.34, 0.36),
        "front_knee.R": leg(-0.18, 0.35, 0.22),
        "front_ankle.R": leg(-0.18, 0.36, 0.10),
        "front_paw.R": leg(-0.18, 0.31, 0.03),
        "rear_leg.L": leg(0.18, 0.60, 0.34),
        "rear_knee.L": leg(0.18, 0.62, 0.21),
        "rear_ankle.L": leg(0.18, 0.64, 0.10),
        "rear_paw.L": leg(0.18, 0.58, 0.03),
        "rear_leg.R": leg(-0.18, 0.60, 0.34),
        "rear_knee.R": leg(-0.18, 0.62, 0.21),
        "rear_ankle.R": leg(-0.18, 0.64, 0.10),
        "rear_paw.R": leg(-0.18, 0.58, 0.03),
        "tail_base": (center_x, y(0.66), z(0.42)),
        "tail_mid": (center_x, y(0.82), z(0.34)),
        "tail_tip": (center_x, y(0.98), z(0.24)),
    }


def prop_hinge_landmarks_from_bbox(
    bbox: dict[str, float],
    *,
    hinge_pivot_x: float = 0.16,
    base_origin_x: float = 0.28,
    layout_axis: str = "x",
) -> dict[str, tuple[float, float, float]]:
    min_x = bbox["min_x"]
    max_x = bbox["max_x"]
    min_y = bbox["min_y"]
    max_y = bbox["max_y"]
    min_z = bbox["min_z"]
    max_z = bbox["max_z"]
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    width = max(max_x - min_x, 0.1)
    depth = max(max_y - min_y, 0.1)
    height = max(max_z - min_z, 0.1)
    hinge_z = min_z + (height * 0.5)
    moving_part_x = max(hinge_pivot_x + 0.08, 0.45)
    axis = normalized_prop_hinge_axis(layout_axis)

    if axis == "y":
        moving_part_y = max(hinge_pivot_x + 0.08, 0.45)
        return {
            "base": rounded_tuple((center_x, min_y + (depth * base_origin_x), min_z + (height * 0.16))),
            "hinge": rounded_tuple((center_x, min_y + (depth * hinge_pivot_x), hinge_z)),
            "moving_part": rounded_tuple((center_x, min_y + (depth * moving_part_y), hinge_z)),
            "moving_tip": rounded_tuple((center_x, max_y - (depth * 0.08), hinge_z)),
        }

    return {
        "base": rounded_tuple((min_x + (width * base_origin_x), center_y, min_z + (height * 0.16))),
        "hinge": rounded_tuple((min_x + (width * hinge_pivot_x), center_y, hinge_z)),
        "moving_part": rounded_tuple((min_x + (width * moving_part_x), center_y, hinge_z)),
        "moving_tip": rounded_tuple((max_x - (width * 0.08), center_y, hinge_z)),
    }


def normalized_prop_hinge_axis(value: str) -> str:
    axis = (value or "x").strip().lower()
    if axis not in {"x", "y"}:
        raise ValueError(f"Unsupported prop hinge axis: {value}")
    return axis


def rounded_tuple(point: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(float(value), 4) for value in point)


def landmarks_from_bbox(
    template: str,
    bbox: dict[str, float],
    *,
    prop_hinge_pivot_x: float = 0.16,
    prop_hinge_base_x: float = 0.28,
    prop_hinge_axis: str = "x",
) -> dict[str, tuple[float, float, float]]:
    if template == "humanoid":
        return humanoid_landmarks_from_bbox(bbox)
    if template == "quadruped":
        return quadruped_landmarks_from_bbox(bbox)
    if template == "tail_creature":
        return tail_creature_landmarks_from_bbox(bbox)
    if template == "prop_hinge":
        return prop_hinge_landmarks_from_bbox(
            bbox,
            hinge_pivot_x=prop_hinge_pivot_x,
            base_origin_x=prop_hinge_base_x,
            layout_axis=prop_hinge_axis,
        )
    raise ValueError(f"Unsupported workflow template: {template}")


def workflow_controls_summary(
    template: str,
    *,
    prop_hinge_pivot_x: float,
    prop_hinge_base_x: float,
    prop_hinge_axis: str = "x",
) -> dict[str, Any]:
    if template != "prop_hinge":
        return {}
    return {
        "propHinge": {
            "pivotX": round(float(prop_hinge_pivot_x), 4),
            "baseX": round(float(prop_hinge_base_x), 4),
            "axis": normalized_prop_hinge_axis(prop_hinge_axis),
        }
    }


def pose_preview_operator_name(template: str = "humanoid") -> str:
    if template == "humanoid":
        return "pose_humanoid_stress"
    if template == "quadruped":
        return "pose_quadruped_gait"
    if template == "tail_creature":
        return "pose_tail_creature_reach"
    if template == "prop_hinge":
        return "pose_prop_hinge_open"
    raise ValueError(f"Unsupported workflow template: {template}")


def side_pose_preview_operator_name(template: str = "humanoid") -> str:
    if template == "humanoid":
        return "pose_humanoid_side_review"
    if template == "quadruped":
        return "pose_quadruped_side_review"
    if template == "tail_creature":
        return "pose_tail_creature_side_review"
    if template == "prop_hinge":
        return "pose_prop_hinge_side_review"
    raise ValueError(f"Unsupported workflow template: {template}")


def preview_material_name() -> str:
    return "MGR_Evidence_Preview_Material"


def preview_artifact_paths(evidence_dir: Path) -> dict[str, Path]:
    return {
        "neutral_front": evidence_dir / "preview-neutral.png",
        "pose_front": evidence_dir / "preview-pose.png",
        "neutral_side": evidence_dir / "preview-neutral-side.png",
        "pose_side": evidence_dir / "preview-pose-side.png",
    }


def preview_artifact_summary(paths: dict[str, Path]) -> dict[str, str]:
    return {
        "previewNeutral": str(paths["neutral_front"]),
        "previewPose": str(paths["pose_front"]),
        "previewNeutralSide": str(paths["neutral_side"]),
        "previewPoseSide": str(paths["pose_side"]),
    }


def unity_export_scale_category(template: str) -> str:
    if template == "humanoid":
        return "humanoid"
    if template == "quadruped":
        return "quadruped"
    if template == "tail_creature":
        return "tail creature"
    if template == "prop_hinge":
        return "prop"
    raise ValueError(f"Unsupported workflow template: {template}")


def bbox_max_dimension(bbox: dict[str, float]) -> float:
    return max(
        _bbox_axis_size(bbox, "x"),
        _bbox_axis_size(bbox, "y"),
        _bbox_axis_size(bbox, "z"),
    )


def unity_export_scale_normalization_plan(
    template: str,
    bbox: dict[str, float],
) -> dict[str, Any]:
    category = unity_export_scale_category(template)
    source_max_dimension = round(bbox_max_dimension(bbox), 4)
    target_max_dimension = round(
        UNITY_EXPORT_WARNING_MAX_DIMENSIONS[category] * UNITY_EXPORT_TARGET_HEADROOM_RATIO,
        4,
    )
    severe_max_dimension = UNITY_EXPORT_SEVERE_MAX_DIMENSIONS[category]
    if source_max_dimension <= severe_max_dimension:
        return {
            "applied": False,
            "category": category,
            "sourceMaxDimension": source_max_dimension,
            "targetMaxDimension": target_max_dimension,
            "scaleFactor": 1.0,
            "reason": "withinSevereLimit",
        }
    return {
        "applied": True,
        "category": category,
        "sourceMaxDimension": source_max_dimension,
        "targetMaxDimension": target_max_dimension,
        "scaleFactor": round(target_max_dimension / source_max_dimension, 6),
        "reason": "severeScaleNormalization",
    }


def apply_unity_export_scale_normalization(
    bpy_module,
    template: str,
) -> dict[str, Any]:
    bbox = mesh_bbox(bpy_module)
    plan = unity_export_scale_normalization_plan(template, bbox)
    if not plan["applied"]:
        return plan

    scale_factor = float(plan["scaleFactor"])
    for obj in bpy_module.context.scene.objects:
        if obj.type not in {"MESH", "ARMATURE"}:
            continue
        obj.scale = tuple(round(float(component) * scale_factor, 6) for component in obj.scale)

    view_layer = getattr(bpy_module.context, "view_layer", None)
    update = getattr(view_layer, "update", None)
    if callable(update):
        update()

    return plan


def side_preview_axis(front_axis: str) -> str:
    if front_axis == "x":
        return "y"
    if front_axis == "y":
        return "x"
    raise ValueError(f"Unsupported camera axis: {front_axis}")


def pose_deformation_summary(
    neutral_bbox: dict[str, float],
    pose_bbox: dict[str, float],
    *,
    template: str = "humanoid",
) -> dict[str, Any]:
    axis_ratios = {
        axis: _bbox_axis_size(pose_bbox, axis) / _bbox_axis_size(neutral_bbox, axis)
        for axis in ("x", "y", "z")
    }
    allowed_expanded_axes = {"y"} if template == "prop_hinge" else set()
    expanded_axes = [
        axis
        for axis, ratio in axis_ratios.items()
        if ratio > 4.0 and axis not in allowed_expanded_axes
    ]
    warn_axes = [
        axis
        for axis, ratio in axis_ratios.items()
        if 2.5 < ratio <= 4.0 and axis not in allowed_expanded_axes
    ]
    status = "fail" if expanded_axes else "warn" if warn_axes else "pass"
    return {
        "status": status,
        "axisExpansionRatios": {
            axis: round(ratio, 4)
            for axis, ratio in axis_ratios.items()
        },
        "maxAxisExpansionRatio": round(max(axis_ratios.values()), 4),
        "expandedAxes": expanded_axes,
        "warningAxes": warn_axes,
        "allowedExpandedAxes": sorted(
            axis for axis in allowed_expanded_axes if axis_ratios.get(axis, 0.0) > 1.0
        ),
    }


def _bbox_axis_size(bbox: dict[str, float], axis: str) -> float:
    return max(bbox[f"max_{axis}"] - bbox[f"min_{axis}"], 0.1)


def cleanup_summary_from_scene(scene) -> dict[str, int]:
    message = getattr(scene, "mgr_weight_cleanup_message", "")
    pairs = dict(
        item.split("=", 1)
        for item in message.split()
        if "=" in item
    )
    removed_names = [
        name
        for name in getattr(scene, "mgr_removed_empty_group_names", "").split(",")
        if name
    ]
    return {
        "unweightedVertices": int(pairs.get("unweighted", 0)),
        "overLimitVertices": int(pairs.get("over_limit", 0)),
        "removedEmptyGroups": int(pairs.get("removed_empty", 0)),
        "removedEmptyGroupNames": removed_names,
        "prunedWeights": int(pairs.get("pruned", 0)),
        "normalizedVertices": int(pairs.get("normalized", 0)),
    }


def apply_capsule_weights_to_mesh_collection(
    meshes,
    armature,
    *,
    bind_func,
) -> dict[str, Any]:
    weighted_vertices = 0
    mesh_names = []
    for mesh in meshes:
        result = bind_func(mesh, armature)
        weighted_vertices += result.weighted_vertices
        mesh_names.append(mesh.name)
    return {
        "meshCount": len(mesh_names),
        "weightedVertices": weighted_vertices,
        "meshNames": mesh_names,
    }


def cleanup_mesh_collection(
    meshes,
    *,
    cleanup_func,
) -> dict[str, Any]:
    totals: dict[str, Any] = {
        "unweightedVertices": 0,
        "overLimitVertices": 0,
        "removedEmptyGroups": 0,
        "removedEmptyGroupNames": [],
        "prunedWeights": 0,
        "normalizedVertices": 0,
    }
    for mesh in meshes:
        result = cleanup_func(mesh)
        totals["unweightedVertices"] += result.unweighted_vertices
        totals["overLimitVertices"] += result.over_limit_vertices
        totals["removedEmptyGroups"] += result.removed_empty_groups
        totals["removedEmptyGroupNames"].extend(result.removed_empty_group_names)
        totals["prunedWeights"] += result.pruned_weights
        totals["normalizedVertices"] += result.normalized_vertices
    return totals


def weight_region_for_bone(bone_name: str) -> str:
    if bone_name == "PropBase":
        return "propBase"
    if bone_name == "Hinge":
        return "propHinge"
    if bone_name == "MovingPart":
        return "propMovingPart"
    if bone_name in {"Neck", "Head"}:
        return "neckHead"
    if bone_name in {"Hips", "Spine", "Chest"}:
        return "core"
    if "UpperArm" in bone_name or "Shoulder" in bone_name:
        return "upperArm"
    if "LowerArm" in bone_name:
        return "lowerArm"
    if "Hand" in bone_name:
        return "hand"
    if "UpperLeg" in bone_name:
        return "upperLeg"
    if "LowerLeg" in bone_name:
        return "lowerLeg"
    if "Foot" in bone_name or "Toe" in bone_name or "Paw" in bone_name or "Ankle" in bone_name:
        return "foot"
    if "Tail" in bone_name:
        return "tail"
    return "other"


def weight_region_summary(meshes: list[Any]) -> dict[str, Any]:
    regions: dict[str, dict[str, float | int]] = {}
    bone_totals: dict[str, float] = {}
    height_band_records: list[tuple[float, str]] = []
    vertex_count = 0

    for mesh in meshes:
        group_names = {
            vertex_group.index: vertex_group.name
            for vertex_group in mesh.vertex_groups
        }
        for vertex in mesh.data.vertices:
            vertex_count += 1
            region_weights: dict[str, float] = {}
            for group in vertex.groups:
                if group.weight <= 0.0:
                    continue
                bone_name = group_names.get(group.group, f"group:{group.group}")
                region = weight_region_for_bone(bone_name)
                region_weights[region] = region_weights.get(region, 0.0) + group.weight
                bone_totals[bone_name] = bone_totals.get(bone_name, 0.0) + group.weight

            if not region_weights:
                continue

            dominant_region = max(region_weights.items(), key=lambda item: item[1])[0]
            vertex_z = vertex_world_z(mesh, vertex)
            if vertex_z is not None:
                height_band_records.append((vertex_z, dominant_region))
            for region, weight in region_weights.items():
                region_summary = regions.setdefault(
                    region,
                    {
                        "influencedVertices": 0,
                        "dominantVertices": 0,
                        "totalWeight": 0.0,
                    },
                )
                region_summary["influencedVertices"] += 1
                region_summary["totalWeight"] += weight
                if region == dominant_region:
                    region_summary["dominantVertices"] += 1

    visible_regions = {}
    for region, summary in regions.items():
        influenced_vertices = int(summary["influencedVertices"])
        average_weight = (
            float(summary["totalWeight"]) / influenced_vertices
            if influenced_vertices
            else 0.0
        )
        visible_regions[region] = {
            "influencedVertices": influenced_vertices,
            "dominantVertices": int(summary["dominantVertices"]),
            "averageWeight": round(average_weight, 4),
        }

    return {
        "meshCount": len(meshes),
        "vertexCount": vertex_count,
        "regions": visible_regions,
        "heightBands": height_band_summary(height_band_records),
        "topBones": [
            {"bone": bone_name, "totalWeight": round(total_weight, 4)}
            for bone_name, total_weight in sorted(
                bone_totals.items(),
                key=lambda item: (-item[1], item[0]),
            )[:12]
        ],
    }


def prop_diagnostics_summary(weight_diagnostics: dict[str, Any], *, template: str) -> dict[str, Any]:
    if template != "prop_hinge":
        return {}

    vertex_count = int(weight_diagnostics.get("vertexCount") or 0)
    regions = weight_diagnostics.get("regions")
    if vertex_count <= 0 or not isinstance(regions, dict):
        return {
            "status": "fail",
            "coverageRatios": {},
            "warnings": ["missingPropWeightDiagnostics"],
        }

    def dominant_ratio(region_name: str) -> float:
        region = regions.get(region_name)
        if not isinstance(region, dict):
            return 0.0
        dominant = region.get("dominantVertices")
        if not isinstance(dominant, int):
            return 0.0
        return dominant / vertex_count

    ratios = {
        "propBase": round(dominant_ratio("propBase"), 4),
        "propHinge": round(dominant_ratio("propHinge"), 4),
        "propMovingPart": round(dominant_ratio("propMovingPart"), 4),
    }
    warnings = []
    fail_codes = []
    if ratios["propBase"] <= 0.0:
        fail_codes.append("missingPropBaseCoverage")
    if ratios["propHinge"] <= 0.0:
        fail_codes.append("missingPropHingeCoverage")
    if ratios["propMovingPart"] <= 0.0:
        fail_codes.append("missingPropMovingPartCoverage")

    if not fail_codes:
        if ratios["propBase"] < 0.10:
            warnings.append("weakPropBaseCoverage")
        if ratios["propHinge"] < 0.01:
            warnings.append("weakPropHingeCoverage")
        if ratios["propMovingPart"] < 0.25:
            warnings.append("weakPropMovingPartCoverage")

    if fail_codes:
        status = "fail"
        warnings = fail_codes
    elif warnings:
        status = "warn"
    else:
        status = "pass"

    return {
        "status": status,
        "coverageRatios": ratios,
        "warnings": warnings,
    }


def humanoid_diagnostics_summary(weight_diagnostics: dict[str, Any], *, template: str) -> dict[str, Any]:
    if template != "humanoid":
        return {}

    vertex_count = int(weight_diagnostics.get("vertexCount") or 0)
    regions = weight_diagnostics.get("regions")
    if vertex_count <= 0 or not isinstance(regions, dict):
        return {
            "status": "fail",
            "coverageRatios": {},
            "warnings": ["missingHumanoidWeightDiagnostics"],
        }

    def dominant_ratio(region_name: str) -> float:
        region = regions.get(region_name)
        if not isinstance(region, dict):
            return 0.0
        dominant = region.get("dominantVertices")
        if not isinstance(dominant, int):
            return 0.0
        return dominant / vertex_count

    arm_ratio = (
        dominant_ratio("upperArm")
        + dominant_ratio("lowerArm")
        + dominant_ratio("hand")
    )
    leg_ratio = dominant_ratio("upperLeg") + dominant_ratio("lowerLeg")
    ratios = {
        "core": round(dominant_ratio("core"), 4),
        "arm": round(arm_ratio, 4),
        "leg": round(leg_ratio, 4),
        "foot": round(dominant_ratio("foot"), 4),
    }
    warnings = []
    if ratios["foot"] < 0.025:
        warnings.append("weakHumanoidFootCoverage")

    return {
        "status": "warn" if warnings else "pass",
        "coverageRatios": ratios,
        "warnings": warnings,
    }


def bone_weight_diagnostics(
    meshes: list[Any],
    *,
    sample_limit: int = 4,
    point_resolver=None,
    point_key: str = "world",
) -> dict[str, Any]:
    bones: dict[str, dict[str, Any]] = {}
    vertex_count = 0
    sample_limit = max(0, int(sample_limit))
    if point_resolver is None:
        point_resolver = vertex_world_point

    for mesh in meshes:
        group_names = {
            vertex_group.index: vertex_group.name
            for vertex_group in mesh.vertex_groups
        }
        for vertex_index, vertex in enumerate(mesh.data.vertices):
            vertex_count += 1
            bone_weights: dict[str, float] = {}
            for group in vertex.groups:
                if group.weight <= 0.0:
                    continue
                bone_name = group_names.get(group.group, f"group:{group.group}")
                bone_weights[bone_name] = bone_weights.get(bone_name, 0.0) + float(group.weight)

            if not bone_weights:
                continue

            dominant_bone = max(bone_weights.items(), key=lambda item: (item[1], item[0]))[0]
            point = point_resolver(mesh, vertex)
            sample_index = int(getattr(vertex, "index", vertex_index))

            for bone_name, weight in bone_weights.items():
                bone_summary = bones.setdefault(
                    bone_name,
                    {
                        "region": weight_region_for_bone(bone_name),
                        "influencedVertices": 0,
                        "dominantVertices": 0,
                        "totalWeight": 0.0,
                        "_influencedPoints": [],
                        "_dominantPoints": [],
                        "_samples": [],
                    },
                )
                bone_summary["influencedVertices"] += 1
                bone_summary["totalWeight"] += weight
                if point is not None:
                    bone_summary["_influencedPoints"].append(point)
                if bone_name == dominant_bone:
                    bone_summary["dominantVertices"] += 1
                    if point is not None:
                        bone_summary["_dominantPoints"].append(point)

                sample = {
                    "mesh": str(mesh.name),
                    "index": sample_index,
                    "weight": round(weight, 4),
                }
                if point is not None:
                    sample[point_key] = rounded_point(point)
                bone_summary["_samples"].append(sample)

    visible_bones: dict[str, dict[str, Any]] = {}
    for bone_name, summary in sorted(bones.items()):
        influenced_vertices = int(summary["influencedVertices"])
        total_weight = float(summary["totalWeight"])
        samples = sorted(
            summary["_samples"],
            key=lambda sample: (-float(sample["weight"]), str(sample["mesh"]), int(sample["index"])),
        )[:sample_limit]
        visible_bones[bone_name] = {
            "region": str(summary["region"]),
            "influencedVertices": influenced_vertices,
            "dominantVertices": int(summary["dominantVertices"]),
            "totalWeight": round(total_weight, 4),
            "averageWeight": round(total_weight / influenced_vertices, 4)
            if influenced_vertices
            else 0.0,
            "influencedBounds": point_bounds(summary["_influencedPoints"]),
            "dominantBounds": point_bounds(summary["_dominantPoints"]),
            "topWeightedVertices": samples,
        }

    return {
        "meshCount": len(meshes),
        "vertexCount": vertex_count,
        "bones": visible_bones,
        "topBones": [
            {"bone": bone_name, "totalWeight": round(float(summary["totalWeight"]), 4)}
            for bone_name, summary in sorted(
                bones.items(),
                key=lambda item: (-float(item[1]["totalWeight"]), item[0]),
            )[:12]
        ],
    }


def capsule_bind_weight_diagnostics(
    meshes: list[Any],
    capsules: list[dict[str, Any]],
    *,
    sample_limit: int = 4,
) -> dict[str, Any]:
    target_bounds = capsule_target_bounds(capsules)
    if target_bounds is None:
        return {
            "space": "capsuleBind",
            "meshCount": len(meshes),
            "vertexCount": 0,
            "targetBounds": None,
            "bones": {},
            "topBones": [],
        }

    mesh_bind_vertex_points = load_weight_binding_core().mesh_bind_vertex_points
    bind_points_by_mesh = {
        str(mesh.name): mesh_bind_vertex_points(mesh, target_bounds=target_bounds)
        for mesh in meshes
    }

    def bind_point(mesh: Any, vertex: Any) -> Any | None:
        mesh_points = bind_points_by_mesh.get(str(mesh.name), {})
        return mesh_points.get(int(getattr(vertex, "index", -1)))

    summary = bone_weight_diagnostics(
        meshes,
        sample_limit=sample_limit,
        point_resolver=bind_point,
        point_key="bind",
    )
    return {
        "space": "capsuleBind",
        "targetBounds": bounds_summary(target_bounds),
        **summary,
    }


def capsule_assignment_diagnostics(
    meshes: list[Any],
    capsules: list[dict[str, Any]],
    *,
    sample_limit: int = 4,
) -> dict[str, Any]:
    target_bounds = capsule_target_bounds(capsules)
    if target_bounds is None:
        return {
            "space": "capsuleBind",
            "meshCount": len(meshes),
            "vertexCount": 0,
            "targetBounds": None,
            "capsuleAssignedVertices": 0,
            "nearestFallbackVertices": 0,
            "fallbackByBone": {},
        }

    weight_binding_core = load_weight_binding_core()
    mesh_bind_vertex_points = weight_binding_core.mesh_bind_vertex_points
    assignment_details = weight_binding_core.capsule_assignment_details
    max_influences = int(getattr(weight_binding_core, "MAX_VERTEX_INFLUENCES", 4))
    sample_limit = max(0, int(sample_limit))

    vertex_count = 0
    capsule_assigned = 0
    fallback_assigned = 0
    fallback_by_bone: dict[str, dict[str, Any]] = {}
    for mesh in meshes:
        bind_points = mesh_bind_vertex_points(mesh, target_bounds=target_bounds)
        for vertex_index, vertex in enumerate(mesh.data.vertices):
            vertex_count += 1
            sample_index = int(getattr(vertex, "index", vertex_index))
            point = bind_points.get(sample_index)
            if point is None:
                continue
            details = assignment_details(point, capsules, max_influences)
            if details.get("mode") != "nearestFallback":
                capsule_assigned += 1
                continue

            fallback_assigned += 1
            bone_name = str(details.get("nearestBone"))
            distance = float(details.get("nearestDistance") or 0.0)
            distance_ratio_value = details.get("nearestDistanceRatio")
            distance_ratio = (
                float(distance_ratio_value)
                if distance_ratio_value is not None
                else 0.0
            )
            bone_summary = fallback_by_bone.setdefault(
                bone_name,
                {
                    "region": str(details.get("nearestBoneRegion") or "unknown"),
                    "vertexCount": 0,
                    "_distanceRatioTotal": 0.0,
                    "maxDistanceRatio": 0.0,
                    "_samples": [],
                },
            )
            bone_summary["vertexCount"] += 1
            bone_summary["_distanceRatioTotal"] += distance_ratio
            bone_summary["maxDistanceRatio"] = max(
                float(bone_summary["maxDistanceRatio"]),
                distance_ratio,
            )
            bone_summary["_samples"].append(
                {
                    "mesh": str(mesh.name),
                    "index": sample_index,
                    "bind": rounded_point(point),
                    "distance": round(distance, 4),
                    "distanceRatio": round(distance_ratio, 4),
                }
            )

    visible_fallback = {}
    for bone_name, summary in sorted(fallback_by_bone.items()):
        vertex_total = int(summary["vertexCount"])
        samples = sorted(
            summary["_samples"],
            key=lambda sample: (-float(sample["distanceRatio"]), str(sample["mesh"]), int(sample["index"])),
        )[:sample_limit]
        visible_fallback[bone_name] = {
            "region": str(summary["region"]),
            "vertexCount": vertex_total,
            "averageDistanceRatio": round(
                float(summary["_distanceRatioTotal"]) / vertex_total,
                4,
            ) if vertex_total else 0.0,
            "maxDistanceRatio": round(float(summary["maxDistanceRatio"]), 4),
            "samples": samples,
        }

    return {
        "space": "capsuleBind",
        "meshCount": len(meshes),
        "vertexCount": vertex_count,
        "targetBounds": bounds_summary(target_bounds),
        "capsuleAssignedVertices": capsule_assigned,
        "nearestFallbackVertices": fallback_assigned,
        "fallbackByBone": visible_fallback,
    }


def capsule_target_bounds(capsules: list[dict[str, Any]]) -> dict[str, tuple[float, float, float]] | None:
    points: list[tuple[float, float, float]] = []
    for capsule in capsules:
        radius = float(capsule["radius"])
        for endpoint_name in ("head", "tail"):
            endpoint = point_xyz(capsule[endpoint_name])
            if endpoint is None:
                continue
            points.append((endpoint[0] - radius, endpoint[1] - radius, endpoint[2] - radius))
            points.append((endpoint[0] + radius, endpoint[1] + radius, endpoint[2] + radius))
    if not points:
        return None
    return {
        "min": (
            min(point[0] for point in points),
            min(point[1] for point in points),
            min(point[2] for point in points),
        ),
        "max": (
            max(point[0] for point in points),
            max(point[1] for point in points),
            max(point[2] for point in points),
        ),
    }


def bounds_summary(bounds: dict[str, tuple[float, float, float]]) -> dict[str, float]:
    return {
        "minX": round(float(bounds["min"][0]), 4),
        "maxX": round(float(bounds["max"][0]), 4),
        "minY": round(float(bounds["min"][1]), 4),
        "maxY": round(float(bounds["max"][1]), 4),
        "minZ": round(float(bounds["min"][2]), 4),
        "maxZ": round(float(bounds["max"][2]), 4),
    }


def point_bounds(points: list[Any]) -> dict[str, float] | None:
    coordinates = [point_xyz(point) for point in points]
    coordinates = [point for point in coordinates if point is not None]
    if not coordinates:
        return None

    xs = [point[0] for point in coordinates]
    ys = [point[1] for point in coordinates]
    zs = [point[2] for point in coordinates]
    return {
        "minX": round(min(xs), 4),
        "maxX": round(max(xs), 4),
        "minY": round(min(ys), 4),
        "maxY": round(max(ys), 4),
        "minZ": round(min(zs), 4),
        "maxZ": round(max(zs), 4),
    }


def vertex_world_point(mesh: Any, vertex: Any) -> Any | None:
    if not hasattr(mesh, "matrix_world") or not hasattr(vertex, "co"):
        return None
    try:
        return mesh.matrix_world @ vertex.co
    except (TypeError, ValueError):
        return None


def vertex_world_z(mesh: Any, vertex: Any) -> float | None:
    point = vertex_world_point(mesh, vertex)
    coordinates = point_xyz(point)
    if coordinates is None:
        return None
    return coordinates[2]


def point_xyz(point: Any) -> tuple[float, float, float] | None:
    if point is None:
        return None
    if all(hasattr(point, axis) for axis in ("x", "y", "z")):
        return (float(point.x), float(point.y), float(point.z))
    try:
        return (float(point[0]), float(point[1]), float(point[2]))
    except (TypeError, IndexError, ValueError):
        return None


def height_band_summary(records: list[tuple[float, str]]) -> dict[str, dict[str, Any]]:
    bands: dict[str, dict[str, Any]] = {
        "lower": {"vertexCount": 0, "dominantRegions": {}, "minZ": None, "maxZ": None},
        "torso": {"vertexCount": 0, "dominantRegions": {}, "minZ": None, "maxZ": None},
        "upper": {"vertexCount": 0, "dominantRegions": {}, "minZ": None, "maxZ": None},
    }
    if not records:
        return bands

    min_z = min(z for z, _region in records)
    max_z = max(z for z, _region in records)
    span = max(max_z - min_z, 0.0001)

    for z, dominant_region in records:
        factor = (z - min_z) / span
        if factor < 0.33:
            band_name = "lower"
        elif factor < 0.70:
            band_name = "torso"
        else:
            band_name = "upper"
        band = bands[band_name]
        band["vertexCount"] += 1
        band["minZ"] = z if band["minZ"] is None else min(float(band["minZ"]), z)
        band["maxZ"] = z if band["maxZ"] is None else max(float(band["maxZ"]), z)
        dominant_regions = band["dominantRegions"]
        dominant_regions[dominant_region] = dominant_regions.get(dominant_region, 0) + 1

    for band in bands.values():
        if band["minZ"] is not None:
            band["minZ"] = round(float(band["minZ"]), 4)
        if band["maxZ"] is not None:
            band["maxZ"] = round(float(band["maxZ"]), 4)

    return bands


def capsule_diagnostics_summary(capsules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": str(capsule["name"]),
            "head": rounded_point(capsule["head"]),
            "tail": rounded_point(capsule["tail"]),
            "radius": round(float(capsule["radius"]), 4),
            "verticalMin": round(float(capsule["verticalMin"]), 4),
            "verticalMax": round(float(capsule["verticalMax"]), 4),
        }
        for capsule in capsules
    ]


def rounded_point(point: Any) -> list[float]:
    coordinates = point_xyz(point)
    if coordinates is None:
        return []
    return [round(float(value), 4) for value in coordinates]


def bind_space_summary(meshes: list[Any]) -> list[dict[str, Any]]:
    mesh_bind_vertex_points = load_weight_binding_core().mesh_bind_vertex_points

    summaries = []
    for mesh in meshes:
        raw_z = [float(vertex.co[2]) for vertex in mesh.data.vertices]
        bind_points = mesh_bind_vertex_points(mesh)
        bind_z = [point[2] for point in bind_points.values()]
        if not raw_z or not bind_z:
            continue
        summaries.append(
            {
                "mesh": mesh.name,
                "rawMinZ": round(min(raw_z), 4),
                "rawMaxZ": round(max(raw_z), 4),
                "bindMinZ": round(min(bind_z), 4),
                "bindMaxZ": round(max(bind_z), 4),
            }
        )
    return summaries


def load_weight_binding_core():
    module_name = "_mgr_weight_binding_core"
    if module_name in sys.modules:
        return sys.modules[module_name]
    module_path = ADDON_ROOT / "mac_game_rigger/core/weight_binding.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def orientation_normalization_plan_from_dimensions(
    dimensions: tuple[float, float, float],
) -> dict[str, str | float] | None:
    width_x, depth_y, height_z = dimensions
    if depth_y > height_z and depth_y > width_x:
        return {
            "sourceUpAxis": "y",
            "rotationAxis": "X",
            "rotationRadians": math.pi / 2,
        }
    return None


def mesh_transform_normalization_plan(
    dimensions: tuple[float, float, float],
    scale: tuple[float, float, float],
) -> dict[str, str | float | bool | None] | None:
    orientation_plan = orientation_normalization_plan_from_dimensions(dimensions)
    apply_scale = any(abs(value - 1.0) > 0.0001 for value in scale)
    if orientation_plan is None and not apply_scale:
        return None
    return {
        "sourceUpAxis": None if orientation_plan is None else orientation_plan["sourceUpAxis"],
        "rotationAxis": None if orientation_plan is None else orientation_plan["rotationAxis"],
        "rotationRadians": 0.0 if orientation_plan is None else orientation_plan["rotationRadians"],
        "applyScale": apply_scale,
    }


def scene_dimensions_from_bbox(bbox: dict[str, float]) -> tuple[float, float, float]:
    return (
        bbox["max_x"] - bbox["min_x"],
        bbox["max_y"] - bbox["min_y"],
        bbox["max_z"] - bbox["min_z"],
    )


def camera_plan_from_bbox(
    bbox: dict[str, float],
    *,
    axis: str = "y",
) -> dict[str, tuple[float, float, float] | float]:
    center_x = (bbox["min_x"] + bbox["max_x"]) / 2.0
    center_y = (bbox["min_y"] + bbox["max_y"]) / 2.0
    center_z = (bbox["min_z"] + bbox["max_z"]) / 2.0
    height = max(bbox["max_z"] - bbox["min_z"], 0.1)
    width = max(bbox["max_x"] - bbox["min_x"], 0.1)
    depth = max(bbox["max_y"] - bbox["min_y"], 0.1)
    distance = max(height * 1.6, width * 2.5, depth * 3.0, 6.0)
    if axis == "x":
        camera_location = (bbox["min_x"] - distance, center_y, center_z)
        key_light_location = (bbox["min_x"] - (distance * 0.6), center_y, center_z + height)
    elif axis == "y":
        camera_location = (center_x, bbox["min_y"] - distance, center_z)
        key_light_location = (center_x, bbox["min_y"] - (distance * 0.6), center_z + height)
    else:
        raise ValueError(f"Unsupported camera axis: {axis}")
    target = (center_x, center_y, center_z)
    return {
        "cameraLocation": camera_location,
        "target": target,
        "keyLightLocation": key_light_location,
        "orthographicScale": max(height * 1.8, width * 2.0, 1.0),
        "clipEnd": (distance * 2.0) + max(height, width, depth),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Mac Game Rigger workflow on a real asset."
    )
    parser.add_argument("--asset", required=True, help="Source FBX, GLB/GLTF, OBJ, or BLEND path.")
    parser.add_argument("--evidence-dir", required=True, help="Evidence output directory.")
    parser.add_argument("--summary", required=True, help="Workflow summary JSON path.")
    parser.add_argument("--camera-axis", choices=("x", "y"), default="x", help="Axis used for evidence previews.")
    parser.add_argument(
        "--template",
        choices=("humanoid", "quadruped", "tail_creature", "prop_hinge"),
        default="humanoid",
    )
    parser.add_argument(
        "--prop-hinge-pivot-x",
        type=normalized_factor,
        default=0.16,
        help="Normalized X position of the prop hinge pivot within the asset bbox.",
    )
    parser.add_argument(
        "--prop-hinge-base-x",
        type=normalized_factor,
        default=0.28,
        help="Normalized X position of the fixed prop base/origin within the asset bbox.",
    )
    parser.add_argument(
        "--prop-hinge-axis",
        choices=("x", "y"),
        default="x",
        help="BBox axis used to lay out the prop hinge chain.",
    )
    return parser.parse_args(argv)


def normalized_factor(value: str) -> float:
    parsed = float(value)
    if parsed < 0.0 or parsed > 1.0:
        raise argparse.ArgumentTypeError("must be between 0.0 and 1.0")
    return parsed


def blender_script_args() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def reset_scene(bpy_module) -> None:
    if bpy_module.ops.object.mode_set.poll():
        bpy_module.ops.object.mode_set(mode="OBJECT")
    bpy_module.ops.object.select_all(action="SELECT")
    bpy_module.ops.object.delete()


def import_asset(bpy_module, asset_path: Path) -> None:
    suffix = asset_path.suffix.lower()
    if suffix == ".fbx":
        bpy_module.ops.import_scene.fbx(filepath=str(asset_path))
        return
    if suffix in {".glb", ".gltf"}:
        bpy_module.ops.import_scene.gltf(filepath=str(asset_path))
        return
    if suffix == ".obj":
        bpy_module.ops.wm.obj_import(filepath=str(asset_path))
        return
    if suffix == ".blend":
        bpy_module.ops.wm.open_mainfile(filepath=str(asset_path))
        return
    raise ValueError(f"Unsupported asset format: {asset_path.suffix}")


def remove_non_exportable_import_objects(bpy_module) -> dict[str, Any]:
    removed_names = []
    for obj in list(bpy_module.context.scene.objects):
        if obj.type != "MESH":
            continue
        collection_names = {collection.name for collection in getattr(obj, "users_collection", ())}
        if collection_names.isdisjoint(NON_EXPORT_COLLECTION_NAMES):
            continue
        obj_name = obj.name
        bpy_module.data.objects.remove(obj, do_unlink=True)
        removed_names.append(obj_name)
    return {
        "removedObjects": len(removed_names),
        "removedObjectNames": removed_names,
    }


def mesh_bbox(bpy_module) -> dict[str, float]:
    from mathutils import Vector

    points = []
    for obj in bpy_module.context.scene.objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise ValueError("Imported asset contains no mesh objects")

    return {
        "min_x": min(point.x for point in points),
        "max_x": max(point.x for point in points),
        "min_y": min(point.y for point in points),
        "max_y": max(point.y for point in points),
        "min_z": min(point.z for point in points),
        "max_z": max(point.z for point in points),
    }


def strip_source_rig(bpy_module) -> dict[str, int]:
    removed_armatures = 0
    removed_modifiers = 0
    removed_groups = 0

    for obj in list(bpy_module.context.scene.objects):
        if obj.type == "ARMATURE":
            bpy_module.data.objects.remove(obj, do_unlink=True)
            removed_armatures += 1

    for obj in bpy_module.context.scene.objects:
        if obj.type != "MESH":
            continue
        obj.parent = None
        for modifier in tuple(obj.modifiers):
            if modifier.type == "ARMATURE":
                obj.modifiers.remove(modifier)
                removed_modifiers += 1
        for vertex_group in tuple(obj.vertex_groups):
            obj.vertex_groups.remove(vertex_group)
            removed_groups += 1

    return {
        "removedArmatures": removed_armatures,
        "removedArmatureModifiers": removed_modifiers,
        "removedVertexGroups": removed_groups,
    }


def normalize_mesh_orientation(bpy_module) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    if bpy_module.ops.object.mode_set.poll():
        bpy_module.ops.object.mode_set(mode="OBJECT")

    meshes = [obj for obj in bpy_module.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        return applied

    scene_orientation_plan = orientation_normalization_plan_from_dimensions(
        scene_dimensions_from_bbox(mesh_bbox(bpy_module))
    )

    for obj in meshes:
        apply_scale = any(abs(value - 1.0) > 0.0001 for value in tuple(obj.scale))
        if scene_orientation_plan is None and not apply_scale:
            continue
        plan = {
            "sourceUpAxis": (
                None
                if scene_orientation_plan is None
                else scene_orientation_plan["sourceUpAxis"]
            ),
            "rotationAxis": (
                None
                if scene_orientation_plan is None
                else scene_orientation_plan["rotationAxis"]
            ),
            "rotationRadians": (
                0.0
                if scene_orientation_plan is None
                else scene_orientation_plan["rotationRadians"]
            ),
            "applyScale": apply_scale,
        }
        bpy_module.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy_module.context.view_layer.objects.active = obj
        if plan["rotationAxis"] is not None:
            obj.rotation_euler.rotate_axis(plan["rotationAxis"], plan["rotationRadians"])
        bpy_module.ops.object.transform_apply(
            location=False,
            rotation=plan["rotationAxis"] is not None,
            scale=bool(plan["applyScale"]),
        )
        obj.select_set(False)
        applied.append(
            {
                "objectName": obj.name,
                "sourceUpAxis": plan["sourceUpAxis"],
                "rotationAxis": plan["rotationAxis"],
                "rotationRadians": plan["rotationRadians"],
                "appliedScale": bool(plan["applyScale"]),
            }
        )

    return applied


def add_landmarks(bpy_module, landmarks: dict[str, tuple[float, float, float]]) -> None:
    for name, location in landmarks.items():
        bpy_module.ops.object.empty_add(type="SPHERE", location=location)
        landmark = bpy_module.context.object
        landmark.name = f"MGR_Landmark_{name}"
        landmark.empty_display_size = 0.08


def select_meshes(bpy_module) -> list[Any]:
    meshes = [obj for obj in bpy_module.context.scene.objects if obj.type == "MESH"]
    bpy_module.ops.object.select_all(action="DESELECT")
    for mesh in meshes:
        make_object_selectable(mesh)
        mesh.select_set(True)
    if meshes:
        bpy_module.context.view_layer.objects.active = meshes[0]
    return meshes


def make_object_selectable(obj) -> None:
    if hasattr(obj, "hide_select"):
        obj.hide_select = False
    if hasattr(obj, "hide_viewport"):
        obj.hide_viewport = False
    if hasattr(obj, "hide_set"):
        obj.hide_set(False)


def select_export_objects(bpy_module) -> list[Any]:
    meshes = select_meshes(bpy_module)
    armature = bpy_module.data.objects.get("MGR_Armature")
    export_objects = list(meshes)
    if armature is not None and getattr(armature, "type", None) == "ARMATURE":
        make_object_selectable(armature)
        armature.select_set(True)
        bpy_module.context.view_layer.objects.active = armature
        export_objects.append(armature)
    return export_objects


def apply_preview_material(bpy_module) -> None:
    material = bpy_module.data.materials.get(preview_material_name())
    if material is None:
        material = bpy_module.data.materials.new(preview_material_name())
    material.diffuse_color = (0.78, 0.78, 0.74, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in tuple(nodes):
        nodes.remove(node)
    output = nodes.new(type="ShaderNodeOutputMaterial")
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.78, 0.78, 0.74, 1.0)
    emission.inputs["Strength"].default_value = 1.0
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])

    for obj in bpy_module.context.scene.objects:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        obj.data.materials.append(material)


def remove_existing_preview_camera_and_light(bpy_module) -> None:
    for obj in list(bpy_module.context.scene.objects):
        if obj.name.startswith(("MGR_Workflow_Camera", "MGR_Workflow_Key_Light")):
            bpy_module.data.objects.remove(obj, do_unlink=True)


def setup_camera_and_light(
    bpy_module,
    bbox: dict[str, float],
    *,
    axis: str,
) -> dict[str, tuple[float, float, float] | float]:
    from mathutils import Vector

    plan = camera_plan_from_bbox(bbox, axis=axis)
    height = max(bbox["max_z"] - bbox["min_z"], 0.1)
    target = Vector(plan["target"])
    remove_existing_preview_camera_and_light(bpy_module)

    world = bpy_module.context.scene.world
    if world is not None:
        world.color = (0.08, 0.08, 0.08)

    bpy_module.ops.object.light_add(type="AREA", location=plan["keyLightLocation"])
    light = bpy_module.context.object
    light.name = "MGR_Workflow_Key_Light"
    light.data.energy = 900
    light.data.size = max(height, 2.0)

    bpy_module.ops.object.camera_add(location=plan["cameraLocation"])
    camera = bpy_module.context.object
    camera.name = "MGR_Workflow_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = plan["orthographicScale"]
    camera.data.clip_end = plan["clipEnd"]
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy_module.context.scene.camera = camera
    return plan


def run_operator(label: str, operator_call) -> str:
    result = operator_call()
    if result != {"FINISHED"}:
        raise RuntimeError(f"{label} failed with {result}")
    return "FINISHED"


def render_preview_frame(
    bpy_module,
    preview_path: Path,
    *,
    axis: str,
) -> dict[str, Any]:
    current_bbox = mesh_bbox(bpy_module)
    camera_plan = setup_camera_and_light(bpy_module, current_bbox, axis=axis)
    bpy_module.context.scene.mgr_preview_output_path = str(preview_path)
    run_operator("render_front_preview", bpy_module.ops.mgr.render_front_preview)
    return {
        "bbox": current_bbox,
        "camera": camera_plan,
    }


def run_pose_preview(bpy_module, preview_pose_path: Path, *, axis: str, template: str = "humanoid") -> dict[str, Any]:
    operator_name = pose_preview_operator_name(template)
    run_operator(operator_name, getattr(bpy_module.ops.mgr, operator_name))
    frame = render_preview_frame(bpy_module, preview_pose_path, axis=axis)
    frame["operator"] = operator_name
    return frame


def run_side_pose_preview(bpy_module, preview_pose_path: Path, *, axis: str, template: str = "humanoid") -> dict[str, Any]:
    operator_name = side_pose_preview_operator_name(template)
    run_operator("reset_pose", bpy_module.ops.mgr.reset_pose)
    run_operator(operator_name, getattr(bpy_module.ops.mgr, operator_name))
    frame = render_preview_frame(bpy_module, preview_pose_path, axis=axis)
    frame["operator"] = operator_name
    return frame


def run_static_pose_preview(bpy_module, preview_pose_path: Path, *, axis: str) -> dict[str, Any]:
    frame = render_preview_frame(bpy_module, preview_pose_path, axis=axis)
    frame["operator"] = "none"
    frame["reason"] = "No automated pose operator is available for this template."
    return frame


def main() -> int:
    args = parse_args(blender_script_args())
    asset_path = Path(args.asset).expanduser().resolve()
    evidence_dir = Path(args.evidence_dir).expanduser().resolve()
    summary_path = Path(args.summary).expanduser().resolve()
    if not asset_path.exists():
        print(f"Asset not found: {asset_path}", file=sys.stderr)
        return 2

    import bpy

    sys.path.insert(0, str(ADDON_ROOT))
    import mac_game_rigger
    from mac_game_rigger.core.weight_binding import apply_capsule_weights_to_mesh
    from mac_game_rigger.core.weight_binding import capsule_diagnostics
    from mac_game_rigger.core.weight_cleanup import cleanup_mesh_weights

    evidence_dir.mkdir(parents=True, exist_ok=True)
    qa_path = evidence_dir / "qa-report.json"
    preview_paths = preview_artifact_paths(evidence_dir)
    unity_export_path = evidence_dir / "export-unity.fbx"

    reset_scene(bpy)
    import_asset(bpy, asset_path)
    import_prune_result = remove_non_exportable_import_objects(bpy)
    orientation_result = normalize_mesh_orientation(bpy)
    strip_result = strip_source_rig(bpy)
    imported_bbox = mesh_bbox(bpy)
    apply_preview_material(bpy)
    setup_camera_and_light(bpy, imported_bbox, axis=args.camera_axis)

    mac_game_rigger.register()
    try:
        bpy.context.scene.mgr_current_template = args.template
        add_landmarks(
            bpy,
            landmarks_from_bbox(
                args.template,
                imported_bbox,
                prop_hinge_pivot_x=args.prop_hinge_pivot_x,
                prop_hinge_base_x=args.prop_hinge_base_x,
                prop_hinge_axis=args.prop_hinge_axis,
            ),
        )
        run_operator("generate_armature", bpy.ops.mgr.generate_armature)
        run_operator("fix_bone_rolls", bpy.ops.mgr.fix_bone_rolls)
        armature = bpy.data.objects["MGR_Armature"]
        capsule_data = capsule_diagnostics(armature)
        capsule_summary = capsule_diagnostics_summary(capsule_data)

        meshes = select_meshes(bpy)
        capsule_bind_summary = apply_capsule_weights_to_mesh_collection(
            meshes,
            armature,
            bind_func=apply_capsule_weights_to_mesh,
        )
        bpy.context.scene["mgr_last_capsule_weighted_vertices"] = capsule_bind_summary[
            "weightedVertices"
        ]
        cleanup_summary = cleanup_mesh_collection(
            meshes,
            cleanup_func=cleanup_mesh_weights,
        )
        unity_scale_normalization = apply_unity_export_scale_normalization(bpy, args.template)
        weight_diagnostics = weight_region_summary(meshes)
        bone_weight_summary = bone_weight_diagnostics(meshes)
        capsule_bind_weight_summary = capsule_bind_weight_diagnostics(meshes, capsule_data)
        capsule_assignment_summary = capsule_assignment_diagnostics(meshes, capsule_data)
        prop_diagnostics = prop_diagnostics_summary(weight_diagnostics, template=args.template)
        humanoid_diagnostics = humanoid_diagnostics_summary(weight_diagnostics, template=args.template)

        bpy.context.scene.mgr_qa_report_path = str(qa_path)
        run_operator("write_qa_report", bpy.ops.mgr.write_qa_report)

        neutral_preview = render_preview_frame(
            bpy,
            preview_paths["neutral_front"],
            axis=args.camera_axis,
        )
        neutral_side_preview = render_preview_frame(
            bpy,
            preview_paths["neutral_side"],
            axis=side_preview_axis(args.camera_axis),
        )
        pose_preview = run_pose_preview(
            bpy,
            preview_paths["pose_front"],
            axis=args.camera_axis,
            template=args.template,
        )
        pose_side_preview = run_side_pose_preview(
            bpy,
            preview_paths["pose_side"],
            axis=side_preview_axis(args.camera_axis),
            template=args.template,
        )
        run_operator("reset_pose", bpy.ops.mgr.reset_pose)
        pose_deformation = pose_deformation_summary(
            neutral_preview["bbox"],
            pose_preview["bbox"],
            template=args.template,
        )

        select_export_objects(bpy)
        bpy.context.scene.mgr_unity_export_path = str(unity_export_path)
        run_operator("export_unity_fbx", bpy.ops.mgr.export_unity_fbx)

        qa_payload = json.loads(qa_path.read_text(encoding="utf-8"))
        export_qa_path = unity_export_path.with_suffix(".qa.json")
        summary = {
            "schemaVersion": 1,
            "status": "pass",
            "assetPath": str(asset_path),
            "template": args.template,
            "workflowControls": workflow_controls_summary(
                args.template,
                prop_hinge_pivot_x=args.prop_hinge_pivot_x,
                prop_hinge_base_x=args.prop_hinge_base_x,
                prop_hinge_axis=args.prop_hinge_axis,
            ),
            "importPrune": import_prune_result,
            "stripSourceRig": strip_result,
            "orientationNormalization": orientation_result,
            "meshCount": len(meshes),
            "bbox": imported_bbox,
            "artifacts": {
                "qaReport": str(qa_path),
                **preview_artifact_summary(preview_paths),
                "exportUnityFbx": str(unity_export_path),
                "exportQaReport": str(export_qa_path),
            },
            "posePreview": {
                "operator": pose_preview["operator"],
            },
            "camera": {
                "axis": args.camera_axis,
            },
            "previewFrames": {
                "neutral": neutral_preview,
                "neutralSide": neutral_side_preview,
                "pose": pose_preview,
                "poseSide": pose_side_preview,
            },
            "poseDeformation": pose_deformation,
            "unityScaleNormalization": unity_scale_normalization,
            "capsuleBind": capsule_bind_summary,
            "cleanup": cleanup_summary,
            "weightDiagnostics": weight_diagnostics,
            "boneWeightDiagnostics": bone_weight_summary,
            "capsuleBindWeightDiagnostics": capsule_bind_weight_summary,
            "capsuleAssignmentDiagnostics": capsule_assignment_summary,
            "propDiagnostics": prop_diagnostics,
            "humanoidDiagnostics": humanoid_diagnostics,
            "capsuleDiagnostics": capsule_summary,
            "bindSpaceDiagnostics": bind_space_summary(meshes),
            "qa": qa_payload,
        }
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "pass", "summary": str(summary_path)}, sort_keys=True))
        return 0
    finally:
        mac_game_rigger.unregister()


if __name__ == "__main__":
    raise SystemExit(main())
