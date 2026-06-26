from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping

Vector3 = tuple[float, float, float]
DEFAULT_CAPSULE_RADIUS_SCALE = 0.6
MIN_CAPSULE_RADIUS = 0.05
MAX_VERTEX_INFLUENCES = 4
LIMB_CAPSULE_RADIUS_SCALE = 0.38
DISTAL_CAPSULE_RADIUS_SCALE = 0.28
CORE_CAPSULE_RADIUS_SCALE = 1.5
CORE_CAPSULE_WEIGHT_BIAS = 2.0
CORE_BONE_NAMES = frozenset({"Hips", "Spine", "Chest"})
MIN_BONE_COVERAGE_VERTICES = 8
MIN_LIMB_COVERAGE_VERTICES = 4
MIN_DISTAL_COVERAGE_VERTICES = 2
MIN_COVERAGE_WEIGHT = 0.15
MIN_DISTAL_COVERAGE_RATIO = 0.0125
DISTAL_COVERAGE_WEIGHT = 2.0


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


def bone_radius_scale(bone_name: str, default_scale: float) -> float:
    if any(token in bone_name for token in ("Hand", "Foot")):
        return min(default_scale, DISTAL_CAPSULE_RADIUS_SCALE)
    if any(token in bone_name for token in ("Arm", "Leg")):
        return min(default_scale, LIMB_CAPSULE_RADIUS_SCALE)
    if bone_name in CORE_BONE_NAMES:
        return max(default_scale, CORE_CAPSULE_RADIUS_SCALE)
    return default_scale


def bone_weight_bias(bone_name: str) -> float:
    if bone_name in CORE_BONE_NAMES:
        return CORE_CAPSULE_WEIGHT_BIAS
    return 1.0


def minimum_coverage_vertices_for_bone(bone_name: str, default_count: int) -> int:
    if any(token in bone_name for token in ("Hand", "Foot")):
        return min(default_count, MIN_DISTAL_COVERAGE_VERTICES)
    if any(token in bone_name for token in ("Arm", "Leg")):
        return min(default_count, MIN_LIMB_COVERAGE_VERTICES)
    return default_count


def effective_minimum_coverage_vertices_for_bone(
    bone_name: str,
    default_count: int,
    vertex_count: int,
) -> int:
    base_count = minimum_coverage_vertices_for_bone(bone_name, default_count)
    if any(token in bone_name for token in ("Hand", "Foot")):
        scaled_count = math.ceil(max(0, vertex_count) * MIN_DISTAL_COVERAGE_RATIO)
        return max(base_count, scaled_count)
    return base_count


def coverage_weight_for_bone(bone_name: str) -> float:
    if any(token in bone_name for token in ("Hand", "Foot")):
        return DISTAL_COVERAGE_WEIGHT
    return MIN_COVERAGE_WEIGHT


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

    vertex_points = mesh_bind_vertex_points(mesh, target_bounds=_capsule_bounds(bones))
    vertex_weights: dict[int, dict[str, float]] = {}
    for vertex in mesh.data.vertices:
        point = vertex_points[vertex.index]
        vertex_weights[vertex.index] = _top_capsule_weights(point, bones, max_influences)

    vertex_weights = ensure_minimum_bone_coverage(
        vertex_weights=vertex_weights,
        vertex_points=vertex_points,
        bones=bones,
        min_vertices_per_bone=MIN_BONE_COVERAGE_VERTICES,
        max_influences=max_influences,
    )

    weighted_vertices = 0
    for vertex_index, weights in vertex_weights.items():
        for bone_name, weight in weights.items():
            vertex_groups[bone_name].add([vertex_index], weight, "REPLACE")
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
        radius = max(MIN_CAPSULE_RADIUS, length * bone_radius_scale(bone.name, radius_scale))
        capsules.append(
            {
                "name": bone.name,
                "head": head,
                "tail": tail,
                "radius": radius,
            }
        )
    return capsules


def mesh_bind_vertex_points(
    mesh,
    target_bounds: dict[str, Vector3] | None = None,
) -> dict[int, Vector3]:
    raw_points = {
        vertex.index: _point_tuple(vertex.co)
        for vertex in mesh.data.vertices
    }
    if not raw_points:
        return {}

    if target_bounds is None:
        target_corners = [
            _point_tuple(_matrix_point(mesh.matrix_world, corner))
            for corner in getattr(mesh, "bound_box", ())
        ]
        if not target_corners:
            return {
                vertex_index: _point_tuple(_matrix_point(mesh.matrix_world, point))
                for vertex_index, point in raw_points.items()
            }
        target_bounds = _bounds(target_corners)

    if target_bounds is None:
        return {
            vertex_index: _point_tuple(_matrix_point(mesh.matrix_world, point))
            for vertex_index, point in raw_points.items()
        }

    raw_bounds = _bounds(raw_points.values())
    return {
        vertex_index: _map_point_between_bounds(point, raw_bounds, target_bounds)
        for vertex_index, point in raw_points.items()
    }


def _capsule_bounds(capsules: list[dict]) -> dict[str, Vector3]:
    points = []
    for capsule in capsules:
        radius = float(capsule["radius"])
        for endpoint in (capsule["head"], capsule["tail"]):
            points.append((endpoint[0] - radius, endpoint[1] - radius, endpoint[2] - radius))
            points.append((endpoint[0] + radius, endpoint[1] + radius, endpoint[2] + radius))
    return _bounds(points)


def _point_tuple(point) -> Vector3:
    if hasattr(point, "x") and hasattr(point, "y") and hasattr(point, "z"):
        return (float(point.x), float(point.y), float(point.z))
    return (float(point[0]), float(point[1]), float(point[2]))


def _matrix_point(matrix, point):
    try:
        return matrix @ point
    except TypeError:
        from mathutils import Vector

        return matrix @ Vector(point)


def _bounds(points) -> dict[str, Vector3]:
    points = tuple(points)
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


def _map_point_between_bounds(
    point: Vector3,
    source_bounds: dict[str, Vector3],
    target_bounds: dict[str, Vector3],
) -> Vector3:
    mapped = []
    for axis in range(3):
        source_min = source_bounds["min"][axis]
        source_max = source_bounds["max"][axis]
        target_min = target_bounds["min"][axis]
        target_max = target_bounds["max"][axis]
        source_span = source_max - source_min
        if abs(source_span) <= 0.0001:
            mapped.append(target_min)
            continue
        factor = (point[axis] - source_min) / source_span
        mapped.append(target_min + ((target_max - target_min) * factor))
    return (mapped[0], mapped[1], mapped[2])


def capsule_diagnostics(
    armature,
    radius_scale: float = DEFAULT_CAPSULE_RADIUS_SCALE,
) -> list[dict[str, object]]:
    return [
        {
            "name": capsule["name"],
            "head": capsule["head"],
            "tail": capsule["tail"],
            "radius": capsule["radius"],
            "verticalMin": min(capsule["head"][2], capsule["tail"][2]),
            "verticalMax": max(capsule["head"][2], capsule["tail"][2]),
        }
        for capsule in _deform_bone_capsules(armature, radius_scale)
    ]


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
    return capsule_assignment_details(point, bones, max_influences)["weights"]


def capsule_assignment_details(point: Vector3, bones: list[dict], max_influences: int) -> dict[str, object]:
    candidate_bones = _candidate_bones_for_point(point, bones)
    raw_weights = {
        bone["name"]: (
            capsule_weight(point, bone["head"], bone["tail"], bone["radius"])
            * bone_weight_bias(bone["name"])
        )
        for bone in candidate_bones
    }
    top_positive = _select_weight_candidates(raw_weights, max_influences)
    normalized = normalize_weights(top_positive)
    if normalized:
        strongest_bone = max(normalized.items(), key=lambda item: item[1])[0]
        return {
            "mode": "capsule",
            "weights": normalized,
            "nearestBone": strongest_bone,
            "nearestBoneRegion": bone_assignment_region(strongest_bone),
            "nearestDistance": 0.0,
            "nearestRadius": None,
            "nearestDistanceRatio": 0.0,
        }

    nearest_bone = min(
        candidate_bones,
        key=lambda bone: fallback_distance_ratio(point, bone),
    )
    nearest_distance = distance_point_to_segment(point, nearest_bone["head"], nearest_bone["tail"])
    nearest_radius = float(nearest_bone["radius"])
    return {
        "mode": "nearestFallback",
        "weights": {nearest_bone["name"]: 1.0},
        "nearestBone": nearest_bone["name"],
        "nearestBoneRegion": bone_assignment_region(nearest_bone["name"]),
        "nearestDistance": nearest_distance,
        "nearestRadius": nearest_radius,
        "nearestDistanceRatio": nearest_distance / nearest_radius if nearest_radius > 0.0 else None,
    }


def fallback_distance_ratio(point: Vector3, bone: Mapping[str, object]) -> float:
    radius = float(bone["radius"])
    distance = distance_point_to_segment(point, bone["head"], bone["tail"])
    if radius <= 0.0:
        return math.inf
    return distance / radius


def bone_assignment_region(bone_name: str) -> str:
    if any(token in bone_name for token in ("Hand", "Foot")):
        return "distal"
    if any(token in bone_name for token in ("Arm", "Leg")):
        return "limb"
    if bone_name in CORE_BONE_NAMES:
        return "core"
    if bone_name in {"Neck", "Head"}:
        return "neckHead"
    return "other"


def _candidate_bones_for_point(point: Vector3, bones: list[dict]) -> list[dict]:
    neck_head_bones = [
        bone
        for bone in bones
        if bone["name"] in {"Neck", "Head"}
    ]
    if not neck_head_bones:
        return bones

    neck_start_z = min(
        min(bone["head"][2], bone["tail"][2])
        for bone in neck_head_bones
    )
    if point[2] >= neck_start_z:
        return bones

    torso_and_limb_bones = [
        bone
        for bone in bones
        if bone["name"] not in {"Neck", "Head"}
    ]
    return torso_and_limb_bones or bones


def ensure_minimum_bone_coverage(
    *,
    vertex_weights: Mapping[int, Mapping[str, float]],
    vertex_points: Mapping[int, Vector3],
    bones: list[dict],
    min_vertices_per_bone: int,
    max_influences: int,
) -> dict[int, dict[str, float]]:
    covered_weights = {
        vertex_index: dict(weights)
        for vertex_index, weights in vertex_weights.items()
    }
    if min_vertices_per_bone <= 0 or max_influences <= 0:
        return covered_weights

    fallback_bones_by_vertex: dict[int, set[str]] = {
        vertex_index: set()
        for vertex_index in covered_weights
    }
    for bone in bones:
        bone_name = bone["name"]
        required_count = effective_minimum_coverage_vertices_for_bone(
            bone_name,
            min_vertices_per_bone,
            len(vertex_points),
        )
        current_count = _bone_influence_count(covered_weights, bone_name)
        if current_count >= required_count:
            continue

        nearest_vertices = sorted(
            vertex_points,
            key=lambda vertex_index: (
                len(fallback_bones_by_vertex.setdefault(vertex_index, set())),
                distance_point_to_segment(
                    vertex_points[vertex_index],
                    bone["head"],
                    bone["tail"],
                ),
            ),
        )
        for vertex_index in nearest_vertices:
            if current_count >= required_count:
                break
            weights = covered_weights.setdefault(vertex_index, {})
            if weights.get(bone_name, 0.0) > 0.0:
                continue
            weights[bone_name] = max(
                coverage_weight_for_bone(bone_name),
                weights.get(bone_name, 0.0),
            )
            protected_bones = fallback_bones_by_vertex.setdefault(vertex_index, set())
            protected_bones.add(bone_name)
            covered_weights[vertex_index] = _limit_and_normalize_weights(
                weights,
                required_bone_name=bone_name,
                protected_bone_names=protected_bones,
                max_influences=max_influences,
            )
            current_count += 1

    return covered_weights


def _bone_influence_count(
    vertex_weights: Mapping[int, Mapping[str, float]],
    bone_name: str,
) -> int:
    return sum(
        1
        for weights in vertex_weights.values()
        if weights.get(bone_name, 0.0) > 0.0
    )


def _limit_and_normalize_weights(
    weights: Mapping[str, float],
    *,
    required_bone_name: str,
    protected_bone_names: set[str],
    max_influences: int,
) -> dict[str, float]:
    positive = {
        bone_name: weight
        for bone_name, weight in weights.items()
        if weight > 0.0
    }
    if required_bone_name not in positive:
        positive[required_bone_name] = MIN_COVERAGE_WEIGHT
    if len(positive) > max_influences:
        required_names = [required_bone_name]
        required_names.extend(
            bone_name
            for bone_name in sorted(protected_bone_names)
            if bone_name != required_bone_name and bone_name in positive
        )
        selected = [
            (bone_name, positive[bone_name])
            for bone_name in required_names[:max_influences]
        ]
        selected_names = {bone_name for bone_name, _weight in selected}
        selected.extend(
            (bone_name, weight)
            for bone_name, weight in sorted(
                positive.items(),
                key=lambda item: item[1],
                reverse=True,
            )
            if bone_name not in selected_names
        )
        positive = dict(selected[:max_influences])
    return normalize_weights(positive)


def _select_weight_candidates(
    raw_weights: Mapping[str, float],
    max_influences: int,
) -> dict[str, float]:
    sorted_positive = [
        item
        for item in sorted(raw_weights.items(), key=lambda item: item[1], reverse=True)
        if item[1] > 0.0
    ]
    if not sorted_positive:
        return {}

    core_positive = [
        item for item in sorted_positive if item[0] in CORE_BONE_NAMES
    ]
    if not core_positive:
        return dict(sorted_positive[:max_influences])

    strongest_core = core_positive[0][1]
    strongest_non_core = next(
        (weight for bone_name, weight in sorted_positive if bone_name not in CORE_BONE_NAMES),
        0.0,
    )
    if strongest_core < strongest_non_core:
        return dict(sorted_positive[:max_influences])

    reserved_core_count = min(3, max_influences, len(core_positive))
    selected = list(core_positive[:reserved_core_count])
    selected_names = {bone_name for bone_name, _weight in selected}
    for bone_name, weight in sorted_positive:
        if len(selected) >= max_influences:
            break
        if bone_name in selected_names:
            continue
        selected.append((bone_name, weight))
        selected_names.add(bone_name)
    return dict(selected)


def selected_meshes(context) -> list:
    return [obj for obj in context.selected_objects if obj.type == "MESH"]


def find_mgr_armature(bpy_module):
    armature = bpy_module.data.objects.get("MGR_Armature")
    if armature is None or armature.type != "ARMATURE":
        return None
    return armature
