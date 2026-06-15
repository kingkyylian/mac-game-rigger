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
    for key in ("mgr_landmark_validation_message",):
        bpy.context.scene.pop(key, None)


def add_landmark(name, location):
    bpy.ops.object.empty_add(type="SPHERE", location=location)
    bpy.context.object.name = f"MGR_Landmark_{name}"


def humanoid_required_landmarks():
    template_path = REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json"
    return tuple(json.loads(template_path.read_text(encoding="utf-8"))["required_landmarks"])


def seed_full_humanoid():
    for index, name in enumerate(humanoid_required_landmarks()):
        x = -0.4 if name.endswith(".R") else 0.4 if name.endswith(".L") else 0.0
        add_landmark(name, (x, index * 0.01, 0.5 + index * 0.08))


def run_test():
    reset_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    add_landmark("hips", (0.0, 0.0, 0.5))

    missing_result = bpy.ops.mgr.generate_armature()
    assert missing_result == {"CANCELLED"}
    assert "MGR_Armature" not in bpy.data.objects
    assert "Missing landmarks:" in bpy.context.scene["mgr_landmark_validation_message"]

    reset_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    seed_full_humanoid()

    full_result = bpy.ops.mgr.generate_armature()
    assert full_result == {"FINISHED"}
    assert "MGR_Armature" in bpy.data.objects
    assert bpy.data.objects["MGR_Armature"].type == "ARMATURE"


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_GENERATE_ARMATURE_OPERATOR_TEST_OK")
