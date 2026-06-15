import json
import sys
from pathlib import Path
import traceback

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "addon"))

import mac_game_rigger  # noqa: E402


def reset_scene():
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def add_landmark(name, location):
    bpy.ops.object.empty_add(type="SPHERE", location=location)
    bpy.context.object.name = f"MGR_Landmark_{name}"


def seed_full_humanoid():
    template_path = REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json"
    required = tuple(json.loads(template_path.read_text(encoding="utf-8"))["required_landmarks"])
    for index, name in enumerate(required):
        x = -0.4 if name.endswith(".R") else 0.4 if name.endswith(".L") else 0.0
        add_landmark(name, (x, index * 0.01, 0.5 + index * 0.08))


def pose_bone_rotation(armature, bone_name):
    return tuple(round(value, 4) for value in armature.pose.bones[bone_name].rotation_euler)


def assert_all_pose_rotations_reset(armature):
    for pose_bone in armature.pose.bones:
        assert pose_bone_rotation(armature, pose_bone.name) == (0.0, 0.0, 0.0)


def create_minimal_armature():
    bpy.ops.object.armature_add(location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = "MGR_Armature"
    armature.data.name = "MGR_Armature_Data"
    armature.pose.bones[0].name = "OnlyBone"
    return armature


def run_test():
    reset_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    seed_full_humanoid()
    assert bpy.ops.mgr.generate_armature() == {"FINISHED"}
    armature = bpy.data.objects["MGR_Armature"]

    assert bpy.ops.mgr.pose_arm_raise() == {"FINISHED"}
    assert pose_bone_rotation(armature, "UpperArm.L") != (0.0, 0.0, 0.0)
    assert pose_bone_rotation(armature, "UpperArm.R") != (0.0, 0.0, 0.0)

    assert bpy.ops.mgr.pose_knee_bend() == {"FINISHED"}
    assert pose_bone_rotation(armature, "LowerLeg.L") != (0.0, 0.0, 0.0)
    assert pose_bone_rotation(armature, "LowerLeg.R") != (0.0, 0.0, 0.0)

    assert bpy.ops.mgr.pose_neck_turn() == {"FINISHED"}
    assert pose_bone_rotation(armature, "Neck") != (0.0, 0.0, 0.0)

    assert bpy.ops.mgr.reset_pose() == {"FINISHED"}
    assert_all_pose_rotations_reset(armature)

    reset_scene()
    create_minimal_armature()
    assert bpy.ops.mgr.pose_arm_raise() == {"FINISHED"}
    assert "Missing pose bones:" in bpy.context.scene.mgr_pose_test_message


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_POSE_TESTS_OPERATOR_TEST_OK")
