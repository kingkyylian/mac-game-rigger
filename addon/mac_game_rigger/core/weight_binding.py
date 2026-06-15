from __future__ import annotations

import math
from collections.abc import Mapping

Vector3 = tuple[float, float, float]


def _subtract(left: Vector3, right: Vector3) -> Vector3:
    return (
        left[0] - right[0],
        left[1] - right[1],
        left[2] - right[2],
    )


def _dot(left: Vector3, right: Vector3) -> float:
    return (left[0] * right[0]) + (left[1] * right[1]) + (left[2] * right[2])


def _length(vector: Vector3) -> float:
    return math.sqrt(_dot(vector, vector))


def _interpolate(start: Vector3, end: Vector3, factor: float) -> Vector3:
    return (
        start[0] + ((end[0] - start[0]) * factor),
        start[1] + ((end[1] - start[1]) * factor),
        start[2] + ((end[2] - start[2]) * factor),
    )


def distance_point_to_segment(
    point: Vector3,
    segment_start: Vector3,
    segment_end: Vector3,
) -> float:
    segment_vector = _subtract(segment_end, segment_start)
    segment_length_squared = _dot(segment_vector, segment_vector)
    if segment_length_squared == 0.0:
        return _length(_subtract(point, segment_start))

    point_vector = _subtract(point, segment_start)
    projection = _dot(point_vector, segment_vector) / segment_length_squared
    clamped_projection = max(0.0, min(1.0, projection))
    closest_point = _interpolate(segment_start, segment_end, clamped_projection)
    return _length(_subtract(point, closest_point))


def capsule_weight(
    point: Vector3,
    segment_start: Vector3,
    segment_end: Vector3,
    radius: float,
) -> float:
    if radius <= 0.0:
        raise ValueError("radius must be positive")

    distance = distance_point_to_segment(point, segment_start, segment_end)
    return max(0.0, 1.0 - (distance / radius))


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    positive_weights = {
        bone_name: weight for bone_name, weight in weights.items() if weight > 0.0
    }
    total = sum(positive_weights.values())
    if total <= 0.0:
        return {}
    return {
        bone_name: weight / total
        for bone_name, weight in positive_weights.items()
    }


def selected_meshes(context) -> list:
    return [obj for obj in context.selected_objects if obj.type == "MESH"]


def find_mgr_armature(bpy_module):
    armature = bpy_module.data.objects.get("MGR_Armature")
    if armature is None or armature.type != "ARMATURE":
        return None
    return armature
