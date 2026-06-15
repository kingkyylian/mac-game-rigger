import json
import sys
from pathlib import Path
import traceback

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "addon"))

import mac_game_rigger  # noqa: E402


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.context.scene.pop("mgr_last_bone_roll_count", None)


def add_landmark(name, location):
    bpy.ops.object.empty_add(type="SPHERE", location=location)
    bpy.context.object.name = f"MGR_Landmark_{name}"


def seed_full_humanoid():
    template_path = REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json"
    required = tuple(json.loads(template_path.read_text(encoding="utf-8"))["required_landmarks"])
    for index, name in enumerate(required):
        x = -0.4 if name.endswith(".R") else 0.4 if name.endswith(".L") else 0.0
        add_landmark(name, (x, index * 0.01, 0.5 + index * 0.08))


def set_edit_rolls(armature):
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    armature.data.edit_bones["UpperArm.L"].roll = 1.25
    armature.data.edit_bones["UpperLeg.R"].roll = -0.75
    bpy.ops.object.mode_set(mode="OBJECT")


def rounded_roll(armature, bone_name):
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    roll = round(armature.data.edit_bones[bone_name].roll, 4)
    bpy.ops.object.mode_set(mode="OBJECT")
    return roll


def run_test():
    reset_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    seed_full_humanoid()
    assert bpy.ops.mgr.generate_armature() == {"FINISHED"}
    armature = bpy.data.objects["MGR_Armature"]
    set_edit_rolls(armature)

    result = bpy.ops.mgr.fix_bone_rolls()
    assert result == {"FINISHED"}
    assert bpy.context.scene["mgr_last_bone_roll_count"] >= 2
    assert rounded_roll(armature, "UpperArm.L") == 0.0
    assert rounded_roll(armature, "UpperLeg.R") == 0.0

    second_result = bpy.ops.mgr.fix_bone_rolls()
    assert second_result == {"FINISHED"}
    assert bpy.context.scene["mgr_last_bone_roll_count"] == 0


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_BONE_ROLL_TEST_OK")
