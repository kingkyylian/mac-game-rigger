from __future__ import annotations

import math

import bpy
from mathutils import Vector

from .templates import RigTemplate


LANDMARK_PREFIX = "MGR_Landmark_"
MIN_BONE_LENGTH = 0.05


def collect_landmark_positions(scene) -> dict[str, tuple[float, float, float]]:
    return {
        obj.name.removeprefix(LANDMARK_PREFIX): tuple(obj.location)
        for obj in scene.objects
        if obj.name.startswith(LANDMARK_PREFIX)
    }


def build_armature_from_template(
    template: RigTemplate,
    landmark_positions: dict[str, tuple[float, float, float]],
    name: str = "MGR_Armature",
):
    armature_data = bpy.data.armatures.new(name)
    armature_obj = bpy.data.objects.new(name, armature_data)
    bpy.context.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    armature_obj.select_set(True)

    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = armature_data.edit_bones

    created_bones = {}
    for bone_spec in template.bones:
        bone = edit_bones.new(bone_spec.name)
        bone.head = Vector(_required_position(landmark_positions, bone_spec.head_landmark))
        bone.tail = _safe_tail(
            bone.head,
            Vector(_required_position(landmark_positions, bone_spec.tail_landmark)),
        )
        created_bones[bone_spec.name] = bone

    for bone_spec in template.bones:
        if bone_spec.parent:
            created_bones[bone_spec.name].parent = created_bones[bone_spec.parent]

    bpy.ops.object.mode_set(mode="OBJECT")
    return armature_obj


def _required_position(
    landmark_positions: dict[str, tuple[float, float, float]],
    landmark_name: str,
) -> tuple[float, float, float]:
    try:
        return landmark_positions[landmark_name]
    except KeyError as exc:
        raise KeyError(f"Missing landmark: {landmark_name}") from exc


def _safe_tail(head: Vector, tail: Vector) -> Vector:
    if math.isclose((tail - head).length, 0.0, abs_tol=1e-6):
        return head + Vector((0.0, 0.0, MIN_BONE_LENGTH))
    return tail
