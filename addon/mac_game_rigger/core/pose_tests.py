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
            "UpperArm.L": (0.0, 0.0, 0.18),
            "UpperArm.R": (0.0, 0.0, -0.18),
            "LowerArm.L": (0.0, 0.0, 0.06),
            "LowerArm.R": (0.0, 0.0, -0.06),
        },
    )


def apply_humanoid_knee_bend(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "UpperLeg.L": (-0.1, 0.0, 0.0),
            "UpperLeg.R": (-0.1, 0.0, 0.0),
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


def apply_humanoid_stress_pose(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "UpperArm.L": (0.0, 0.0, 0.18),
            "UpperArm.R": (0.0, 0.0, -0.18),
            "LowerArm.L": (0.0, 0.0, 0.06),
            "LowerArm.R": (0.0, 0.0, -0.06),
            "UpperLeg.L": (-0.1, 0.0, 0.0),
            "UpperLeg.R": (-0.1, 0.0, 0.0),
            "LowerLeg.L": (0.75, 0.0, 0.0),
            "LowerLeg.R": (0.75, 0.0, 0.0),
            "Neck": (0.0, 0.0, 0.45),
            "Head": (0.0, 0.0, 0.2),
        },
    )


def apply_humanoid_side_review_pose(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "UpperLeg.L": (-0.1, 0.0, 0.0),
            "UpperLeg.R": (-0.1, 0.0, 0.0),
            "LowerLeg.L": (0.75, 0.0, 0.0),
            "LowerLeg.R": (0.75, 0.0, 0.0),
        },
    )


def apply_quadruped_gait_pose(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "FrontUpperLeg.L": (-0.32, 0.0, 0.0),
            "FrontLowerLeg.L": (0.42, 0.0, 0.0),
            "FrontPaw.L": (-0.18, 0.0, 0.0),
            "FrontUpperLeg.R": (0.28, 0.0, 0.0),
            "FrontLowerLeg.R": (-0.36, 0.0, 0.0),
            "FrontPaw.R": (0.14, 0.0, 0.0),
            "RearUpperLeg.L": (0.32, 0.0, 0.0),
            "RearLowerLeg.L": (-0.4, 0.0, 0.0),
            "RearPaw.L": (0.16, 0.0, 0.0),
            "RearUpperLeg.R": (-0.28, 0.0, 0.0),
            "RearLowerLeg.R": (0.36, 0.0, 0.0),
            "RearPaw.R": (-0.14, 0.0, 0.0),
            "Tail.001": (0.0, 0.0, 0.18),
            "Tail.002": (0.0, 0.0, -0.12),
            "Neck": (0.0, 0.0, -0.08),
            "Head": (0.0, 0.0, 0.06),
        },
    )


def apply_quadruped_side_review_pose(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "FrontUpperLeg.L": (-0.24, 0.0, 0.0),
            "FrontLowerLeg.L": (0.34, 0.0, 0.0),
            "FrontPaw.L": (-0.12, 0.0, 0.0),
            "FrontUpperLeg.R": (0.2, 0.0, 0.0),
            "FrontLowerLeg.R": (-0.3, 0.0, 0.0),
            "FrontPaw.R": (0.1, 0.0, 0.0),
            "RearUpperLeg.L": (0.24, 0.0, 0.0),
            "RearLowerLeg.L": (-0.34, 0.0, 0.0),
            "RearPaw.L": (0.12, 0.0, 0.0),
            "RearUpperLeg.R": (-0.2, 0.0, 0.0),
            "RearLowerLeg.R": (0.3, 0.0, 0.0),
            "RearPaw.R": (-0.1, 0.0, 0.0),
        },
    )


def apply_tail_creature_reach_pose(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "FrontUpperLeg.L": (-0.06, 0.0, 0.0),
            "FrontUpperLeg.R": (0.06, 0.0, 0.0),
            "RearUpperLeg.L": (0.06, 0.0, 0.0),
            "RearUpperLeg.R": (-0.06, 0.0, 0.0),
            "Neck.001": (-0.16, 0.0, 0.0),
            "Neck.002": (0.12, 0.0, 0.0),
            "Head": (0.04, 0.0, 0.0),
            "Tail.001": (0.0, 0.0, 0.12),
            "Tail.002": (0.0, 0.0, -0.08),
            "Tail.003": (0.0, 0.0, -0.06),
        },
    )


def apply_tail_creature_side_review_pose(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "Neck.001": (-0.08, 0.0, 0.0),
            "Neck.002": (0.05, 0.0, 0.0),
            "Head": (0.02, 0.0, 0.0),
            "Tail.001": (0.0, 0.0, 0.08),
            "Tail.002": (0.0, 0.0, -0.04),
            "Tail.003": (0.0, 0.0, -0.03),
        },
    )


def apply_prop_hinge_open_pose(
    armature,
    *,
    open_angle: float = 0.65,
    moving_part_angle: float = 0.18,
    swing_direction: str = "positive",
    rotation_axis: str = "z",
) -> PoseTestResult:
    direction_sign = -1.0 if swing_direction == "negative" else 1.0
    axis_index = {"x": 0, "y": 1, "z": 2}.get(rotation_axis, 2)
    hinge_rotation = [0.0, 0.0, 0.0]
    moving_part_rotation = [0.0, 0.0, 0.0]
    hinge_rotation[axis_index] = round(abs(open_angle) * direction_sign, 4)
    moving_part_rotation[axis_index] = round(abs(moving_part_angle) * direction_sign, 4)
    return _apply_pose_rotations(
        armature,
        {
            "Hinge": tuple(hinge_rotation),
            "MovingPart": tuple(moving_part_rotation),
        },
    )


def apply_prop_hinge_side_review_pose(armature) -> PoseTestResult:
    return _apply_pose_rotations(
        armature,
        {
            "Hinge": (0.0, 0.0, 0.35),
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
