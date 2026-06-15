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


def add_landmark(name):
    bpy.ops.object.empty_add(type="SPHERE", location=(0.0, 0.0, 0.0))
    bpy.context.object.name = f"MGR_Landmark_{name}"


def humanoid_required_landmarks():
    template_path = REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json"
    return tuple(json.loads(template_path.read_text(encoding="utf-8"))["required_landmarks"])


def run_test():
    reset_scene()

    bpy.context.scene.mgr_current_template = "humanoid"
    add_landmark("hips")

    missing_result = bpy.ops.mgr.validate_landmarks()
    assert missing_result == {"FINISHED"}
    missing_message = bpy.context.scene["mgr_landmark_validation_message"]
    assert "Missing landmarks:" in missing_message
    assert "spine" in missing_message
    assert "head" in missing_message

    reset_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    for name in humanoid_required_landmarks():
        add_landmark(name)

    success_result = bpy.ops.mgr.validate_landmarks()
    assert success_result == {"FINISHED"}
    assert bpy.context.scene["mgr_landmark_validation_message"] == "All humanoid landmarks present"


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_LANDMARK_VALIDATION_TEST_OK")
