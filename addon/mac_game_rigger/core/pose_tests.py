from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PoseTestResult:
    changed_bones: int
    missing_bones: tuple[str, ...]


def reset_pose(armature) -> PoseTestResult:
    changed_bones = 0
    for pose_bone in armature.pose.bones:
        _ensure_euler_rotation(pose_bone)
        if any(round(value, 6) != 0.0 for value in pose_bone.rotation_euler):
            changed_bones += 1
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
    return PoseTestResult(changed_bones=changed_bones, missing_bones=())


def apply_humanoid_arm_raise(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "UpperArm.L": (0.0, 0.0, 1.1),
            "UpperArm.R": (0.0, 0.0, -1.1),
            "LowerArm.L": (0.0, 0.0, 0.35),
            "LowerArm.R": (0.0, 0.0, -0.35),
        },
    )


def apply_humanoid_knee_bend(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "UpperLeg.L": (-0.25, 0.0, 0.0),
            "UpperLeg.R": (-0.25, 0.0, 0.0),
            "LowerLeg.L": (0.75, 0.0, 0.0),
            "LowerLeg.R": (0.75, 0.0, 0.0),
        },
    )


def apply_neck_turn(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "Neck": (0.0, 0.0, 0.45),
            "Head": (0.0, 0.0, 0.2),
        },
    )


def _apply_pose_rotations(armature, rotations: dict[str, tuple[float, float, float]]) -> PoseTestResult:
    changed_bones = 0
    missing_bones = []
    for bone_name, rotation in rotations.items():
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            missing_bones.append(bone_name)
            continue
        _ensure_euler_rotation(pose_bone)
        pose_bone.rotation_euler = rotation
        changed_bones += 1
    return PoseTestResult(
        changed_bones=changed_bones,
        missing_bones=tuple(missing_bones),
    )


def _ensure_euler_rotation(pose_bone) -> None:
    pose_bone.rotation_mode = "XYZ"
