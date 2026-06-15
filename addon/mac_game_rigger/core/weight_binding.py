from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping

Vector3 = tuple[float, float, float]
DEFAULT_CAPSULE_RADIUS_SCALE = 0.6
MIN_CAPSULE_RADIUS = 0.05
MAX_VERTEX_INFLUENCES = 4


@dataclass(frozen=True)
class CapsuleBindResult:
    mesh_name: str
    weighted_vertices: int
    vertex_group_count: int


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


def apply_capsule_weights_to_mesh(
    mesh,
    armature,
    radius_scale: float = DEFAULT_CAPSULE_RADIUS_SCALE,
    max_influences: int = MAX_VERTEX_INFLUENCES,
) -> CapsuleBindResult:
    if mesh.type != "MESH":
        raise ValueError("mesh must be a Blender mesh object")
    if armature.type != "ARMATURE":
        raise ValueError("armature must be a Blender armature object")
    if radius_scale <= 0.0:
        raise ValueError("radius_scale must be positive")
    if max_influences <= 0:
        raise ValueError("max_influences must be positive")

    bones = _deform_bone_capsules(armature, radius_scale)
    if not bones:
        return CapsuleBindResult(
            mesh_name=mesh.name,
            weighted_vertices=0,
            vertex_group_count=0,
        )

    _ensure_armature_modifier(mesh, armature)
    vertex_groups = _rebuild_vertex_groups(mesh, tuple(bone["name"] for bone in bones))

    weighted_vertices = 0
    for vertex in mesh.data.vertices:
        point = tuple(mesh.matrix_world @ vertex.co)
        weights = _top_capsule_weights(point, bones, max_influences)
        for bone_name, weight in weights.items():
            vertex_groups[bone_name].add([vertex.index], weight, "REPLACE")
        if weights:
            weighted_vertices += 1

    return CapsuleBindResult(
        mesh_name=mesh.name,
        weighted_vertices=weighted_vertices,
        vertex_group_count=len(vertex_groups),
    )


def _deform_bone_capsules(armature, radius_scale: float) -> list[dict]:
    capsules = []
    for bone in armature.data.bones:
        if not bone.use_deform:
            continue
        head = tuple(armature.matrix_world @ bone.head_local)
        tail = tuple(armature.matrix_world @ bone.tail_local)
        length = distance_point_to_segment(tail, head, head)
        radius = max(MIN_CAPSULE_RADIUS, length * radius_scale)
        capsules.append(
            {
                "name": bone.name,
                "head": head,
                "tail": tail,
                "radius": radius,
            }
        )
    return capsules


def _ensure_armature_modifier(mesh, armature) -> None:
    modifier = next(
        (item for item in mesh.modifiers if item.type == "ARMATURE" and item.object == armature),
        None,
    )
    if modifier is None:
        modifier = mesh.modifiers.new(name=armature.name, type="ARMATURE")
        modifier.object = armature


def _rebuild_vertex_groups(mesh, bone_names: tuple[str, ...]) -> dict[str, object]:
    for vertex_group in tuple(mesh.vertex_groups):
        mesh.vertex_groups.remove(vertex_group)
    return {
        bone_name: mesh.vertex_groups.new(name=bone_name)
        for bone_name in bone_names
    }


def _top_capsule_weights(point: Vector3, bones: list[dict], max_influences: int) -> dict[str, float]:
    raw_weights = {
        bone["name"]: capsule_weight(point, bone["head"], bone["tail"], bone["radius"])
        for bone in bones
    }
    top_positive = dict(
        sorted(raw_weights.items(), key=lambda item: item[1], reverse=True)[:max_influences]
    )
    normalized = normalize_weights(top_positive)
    if normalized:
        return normalized

    nearest_bone = min(
        bones,
        key=lambda bone: distance_point_to_segment(point, bone["head"], bone["tail"]),
    )
    return {nearest_bone["name"]: 1.0}


def selected_meshes(context) -> list:
    return [obj for obj in context.selected_objects if obj.type == "MESH"]


def find_mgr_armature(bpy_module):
    armature = bpy_module.data.objects.get("MGR_Armature")
    if armature is None or armature.type != "ARMATURE":
        return None
    return armature
